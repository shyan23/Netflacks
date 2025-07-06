# import os
# import hashlib
# import json
# import time
# from typing import Dict, List, Optional, Tuple
# from dataclasses import dataclass
# from pathlib import Path
# import subprocess
# import tempfile
# import psutil
# from concurrent.futures import ThreadPoolExecutor, as_completed
# import threading
# import ffmpeg
# from fractions import Fraction
# import logging
# import shutil

# # Configure logging for clear, informative output
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# # --- Data Classes for structured information ---
# @dataclass
# class ChunkInfo:
#     index: int; size: int; hash: str; offset: int; timestamp: float; data: bytes

# @dataclass
# class VideoMetadata:
#     filename: str; original_size: int; chunk_size: int; total_chunks: int
#     chunks: List[Dict]; created_at: float; mime_type: str
#     duration: Optional[float] = None; resolution: Optional[Tuple[int, int]] = None
#     fps: Optional[float] = None

# @dataclass
# class BenchmarkResult:
#     method: str; duration: float; speed_factor: float; success: bool
#     error: Optional[str] = None


# class LightweightVideoProcessor:
#     """
#     An intelligent video processor that benchmarks hardware to find the fastest
#     encoding method (CPU vs GPU) for a given machine and workload.
#     """
#     def __init__(self, cache_dir: str = "./video_cache", max_threads: int = None,
#                  max_cpu_threads: int = None, benchmark_cache_file: str = "benchmark_cache.json"):
        
#         self.cache_dir = Path(cache_dir)
#         self.cache_dir.mkdir(exist_ok=True)
#         self.benchmark_cache_file = self.cache_dir / benchmark_cache_file
        
#         cpu_count = psutil.cpu_count(logical=True)
#         self.max_threads = max_threads or max(2, cpu_count // 2)
#         self.max_cpu_threads = max_cpu_threads or max(2, cpu_count // 2)
#         self.cpu_boost_threads = cpu_count
        
#         self.chunk_cache: Dict[str, ChunkInfo] = {}
#         self.cache_lock = threading.Lock()
#         self.temp_dir = tempfile.mkdtemp(prefix="netflacks_")
        
#         self.benchmark_results = self._load_benchmark_cache()
#         self.vaapi_device = '/dev/dri/renderD128'
#         self.gpu_info = self.detect_gpu()
        
#         self.preferred_method = None
#         self.optimal_cpu_threads = 0
        
#         logger.info(f"Video processor initialized. CPU threads: default={self.max_cpu_threads}, boost={self.cpu_boost_threads}. GPU: {self.gpu_info['type']}")

#     def _load_benchmark_cache(self):
#         if self.benchmark_cache_file.exists():
#             try:
#                 with open(self.benchmark_cache_file, 'r') as f:
#                     logger.info(f"Loading benchmark cache from {self.benchmark_cache_file}")
#                     return json.load(f)
#             except Exception as e:
#                 logger.warning(f"Could not load benchmark cache: {e}")
#         return {}

#     def _save_benchmark_cache(self):
#         try:
#             logger.info(f"Saving benchmark results to {self.benchmark_cache_file}")
#             with open(self.benchmark_cache_file, 'w') as f:
#                 json.dump(self.benchmark_results, f, indent=2)
#         except Exception as e:
#             logger.warning(f"Could not save benchmark cache: {e}")
            
#     def detect_gpu(self):
#         gpu_info = {'type': 'none', 'description': None, 'capable': False}
#         if shutil.which('nvidia-smi'):
#             try:
#                 result = subprocess.run(['nvidia-smi', '-L'], capture_output=True, text=True, check=True)
#                 gpu_info = {'type': 'nvidia', 'description': result.stdout.strip(), 'capable': True}
#                 logger.info("NVIDIA GPU detected.")
#                 return gpu_info
#             except Exception: pass
#         if os.path.exists(self.vaapi_device):
#             gpu_info = {'type': 'amd_or_intel', 'description': f"VA-API device found at {self.vaapi_device}", 'capable': True}
#             logger.info("VA-API capable GPU (AMD/Intel) detected.")
#             return gpu_info
#         logger.info("No capable GPU detected, will use CPU encoding.")
#         return gpu_info

#     def create_benchmark_clip(self, video_path: str, duration: int) -> str:
#         logger.info(f"Creating a {duration}s benchmark clip from the source video...")
#         clip_path = os.path.join(self.temp_dir, "benchmark_clip.mp4")
#         try:
#             info = self.get_video_info(video_path)
#             video_duration = info.get('duration', 0)
#             start_time = 30 if video_duration > duration + 30 else 0
            
#             (ffmpeg.input(video_path, ss=start_time)
#              .output(clip_path, t=duration, c='copy')
#              .overwrite_output().run(capture_stdout=True, capture_stderr=True))
             
#             logger.info(f"Benchmark clip created successfully at {clip_path}")
#             return clip_path
#         except ffmpeg.Error as e:
#             logger.error(f"Failed to create benchmark clip, falling back to CPU. FFmpeg stderr:\n{e.stderr.decode()}")
#             self.gpu_info['capable'] = False
#             return ""

#     def _has_audio_stream(self, filepath: str) -> bool:
#         """Checks if a video file contains an audio stream."""
#         try:
#             probe = ffmpeg.probe(filepath)
#             return any(stream['codec_type'] == 'audio' for stream in probe['streams'])
#         except ffmpeg.Error:
#             return False

#     def _encode_with_vaapi(self, input_path, output_path, options):
#         logger.info(f"Attempting GPU encoding with VA-API on device {self.vaapi_device}")
#         try:
#             input_video_stream = ffmpeg.input(input_path, hwaccel='vaapi', hwaccel_device=self.vaapi_device, hwaccel_output_format='vaapi').video
#             output_streams = [input_video_stream]
#             output_opts = {'c:v': 'h264_vaapi', 'qp': options.get('qp', 24)}
            
#             if self._has_audio_stream(input_path):
#                 input_audio_stream = ffmpeg.input(input_path).audio
#                 output_streams.append(input_audio_stream)
#                 output_opts['c:a'] = 'copy'

#             (ffmpeg.output(*output_streams, output_path, **output_opts)
#              .overwrite_output().run(capture_stdout=True, capture_stderr=True))
#             return output_path
#         except ffmpeg.Error as e:
#             logger.error(f"VA-API encoding failed. FFmpeg stderr:\n{e.stderr.decode('utf-8')}")
#             raise

#     def _encode_with_cpu(self, input_path, output_path, options):
#         thread_count = options.get('threads', 0)
#         logger.info(f"Attempting CPU encoding with {'auto' if thread_count == 0 else thread_count} threads.")
#         try:
#             input_stream = ffmpeg.input(input_path)
#             output_streams = [input_stream.video]
#             output_opts = {
#                 'c:v': 'libx264', 'preset': options.get('preset', 'fast'),
#                 'crf': options.get('crf', 23), 'movflags': '+faststart',
#             }
#             if thread_count > 0: output_opts['threads'] = thread_count
            
#             if self._has_audio_stream(input_path):
#                 output_streams.append(input_stream.audio)
#                 output_opts['c:a'] = 'copy'

#             (ffmpeg.output(*output_streams, output_path, **output_opts)
#              .overwrite_output().run(capture_stdout=True, capture_stderr=True))
#             return output_path
#         except ffmpeg.Error as e:
#             logger.error(f"CPU encoding failed. FFmpeg stderr:\n{e.stderr.decode()}")
#             raise
    
#     def benchmark_encoding_methods(self, video_path: str, duration: int):
#         logger.info("--- Starting Encoding Performance Benchmark ---")
#         # Add benchmark duration to cache key for more specific caching
#         cache_key = f"{self.gpu_info['type']}_v3_{duration}s"
#         if cache_key in self.benchmark_results:
#             logger.info(f"Using cached benchmark results for key '{cache_key}'.")
#             cached = self.benchmark_results[cache_key]
#             return {k: BenchmarkResult(**v) for k, v in cached.items()}
            
#         test_clip_path = self.create_benchmark_clip(video_path, duration)
#         if not test_clip_path:
#             logger.warning("Aborting benchmark due to clip creation failure.")
#             return {}
            
#         clip_duration = duration
#         results = {}
        
#         cpu_test_threads = [0, self.max_cpu_threads, self.cpu_boost_threads]
#         for thread_count in sorted(list(set(cpu_test_threads))):
#             method_name = f"cpu_{'auto' if thread_count == 0 else thread_count}_threads"
#             output_path = os.path.join(self.temp_dir, f"test_{method_name}.mp4")
#             try:
#                 start_time = time.time()
#                 self._encode_with_cpu(test_clip_path, output_path, {'threads': thread_count})
#                 enc_time = time.time() - start_time
#                 speed_factor = clip_duration / enc_time if enc_time > 0 else 0
#                 results[method_name] = BenchmarkResult(method=method_name, duration=enc_time, speed_factor=speed_factor, success=True)
#                 logger.info(f"Benchmark | {method_name:<20}: {enc_time:.2f}s ({speed_factor:.2f}x real-time)")
#             except Exception as e:
#                 results[method_name] = BenchmarkResult(method=method_name, duration=float('inf'), speed_factor=0, success=False, error=str(e))
#                 logger.error(f"Benchmark FAILED | {method_name}: {e}")
                
#         if self.gpu_info['capable']:
#             gpu_method_name = f"gpu_{self.gpu_info['type']}"
#             output_path = os.path.join(self.temp_dir, f"test_gpu.mp4")
#             try:
#                 start_time = time.time()
#                 self._encode_with_vaapi(test_clip_path, output_path, {})
#                 enc_time = time.time() - start_time
#                 speed_factor = clip_duration / enc_time if enc_time > 0 else 0
#                 results[gpu_method_name] = BenchmarkResult(method=gpu_method_name, duration=enc_time, speed_factor=speed_factor, success=True)
#                 logger.info(f"Benchmark | {gpu_method_name:<20}: {enc_time:.2f}s ({speed_factor:.2f}x real-time)")
#             except Exception as e:
#                 results[gpu_method_name] = BenchmarkResult(method=gpu_method_name, duration=float('inf'), speed_factor=0, success=False, error=str(e))
#                 logger.error(f"Benchmark FAILED | {gpu_method_name}: {e}")

#         self.benchmark_results[cache_key] = {k: v.__dict__ for k, v in results.items()}
#         self._save_benchmark_cache()
#         logger.info("--- Benchmark Complete ---")
#         return results

#     def determine_optimal_method(self, benchmark_results: Dict[str, BenchmarkResult]):
#         successful_results = {k: v for k, v in benchmark_results.items() if v.success}
#         if not successful_results:
#             logger.warning("No successful encoding methods found. Falling back to CPU with auto threads.")
#             self.preferred_method = "cpu"; self.optimal_cpu_threads = 0
#             return
            
#         best_method_name, best_result = max(successful_results.items(), key=lambda item: item[1].speed_factor)
#         logger.info(f"Optimal method determined: '{best_method_name}' with {best_result.speed_factor:.2f}x real-time speed.")
        
#         if best_method_name.startswith('gpu_'):
#             self.preferred_method = "gpu"; self.optimal_cpu_threads = 0
#         else:
#             self.preferred_method = "cpu"
#             if "auto" in best_method_name: self.optimal_cpu_threads = 0
#             else: self.optimal_cpu_threads = int(best_method_name.split('_')[1])

#     def process_video_with_ffmpeg(self, input_path: str, output_path: str, options: Dict = None, force_benchmark: bool = False, benchmark_duration: int = 30):
#         if options is None: options = {}
        
#         if self.preferred_method is None or force_benchmark:
#             benchmark_results = self.benchmark_encoding_methods(input_path, duration=benchmark_duration)
#             self.determine_optimal_method(benchmark_results)
            
#         logger.info(f"--- Starting Final Video Encode using method: '{self.preferred_method}' ---")
        
#         start_time = time.time()
#         try:
#             if self.preferred_method == "gpu" and self.gpu_info['capable']:
#                 result = self._encode_with_vaapi(input_path, output_path, options)
#             else: # Fallback to CPU
#                 options['threads'] = self.optimal_cpu_threads
#                 result = self._encode_with_cpu(input_path, output_path, options)
#         except Exception as e:
#             logger.error(f"The selected optimal method '{self.preferred_method}' failed during the full encode. Aborting.", exc_info=True)
#             raise e
            
#         elapsed = time.time() - start_time
#         logger.info(f"Video encoding completed in {elapsed:.2f} seconds.")
#         return result
    
#     def get_video_info(self, video_path: str) -> Dict:
#         try:
#             probe = ffmpeg.probe(video_path)
#             video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
#             if video_stream:
#                 fps = 0
#                 if 'r_frame_rate' in video_stream:
#                     try: fps = float(Fraction(video_stream['r_frame_rate']))
#                     except (ValueError, ZeroDivisionError): pass
#                 return { 'duration': float(video_stream.get('duration', 0)), 'fps': fps,
#                     'resolution': (int(video_stream['width']), int(video_stream['height'])), }
#         except Exception as e:
#             logger.error(f"Error getting video info: {e}")
#             return {}

#     def cleanup(self):
#         try:
#             if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
#                 shutil.rmtree(self.temp_dir)
#             with self.cache_lock: self.chunk_cache.clear()
#             logger.info("Cleanup completed.")
#         except Exception as e:
#             logger.error(f"Error during cleanup: {e}")

#     def __del__(self):
#         self.cleanup()

# if __name__ == "__main__":
#     # --- CONFIGURATION ---
#     # Here you can tune the benchmark duration.
#     # 15 seconds is a good compromise between speed and accuracy.
#     # 30 seconds is for maximum accuracy.
#     # 5 seconds is for a very quick check.
#     BENCHMARK_DURATION_SECONDS = 10
    
#     # Set to True to force a re-benchmark. Set to False to use cached results if they exist.
#     FORCE_REBENCHMARK = False
    
#     # Clear the cache if you want a completely fresh run (useful after code changes)
#     # Be sure to set FORCE_REBENCHMARK to True as well.
#     CLEAR_CACHE_ON_START = False

#     # --- SCRIPT EXECUTION ---
#     main_start_time = time.time()
    
#     if CLEAR_CACHE_ON_START:
#         cache_file = Path("./video_cache/benchmark_cache.json")
#         if cache_file.exists():
#             logger.warning(f"CLEAR_CACHE_ON_START is True. Deleting {cache_file}")
#             cache_file.unlink()

#     processor = LightweightVideoProcessor(max_cpu_threads=8)
    
#     video_path = "/home/shyan/Desktop/Code/Bittorrent/public/sample_video.mp4"
#     output_dir = Path("/home/shyan/Desktop/Code/Bittorrent/public/processed_video_folder")
#     output_dir.mkdir(exist_ok=True)
#     output_path = str(output_dir / "processed_output_final.mp4")
    
#     try:
#         processed_path = processor.process_video_with_ffmpeg(
#             video_path,
#             output_path,
#             options={'crf': 23, 'qp': 24},
#             force_benchmark=FORCE_REBENCHMARK,
#             benchmark_duration=BENCHMARK_DURATION_SECONDS
#         )
        
#         main_total_time = time.time() - main_start_time
#         logger.info("="*60)
#         logger.info(f"✅ PROCESSING COMPLETE")
#         logger.info(f"Video processed and saved to: {processed_path}")
#         logger.info(f"Total script execution time: {main_total_time:.2f} seconds")
#         logger.info("="*60)
        
#     except Exception as e:
#         logger.error(f"A critical error occurred during processing.", exc_info=True)
#     finally:
#         processor.cleanup()