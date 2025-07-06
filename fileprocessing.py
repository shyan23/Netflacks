import os
import hashlib
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import subprocess
import tempfile
import psutil
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import ffmpeg
from fractions import Fraction
import logging
import shutil

# Configure logging for clear, informative output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Data Classes for structured information ---

@dataclass
class ChunkInfo:
    """Stores metadata for a single video chunk."""
    index: int
    size: int
    hash: str
    offset: int

@dataclass
class NetflacksMetadata:
    """
    Stores all metadata for a video, intended to be saved as a .netflacks file.
    This is the equivalent of a .torrent file for the NetFlacks system.
    """
    filename: str
    original_size: int
    chunk_size: int
    total_chunks: int
    chunks: List[Dict]  # List of ChunkInfo dictionaries
    created_at: float
    mime_type: str
    # Video-specific metadata
    duration: Optional[float] = None
    resolution: Optional[Tuple[int, int]] = None
    fps: Optional[float] = None

@dataclass
class BenchmarkResult:
    """Stores the result of a single encoding benchmark test."""
    method: str
    duration: float
    speed_factor: float
    success: bool
    error: Optional[str] = None


class LightweightVideoProcessor:
    """
    An intelligent video processor that first transcodes a video for optimal streaming
    by benchmarking hardware (CPU vs GPU), and then chunks the result into verifiable
    pieces for a P2P distribution network, creating a .netflacks metadata file.
    """
    def __init__(self, cache_dir: str = "./video_cache", max_threads: int = None,
                 max_cpu_threads: int = None, benchmark_cache_file: str = "benchmark_cache.json"):
        
        self.cache_dir = Path(cache_dir)
        self.chunks_dir = self.cache_dir / "chunks"
        self.cache_dir.mkdir(exist_ok=True)
        self.chunks_dir.mkdir(exist_ok=True)
        
        self.benchmark_cache_file = self.cache_dir / benchmark_cache_file
        self.default_chunk_size = 512 * 1024  # 512KB
        
        cpu_count = psutil.cpu_count(logical=True)
        self.max_threads = max_threads or max(2, cpu_count // 2)
        self.max_cpu_threads = max_cpu_threads or max(2, cpu_count // 2)
        self.cpu_boost_threads = cpu_count
        
        self.temp_dir = tempfile.mkdtemp(prefix="netflacks_")
        
        self.benchmark_results = self._load_benchmark_cache()
        self.vaapi_device = '/dev/dri/renderD128'
        self.gpu_info = self.detect_gpu()
        
        self.preferred_method = None
        self.optimal_cpu_threads = 0
        
        logger.info(f"Video processor initialized. CPU threads: default={self.max_cpu_threads}, boost={self.cpu_boost_threads}. GPU: {self.gpu_info['type']}")
        logger.info(f"Cache directory: {self.cache_dir}")
        logger.info(f"Chunks directory: {self.chunks_dir}")

    # --- Benchmarking and Transcoding Methods (from your original script) ---

    def _load_benchmark_cache(self):
        if self.benchmark_cache_file.exists():
            try:
                with open(self.benchmark_cache_file, 'r') as f:
                    logger.info(f"Loading benchmark cache from {self.benchmark_cache_file}")
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load benchmark cache: {e}")
        return {}

    def _save_benchmark_cache(self):
        try:
            logger.info(f"Saving benchmark results to {self.benchmark_cache_file}")
            with open(self.benchmark_cache_file, 'w') as f:
                json.dump(self.benchmark_results, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save benchmark cache: {e}")
            
    def detect_gpu(self):
        gpu_info = {'type': 'none', 'description': None, 'capable': False}
        if shutil.which('nvidia-smi'):
            try:
                result = subprocess.run(['nvidia-smi', '-L'], capture_output=True, text=True, check=True)
                gpu_info = {'type': 'nvidia', 'description': result.stdout.strip(), 'capable': True}
                logger.info("NVIDIA GPU detected.")
                return gpu_info
            except Exception: pass
        if os.path.exists(self.vaapi_device):
            gpu_info = {'type': 'amd_or_intel', 'description': f"VA-API device found at {self.vaapi_device}", 'capable': True}
            logger.info("VA-API capable GPU (AMD/Intel) detected.")
            return gpu_info
        logger.info("No capable GPU detected, will use CPU encoding.")
        return gpu_info

    def create_benchmark_clip(self, video_path: str, duration: int) -> str:
        logger.info(f"Creating a {duration}s benchmark clip from the source video...")
        clip_path = os.path.join(self.temp_dir, "benchmark_clip.mp4")
        try:
            info = self.get_video_info(video_path)
            video_duration = info.get('duration', 0)
            start_time = 30 if video_duration > duration + 30 else 0
            
            (ffmpeg.input(video_path, ss=start_time)
             .output(clip_path, t=duration, c='copy')
             .overwrite_output().run(capture_stdout=True, capture_stderr=True))
             
            logger.info(f"Benchmark clip created successfully at {clip_path}")
            return clip_path
        except ffmpeg.Error as e:
            logger.error(f"Failed to create benchmark clip, falling back to CPU. FFmpeg stderr:\n{e.stderr.decode()}")
            self.gpu_info['capable'] = False
            return ""

    def _has_audio_stream(self, filepath: str) -> bool:
        try:
            probe = ffmpeg.probe(filepath)
            return any(stream['codec_type'] == 'audio' for stream in probe['streams'])
        except ffmpeg.Error:
            return False

    def _encode_with_vaapi(self, input_path, output_path, options):
        logger.info(f"Attempting GPU encoding with VA-API on device {self.vaapi_device}")
        try:
            input_video_stream = ffmpeg.input(input_path, hwaccel='vaapi', hwaccel_device=self.vaapi_device, hwaccel_output_format='vaapi').video
            output_streams = [input_video_stream]
            output_opts = {'c:v': 'h264_vaapi', 'qp': options.get('qp', 24)}
            
            if self._has_audio_stream(input_path):
                input_audio_stream = ffmpeg.input(input_path).audio
                output_streams.append(input_audio_stream)
                output_opts['c:a'] = 'copy'

            (ffmpeg.output(*output_streams, output_path, **output_opts)
             .overwrite_output().run(capture_stdout=True, capture_stderr=True))
            return output_path
        except ffmpeg.Error as e:
            logger.error(f"VA-API encoding failed. FFmpeg stderr:\n{e.stderr.decode('utf-8')}")
            raise

    def _encode_with_cpu(self, input_path, output_path, options):
        thread_count = options.get('threads', 0)
        logger.info(f"Attempting CPU encoding with {'auto' if thread_count == 0 else thread_count} threads.")
        try:
            input_stream = ffmpeg.input(input_path)
            output_streams = [input_stream.video]
            output_opts = {
                'c:v': 'libx264', 'preset': options.get('preset', 'fast'),
                'crf': options.get('crf', 23), 'movflags': '+faststart',
            }
            if thread_count > 0: output_opts['threads'] = thread_count
            
            if self._has_audio_stream(input_path):
                output_streams.append(input_stream.audio)
                output_opts['c:a'] = 'copy'

            (ffmpeg.output(*output_streams, output_path, **output_opts)
             .overwrite_output().run(capture_stdout=True, capture_stderr=True))
            return output_path
        except ffmpeg.Error as e:
            logger.error(f"CPU encoding failed. FFmpeg stderr:\n{e.stderr.decode()}")
            raise
    
    def benchmark_encoding_methods(self, video_path: str, duration: int):
        logger.info("--- Starting Encoding Performance Benchmark ---")
        cache_key = f"{self.gpu_info['type']}_v3_{duration}s"
        if cache_key in self.benchmark_results:
            logger.info(f"Using cached benchmark results for key '{cache_key}'.")
            cached = self.benchmark_results[cache_key]
            return {k: BenchmarkResult(**v) for k, v in cached.items()}
            
        test_clip_path = self.create_benchmark_clip(video_path, duration)
        if not test_clip_path:
            logger.warning("Aborting benchmark due to clip creation failure.")
            return {}
            
        results = {}
        cpu_test_threads = sorted(list(set([0, self.max_cpu_threads, self.cpu_boost_threads])))
        
        # Run CPU benchmarks
        for thread_count in cpu_test_threads:
            method_name = f"cpu_{'auto' if thread_count == 0 else thread_count}_threads"
            output_path = os.path.join(self.temp_dir, f"test_{method_name}.mp4")
            try:
                start_time = time.time()
                self._encode_with_cpu(test_clip_path, output_path, {'threads': thread_count})
                enc_time = time.time() - start_time
                speed_factor = duration / enc_time if enc_time > 0 else 0
                results[method_name] = BenchmarkResult(method=method_name, duration=enc_time, speed_factor=speed_factor, success=True)
                logger.info(f"Benchmark | {method_name:<20}: {enc_time:.2f}s ({speed_factor:.2f}x real-time)")
            except Exception as e:
                results[method_name] = BenchmarkResult(method=method_name, duration=float('inf'), speed_factor=0, success=False, error=str(e))
                logger.error(f"Benchmark FAILED | {method_name}: {e}")
                
        # Run GPU benchmark if capable
        if self.gpu_info['capable']:
            gpu_method_name = f"gpu_{self.gpu_info['type']}"
            output_path = os.path.join(self.temp_dir, f"test_gpu.mp4")
            try:
                start_time = time.time()
                self._encode_with_vaapi(test_clip_path, output_path, {})
                enc_time = time.time() - start_time
                speed_factor = duration / enc_time if enc_time > 0 else 0
                results[gpu_method_name] = BenchmarkResult(method=gpu_method_name, duration=enc_time, speed_factor=speed_factor, success=True)
                logger.info(f"Benchmark | {gpu_method_name:<20}: {enc_time:.2f}s ({speed_factor:.2f}x real-time)")
            except Exception as e:
                results[gpu_method_name] = BenchmarkResult(method=gpu_method_name, duration=float('inf'), speed_factor=0, success=False, error=str(e))
                logger.error(f"Benchmark FAILED | {gpu_method_name}: {e}")

        self.benchmark_results[cache_key] = {k: asdict(v) for k, v in results.items()}
        self._save_benchmark_cache()
        logger.info("--- Benchmark Complete ---")
        return results

    def determine_optimal_method(self, benchmark_results: Dict[str, BenchmarkResult]):
        successful_results = {k: v for k, v in benchmark_results.items() if v.success}
        if not successful_results:
            logger.warning("No successful encoding methods found. Falling back to CPU with auto threads.")
            self.preferred_method, self.optimal_cpu_threads = "cpu", 0
            return
            
        best_method_name, best_result = max(successful_results.items(), key=lambda item: item[1].speed_factor)
        logger.info(f"Optimal method determined: '{best_method_name}' with {best_result.speed_factor:.2f}x real-time speed.")
        
        if best_method_name.startswith('gpu_'):
            self.preferred_method, self.optimal_cpu_threads = "gpu", 0
        else:
            self.preferred_method = "cpu"
            self.optimal_cpu_threads = int(best_method_name.split('_')[1]) if "auto" not in best_method_name else 0

    def transcode_video(self, input_path: str, output_path: str, options: Dict = None, force_benchmark: bool = False, benchmark_duration: int = 30):
        if options is None: options = {}
        
        if self.preferred_method is None or force_benchmark:
            benchmark_results = self.benchmark_encoding_methods(input_path, duration=benchmark_duration)
            self.determine_optimal_method(benchmark_results)
            
        logger.info(f"--- Starting Final Video Transcode using method: '{self.preferred_method}' ---")
        
        start_time = time.time()
        try:
            if self.preferred_method == "gpu" and self.gpu_info['capable']:
                result = self._encode_with_vaapi(input_path, output_path, options)
            else: # Fallback to CPU
                options['threads'] = self.optimal_cpu_threads
                result = self._encode_with_cpu(input_path, output_path, options)
        except Exception as e:
            logger.error(f"The selected optimal method '{self.preferred_method}' failed during the full encode. Aborting.", exc_info=True)
            raise e
            
        elapsed = time.time() - start_time
        logger.info(f"Video transcoding completed in {elapsed:.2f} seconds.")
        return result

    # --- Chunking and Metadata Methods (from your second script, adapted) ---

    def calculate_sha1(self, data: bytes) -> str:
        """Calculate SHA-1 hash of data for integrity checking."""
        return hashlib.sha1(data).hexdigest()

    def _process_chunk(self, video_path: Path, index: int, chunk_size: int, video_hash: str) -> Optional[ChunkInfo]:
        """Reads a chunk from the video file, hashes it, and saves it to disk."""
        try:
            start_offset = index * chunk_size
            with open(video_path, 'rb') as file:
                file.seek(start_offset)
                chunk_data = file.read(chunk_size)
                
                if not chunk_data:
                    return None
                
                chunk_hash = self.calculate_sha1(chunk_data)
                
                # Persist chunk to disk in the dedicated chunks directory
                chunk_filename = f"{video_hash}_{index}.chunk"
                chunk_file_path = self.chunks_dir / chunk_filename
                with open(chunk_file_path, 'wb') as chunk_file:
                    chunk_file.write(chunk_data)
                
                return ChunkInfo(
                    index=index,
                    size=len(chunk_data),
                    hash=chunk_hash,
                    offset=start_offset
                )
        except Exception as e:
            logger.error(f"Error processing chunk {index}: {e}", exc_info=True)
            return None

    def chunk_video(self, video_path: str, chunk_size: Optional[int] = None) -> Path:
        """
        Splits a video file into chunks, generates hashes, and creates a metadata file.
        This should be called on the *transcoded* video file.
        """
        logger.info("--- Starting Video Chunking and Metadata Generation ---")
        video_p = Path(video_path)
        if not video_p.exists():
            raise FileNotFoundError(f"Video file not found for chunking: {video_p}")
        
        if chunk_size is None:
            chunk_size = self.default_chunk_size
        
        file_size = video_p.stat().st_size
        video_info = self.get_video_info(str(video_p))
        total_chunks = (file_size + chunk_size - 1) // chunk_size
        
        # Generate a unique hash for the entire video to use in chunk filenames
        video_hash = self.calculate_sha1(video_p.read_bytes())
        
        logger.info(f"Chunking video: {video_p.name} (hash: {video_hash[:8]}...)")
        logger.info(f"File size: {file_size / (1024*1024):.2f} MB, Chunk size: {chunk_size / 1024} KB, Total chunks: {total_chunks}")
        
        chunks = [None] * total_chunks
        
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            future_to_index = {
                executor.submit(self._process_chunk, video_p, i, chunk_size, video_hash): i
                for i in range(total_chunks)
            }
            completed = 0
            for future in as_completed(future_to_index):
                completed += 1
                progress = (completed / total_chunks) * 100
                print(f"\rProcessing chunks: {completed}/{total_chunks} ({progress:.1f}%)", end="")
                index = future_to_index[future]
                chunk_info = future.result()
                if chunk_info:
                    chunks[index] = chunk_info
        print("\nChunk processing complete.")
        
        if any(c is None for c in chunks):
            raise RuntimeError("Failed to process one or more chunks. Aborting metadata creation.")
        
        metadata = NetflacksMetadata(
            filename=video_p.name,
            original_size=file_size,
            chunk_size=chunk_size,
            total_chunks=total_chunks,
            chunks=[asdict(c) for c in chunks],
            created_at=time.time(),
            mime_type=self._get_mime_type(video_p.suffix),
            duration=video_info.get('duration'),
            resolution=video_info.get('resolution'),
            fps=video_info.get('fps')
        )
        
        # Save metadata to a .netflacks file (which is just JSON)
        metadata_filename = f"{video_p.stem}.netflacks"
        metadata_path = self.cache_dir / metadata_filename
        with open(metadata_path, 'w') as f:
            json.dump(asdict(metadata), f, indent=2)
        
        logger.info(f"Successfully created metadata file: {metadata_path}")
        return metadata_path
    
    # --- Utility Methods ---

    def get_video_info(self, video_path: str) -> Dict:
        try:
            probe = ffmpeg.probe(video_path)
            stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
            if stream:
                fps = 0
                if 'r_frame_rate' in stream and stream['r_frame_rate'] != '0/0':
                    try: fps = float(Fraction(stream['r_frame_rate']))
                    except (ValueError, ZeroDivisionError): pass
                return {
                    'duration': float(stream.get('duration', 0)),
                    'fps': fps,
                    'resolution': (int(stream['width']), int(stream['height'])),
                }
        except Exception as e:
            logger.error(f"Error getting video info for {video_path}: {e}")
        return {}

    def _get_mime_type(self, extension: str) -> str:
        mime_types = {'.mp4': 'video/mp4', '.mkv': 'video/x-matroska', '.webm': 'video/webm'}
        return mime_types.get(extension.lower(), 'video/unknown')

    def cleanup(self):
        try:
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            logger.info("Cleanup of temporary benchmark files completed.")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def __del__(self):
        self.cleanup()
        
    # --- Main Orchestration Method ---

    def process_and_chunk_video(self, input_path: str, output_dir: str, force_benchmark: bool = False, benchmark_duration: int = 10, chunk_size: Optional[int] = None) -> Tuple[Path, Path]:
        """
        Runs the full pipeline: transcode, then chunk, and create metadata.
        
        Returns:
            A tuple containing (path_to_transcoded_video, path_to_metadata_file).
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # Define path for the transcoded video
        input_p = Path(input_path)
        transcoded_video_path = output_dir / f"{input_p.stem}_processed.mp4"
        
        # --- Step 1: Transcode the video using the optimal method ---
        self.transcode_video(
            input_path,
            str(transcoded_video_path),
            options={'crf': 23, 'qp': 24},
            force_benchmark=force_benchmark,
            benchmark_duration=benchmark_duration
        )
        
        # --- Step 2: Chunk the newly transcoded video and generate metadata ---
        metadata_path = self.chunk_video(str(transcoded_video_path), chunk_size=chunk_size)
        
        return transcoded_video_path, metadata_path


if __name__ == "__main__":
    # --- CONFIGURATION ---
    BENCHMARK_DURATION_SECONDS = 10
    FORCE_REBENCHMARK = False
    CLEAR_CACHE_ON_START = False # Set to True to delete benchmark cache and all chunks

    # --- SCRIPT EXECUTION ---
    main_start_time = time.time()
    
    cache_path = Path("./video_cache")
    if CLEAR_CACHE_ON_START and cache_path.exists():
        logger.warning(f"CLEAR_CACHE_ON_START is True. Deleting {cache_path}")
        shutil.rmtree(cache_path)

    processor = LightweightVideoProcessor(max_cpu_threads=8)
    
    # Define input and output paths
    video_path = "/home/shyan/Desktop/Code/Bittorrent/public/sample_video.mp4"
    output_dir = Path("/home/shyan/Desktop/Code/Bittorrent/public/processed_video_folder")
    
    try:
        # Run the full pipeline
        transcoded_path, metadata_path = processor.process_and_chunk_video(
            video_path,
            str(output_dir),
            force_benchmark=FORCE_REBENCHMARK,
            benchmark_duration=BENCHMARK_DURATION_SECONDS
        )
        
        main_total_time = time.time() - main_start_time
        logger.info("="*60)
        logger.info("✅ FULL PIPELINE COMPLETE")
        logger.info(f"Transcoded video saved to: {transcoded_path}")
        logger.info(f"NetFlacks metadata file created at: {metadata_path}")
        logger.info(f"Individual chunks saved in: {processor.chunks_dir}")
        logger.info(f"Total script execution time: {main_total_time:.2f} seconds")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"A critical error occurred during the pipeline.", exc_info=True)
    finally:
        processor.cleanup()