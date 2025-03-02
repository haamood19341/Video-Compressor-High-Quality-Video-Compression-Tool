#!/usr/bin/env python3
"""
Video Compressor

A script to compress large video files while maintaining high visual quality.
Supports batch processing of multiple videos.

Requirements:
- FFmpeg must be installed on your system
- Python 3.6+
"""

import os
import sys
import argparse
import subprocess
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Tuple, Optional


def get_video_info(video_path: str) -> Dict:
    """Get video information using FFmpeg."""
    cmd = [
        "ffmpeg", "-i", video_path,
        "-hide_banner"
    ]
    
    # FFmpeg outputs to stderr
    result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
    info = result.stderr
    
    # Extract basic information
    video_info = {}
    
    # Extract resolution
    resolution_match = None
    for line in info.split('\n'):
        if 'Stream' in line and 'Video' in line:
            import re
            resolution_match = re.search(r'(\d{2,4}x\d{2,4})', line)
            if resolution_match:
                video_info['resolution'] = resolution_match.group(1)
            
            # Extract codec
            codec_match = re.search(r'Video: (\w+)', line)
            if codec_match:
                video_info['codec'] = codec_match.group(1)
                
    # Get file size
    video_info['size_mb'] = os.path.getsize(video_path) / (1024 * 1024)
    
    return video_info


def compress_video(
    input_path: str, 
    output_path: str, 
    target_size_mb: int = 30,
    codec: str = 'libx265',
    crf: int = 28,
    preset: str = 'medium',
    audio_bitrate: str = '128k',
    max_width: Optional[int] = None
) -> Tuple[bool, str, float]:
    """
    Compress a video file using FFmpeg.
    
    Args:
        input_path: Path to the input video file
        output_path: Path to save the compressed video
        target_size_mb: Target file size in MB
        codec: Video codec to use (libx264, libx265, etc.)
        crf: Constant Rate Factor (quality - lower is better)
        preset: Encoding preset (slower = better compression)
        audio_bitrate: Audio bitrate
        max_width: Maximum width to scale video to (keeps aspect ratio)
        
    Returns:
        Tuple of (success, message, compression_ratio)
    """
    start_time = time.time()
    
    try:
        # Get original video info
        original_info = get_video_info(input_path)
        original_size_mb = original_info.get('size_mb', 0)
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Base FFmpeg command
        cmd = ["ffmpeg", "-i", input_path]
        
        # Add scaling if max_width is specified
        if max_width:
            cmd.extend(["-vf", f"scale='min({max_width},iw)':-2"])
        
        # Add video codec settings
        cmd.extend([
            "-c:v", codec,
            "-crf", str(crf),
            "-preset", preset
        ])
        
        # Add audio settings
        cmd.extend([
            "-c:a", "aac",
            "-b:a", audio_bitrate
        ])
        
        # Add additional optimization flags based on codec
        if codec == 'libx265':
            cmd.extend(["-x265-params", "log-level=error"])
        
        # Output file
        cmd.extend(["-y", output_path])
        
        # Run FFmpeg
        process = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        if process.returncode != 0:
            return False, f"FFmpeg error: {process.stderr}", 0
        
        # Get compressed file info
        compressed_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        compression_ratio = original_size_mb / compressed_size_mb if compressed_size_mb > 0 else 0
        
        elapsed_time = time.time() - start_time
        
        result_message = (
            f"Compression complete:\n"
            f"Original size: {original_size_mb:.2f} MB\n"
            f"Compressed size: {compressed_size_mb:.2f} MB\n"
            f"Compression ratio: {compression_ratio:.2f}x\n"
            f"Time taken: {elapsed_time:.2f} seconds"
        )
        
        return True, result_message, compression_ratio
        
    except Exception as e:
        return False, f"Error: {str(e)}", 0


def batch_process(
    input_files: List[str],
    output_dir: str,
    target_size_mb: int = 30,
    codec: str = 'libx265',
    crf: int = 28,
    preset: str = 'medium',
    audio_bitrate: str = '128k',
    max_width: Optional[int] = None,
    max_workers: int = 1
) -> None:
    """Process multiple video files in batch."""
    os.makedirs(output_dir, exist_ok=True)
    
    def process_file(input_path):
        filename = os.path.basename(input_path)
        output_path = os.path.join(output_dir, f"compressed_{filename}")
        
        print(f"Processing: {input_path}")
        success, message, _ = compress_video(
            input_path, 
            output_path,
            target_size_mb,
            codec,
            crf,
            preset,
            audio_bitrate,
            max_width
        )
        
        print(message)
        return success
    
    # Use ThreadPoolExecutor for parallel processing if max_workers > 1
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_file, input_files))
    
    success_count = sum(1 for r in results if r)
    print(f"\nBatch processing complete. {success_count}/{len(input_files)} files processed successfully.")


def check_ffmpeg():
    """Check if FFmpeg is installed."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def main():
    parser = argparse.ArgumentParser(description="Compress video files while maintaining quality")
    
    # Input/output options
    parser.add_argument("input", nargs="+", help="Input video file(s) or directory")
    parser.add_argument("-o", "--output", default="compressed", help="Output directory or file (if single input)")
    
    # Compression options
    parser.add_argument("-s", "--size", type=int, default=30, help="Target size in MB (default: 30)")
    parser.add_argument("-c", "--codec", choices=["libx264", "libx265", "vp9"], default="libx265", 
                        help="Video codec (default: libx265/HEVC)")
    parser.add_argument("--crf", type=int, default=28, help="Constant Rate Factor - quality (lower is better, default: 28)")
    parser.add_argument("-p", "--preset", choices=["ultrafast", "superfast", "veryfast", "faster", "fast", 
                                                 "medium", "slow", "slower", "veryslow"], 
                        default="medium", help="Encoding preset (default: medium)")
    parser.add_argument("-a", "--audio", default="128k", help="Audio bitrate (default: 128k)")
    parser.add_argument("-w", "--max-width", type=int, help="Maximum width to scale video to (keeps aspect ratio)")
    
    # Batch processing options
    parser.add_argument("-j", "--jobs", type=int, default=1, help="Number of parallel jobs (default: 1)")
    
    args = parser.parse_args()
    
    # Check if FFmpeg is installed
    if not check_ffmpeg():
        print("Error: FFmpeg is not installed or not in PATH. Please install FFmpeg first.")
        sys.exit(1)
    
    # Collect input files
    input_files = []
    for input_path in args.input:
        if os.path.isdir(input_path):
            # If input is a directory, find all video files
            for root, _, files in os.walk(input_path):
                for file in files:
                    if file.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv')):
                        input_files.append(os.path.join(root, file))
        elif os.path.isfile(input_path):
            input_files.append(input_path)
        else:
            print(f"Warning: Input '{input_path}' does not exist, skipping.")
    
    if not input_files:
        print("Error: No valid input files found.")
        sys.exit(1)
    
    # Single file mode
    if len(input_files) == 1 and not os.path.isdir(args.output):
        output_path = args.output
        if os.path.isdir(output_path):
            output_path = os.path.join(output_path, f"compressed_{os.path.basename(input_files[0])}")
            
        success, message, _ = compress_video(
            input_files[0],
            output_path,
            args.size,
            args.codec,
            args.crf,
            args.preset,
            args.audio,
            args.max_width
        )
        print(message)
    
    # Batch mode
    else:
        batch_process(
            input_files,
            args.output,
            args.size,
            args.codec,
            args.crf,
            args.preset,
            args.audio,
            args.max_width,
            args.jobs
        )


if __name__ == "__main__":
    main() 