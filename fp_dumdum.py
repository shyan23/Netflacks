    import os
    import hashlib
    import json
    import time
    from typing import Dict, List, Optional, Tuple
    from dataclasses import dataclass
    from pathlib import Path
    import subprocess
    import tempfile
    import psutil
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading
    import ffmpeg

    @dataclass
    class ChunkInfo:
        """Data class to store chunk information"""
        index: int
        size: int
        hash: str
        offset: int
        timestamp: float
        data: bytes

    @dataclass
    class VideoMetadata:
        """Data class to store video metadata"""
        filename: str
        original_size: int
        chunk_size: int
        total_chunks: int
        chunks: List[Dict]
        created_at: float
        mime_type: str
        duration: Optional[float] = None
        resolution: Optional[Tuple[int, int]] = None
        fps: Optional[float] = None

    class LightweightVideoProcessor:
        """
        Lightweight video chunking and processing using ffmpeg-python with multithreading.
        Default device type is always desktop.
        """
        
        def __init__(self, cache_dir: str = "./video_cache", max_threads: int = None):
            self.cache_dir = Path(cache_dir)
            self.cache_dir.mkdir(exist_ok=True)
            
            # Chunk size configuration
            self.default_chunk_size = 512 * 1024  # 512KB
            self.min_chunk_size = 256 * 1024     # 256KB
            self.max_chunk_size = 1024 * 1024    # 1MB
            
            # Thread configuration
            self.max_threads = max_threads or max(2, psutil.cpu_count() // 2)
            
            # Thread-safe in-memory cache for chunks
            self.chunk_cache: Dict[str, ChunkInfo] = {}
            self.cache_lock = threading.Lock()
            
            # Temporary directory for processing
            self.temp_dir = tempfile.mkdtemp(prefix="netflacks_")
            
            print(f"Lightweight video processor initialized with cache directory: {self.cache_dir}")
            print(f"Using {self.max_threads} threads for chunking operations")
        
        def calculate_optimal_chunk_size(self, video_size: int, network_speed: str = 'medium') -> int:
            """
            Calculate optimal chunk size based on video size and network speed.
            Device type is fixed to desktop, so applies a 1.25 multiplier.
            """
            base_size = self.default_chunk_size
            
            network_multipliers = {
                'slow': 0.5,
                'medium': 1.0,
                'fast': 1.5
            }
            
            base_size *= network_multipliers.get(network_speed, 1.0)
            base_size *= 1.25  # Always desktop
            
            chunk_size = max(self.min_chunk_size, min(self.max_chunk_size, int(base_size)))
            return chunk_size
        
        def calculate_sha1(self, data: bytes) -> str:
            """Calculate SHA-1 hash of data for integrity checking"""
            sha1_hash = hashlib.sha1()
            sha1_hash.update(data)
            return sha1_hash.hexdigest()
            
        def estimate_network_speed(self) -> str:
            """Estimate network speed using simple ping test"""
            try:
                # Using a reliable public DNS server for the ping test
                result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                                        capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and 'time=' in result.stdout:
                    ping_time = float(result.stdout.split('time=')[1].split()[0])
                    if ping_time < 50:
                        return 'fast'
                    elif ping_time < 100:
                        return 'medium'
                    else:
                        return 'slow'
            except Exception:
                # Fallback in case of any error (e.g., ping not available, timeout)
                pass
            
            return 'medium'  # Default fallback
        
        def get_video_info(self, video_path: str) -> Dict:
            """Get video information using ffmpeg-python"""
            try:
                probe = ffmpeg.probe(video_path)
                video_stream = next(
                    (stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
                if video_stream:
                    width = int(video_stream['width'])
                    height = int(video_stream['height'])
                    # Use eval to handle fractional frame rates like '30000/1001'
                    fps = eval(video_stream['r_frame_rate']) if 'r_frame_rate' in video_stream else 0
                    duration = float(video_stream.get('duration', 0))
                    return {
                        'duration': duration,
                        'fps': fps,
                        'resolution': (width, height),
                        'width': width,
                        'height': height,
                        'frame_count': int(fps * duration) if fps and duration else 0,
                        'codec': video_stream.get('codec_name'),
                        'bitrate': video_stream.get('bit_rate')
                    }
            except Exception as e:
                print(f"Error getting video info with ffmpeg-python: {e}")
            return {}
        
        def _process_chunk(self, video_path: Path, index: int, chunk_size: int) -> Optional[ChunkInfo]:
            """Process a single chunk (used by thread pool)"""
            try:
                start_offset = index * chunk_size
                with open(video_path, 'rb') as file:
                    file.seek(start_offset)
                    chunk_data = file.read(chunk_size)
                    
                    if not chunk_data:
                        return None
                    
                    chunk_hash = self.calculate_sha1(chunk_data)
                    chunk_info = ChunkInfo(
                        index=index,
                        size=len(chunk_data),
                        hash=chunk_hash,
                        offset=start_offset,
                        timestamp=time.time(),
                        data=chunk_data # Note: storing all chunk data in memory can be intensive
                    )
                    cache_key = f"{video_path.name}_chunk_{index}"
                    with self.cache_lock:
                        self.chunk_cache[cache_key] = chunk_info
                    
                    # Persist chunk to disk in the cache directory
                    chunk_file_path = self.cache_dir / f"{cache_key}.bin"
                    with open(chunk_file_path, 'wb') as chunk_file:
                        chunk_file.write(chunk_data)
                    
                    return chunk_info
            except Exception as e:
                print(f"Error processing chunk {index}: {e}")
                return None
        
        def chunk_video(self, video_path: str, chunk_size: Optional[int] = None,
                        progress_callback: Optional[callable] = None) -> VideoMetadata:
            """Split video file into chunks using multiple threads"""
            video_path = Path(video_path)
            if not video_path.exists():
                raise FileNotFoundError(f"Video file not found: {video_path}")
            
            video_info = self.get_video_info(str(video_path))
            file_size = video_path.stat().st_size
            
            if chunk_size is None:
                network_speed = self.estimate_network_speed()
                chunk_size = self.calculate_optimal_chunk_size(file_size, network_speed)
            
            print(f"Processing video: {video_path.name}")
            print(f"File size: {file_size / (1024*1024):.2f} MB")
            print(f"Chunk size: {chunk_size / 1024:.2f} KB")
            
            total_chunks = (file_size + chunk_size - 1) // chunk_size
            print(f"Total chunks: {total_chunks}")
            
            chunks = [None] * total_chunks
            
            with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                future_to_index = {
                    executor.submit(self._process_chunk, video_path, i, chunk_size): i
                    for i in range(total_chunks)
                }
                completed = 0
                for future in as_completed(future_to_index):
                    index = future_to_index[future]
                    chunk_info = future.result()
                    if chunk_info:
                        chunks[index] = chunk_info
                        completed += 1
                        if progress_callback:
                            progress_callback({
                                'current': completed,
                                'total': total_chunks,
                                'percentage': (completed / total_chunks) * 100
                            })
            
            # Ensure all chunks were processed successfully
            if None in chunks:
                raise RuntimeError("Failed to process one or more chunks")
            
            metadata = VideoMetadata(
                filename=video_path.name,
                original_size=file_size,
                chunk_size=chunk_size,
                total_chunks=total_chunks,
                chunks=[{
                    'index': chunk.index,
                    'size': chunk.size,
                    'hash': chunk.hash,
                    'offset': chunk.offset
                } for chunk in chunks],
                created_at=time.time(),
                mime_type=self._get_mime_type(video_path.suffix),
                duration=video_info.get('duration'),
                resolution=video_info.get('resolution'),
                fps=video_info.get('fps')
            )
            
            metadata_path = self.cache_dir / f"{video_path.name}_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata.__dict__, f, indent=2)
            
            return metadata
        
        def process_video_with_ffmpeg(self, input_path: str, output_path: str,
                                    options: Dict = None) -> str:
            """Process video using FFmpeg for re-encoding or other operations"""
            if options is None:
                options = {}
            # Using the ffmpeg-python wrapper for a more Pythonic approach
            return self._process_with_ffmpeg_python(input_path, output_path, options)
        
        def _process_with_ffmpeg_python(self, input_path: str, output_path: str, options: Dict) -> str:
            """Process video using the ffmpeg-python library"""
            try:
                stream = ffmpeg.input(input_path)
                
                # Apply filters based on options
                if 'resolution' in options:
                    width, height = options['resolution'].split('x')
                    stream = ffmpeg.filter(stream, 'scale', width, height)
                if 'fps' in options:
                    stream = ffmpeg.filter(stream, 'fps', fps=options['fps'])
                
                # Prepare output options
                output_options = {}
                if 'video_bitrate' in options:
                    output_options['b:v'] = options['video_bitrate']
                if 'audio_bitrate' in options:
                    output_options['b:a'] = options['audio_bitrate']
                if 'crf' in options:
                    output_options['crf'] = options['crf']
                if 'preset' in options:
                    output_options['preset'] = options['preset']
                
                # Set codecs and other flags
                output_options['c:v'] = options.get('video_codec', 'libx264')
                output_options['c:a'] = options.get('audio_codec', 'aac')
                output_options['movflags'] = '+faststart' # Essential for web streaming
                
                # Execute FFmpeg command
                ffmpeg.output(stream, output_path, **output_options).overwrite_output().run()
                return output_path
            except Exception as e:
                print(f"Error processing video with ffmpeg-python: {e}")
                raise
        
        def _get_mime_type(self, extension: str) -> str:
            """Get MIME type based on file extension"""
            mime_types = {
                '.mp4': 'video/mp4',
                '.avi': 'video/x-msvideo',
                '.mov': 'video/quicktime',
                '.mkv': 'video/x-matroska',
                '.wmv': 'video/x-ms-wmv',
                '.flv': 'video/x-flv',
                '.webm': 'video/webm',
                '.m4v': 'video/x-m4v',
                '.3gp': 'video/3gpp',
                '.ogv': 'video/ogg'
            }
            return mime_types.get(extension.lower(), 'video/unknown')
        
        def cleanup(self):
            """Clean up temporary files and cache"""
            try:
                if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                    import shutil
                    shutil.rmtree(self.temp_dir)
                with self.cache_lock:
                    self.chunk_cache.clear()
                print("Cleanup completed")
            except Exception as e:
                print(f"Error during cleanup: {e}")
        
        def __del__(self):
            """Destructor to ensure cleanup is called"""
            self.cleanup()

    if __name__ == "__main__":
        total_start_time = time.time()
        
        processor = LightweightVideoProcessor(max_threads=4)
        video_path = "/home/shyan/Desktop/Code/Bittorrent/public/sample_video.mp4"
        
        try:
            # --- Timing for Chunking ---
            chunking_start_time = time.time()
            metadata = processor.chunk_video(video_path)
            chunking_end_time = time.time()
            print(f"Video chunked into {metadata.total_chunks} chunks")
            print(f"--- Chunking took: {chunking_end_time - chunking_start_time:.2f} seconds ---")
            
            # --- Timing for FFmpeg Processing ---
            output_path = "processed_video.mp4"
            options = {
                'resolution': '1280x720',
                'video_codec': 'libx264',
                'audio_codec': 'aac', # Re-enabling audio codec
                'crf': '23',
                'preset': 'fast'
            }
            
            processing_start_time = time.time()
            processed_path = processor.process_video_with_ffmpeg(video_path, output_path, options)
            processing_end_time = time.time()
            print(f"Video processed and saved to: {processed_path}")
            print(f"--- FFmpeg processing took: {processing_end_time - processing_start_time:.2f} seconds ---")

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            processor.cleanup()
            total_end_time = time.time()
            print(f"--- Total execution time: {total_end_time - total_start_time:.2f} seconds ---")
