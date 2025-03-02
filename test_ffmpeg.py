#!/usr/bin/env python3
"""
FFmpeg Installation Test

This script checks if FFmpeg is installed and available in your system PATH.
It also displays the FFmpeg version and available codecs.
"""

import subprocess
import sys
import os
import platform

def check_ffmpeg():
    """Check if FFmpeg is installed and print version information."""
    try:
        # Run FFmpeg version command
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            print("❌ FFmpeg is installed but returned an error.")
            print(f"Error: {result.stderr}")
            return False
        
        # Extract version information
        version_info = result.stdout.split('\n')[0]
        print(f"✅ FFmpeg is installed: {version_info}")
        
        # Check for H.264 encoder
        h264_result = subprocess.run(
            ["ffmpeg", "-encoders"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if "libx264" in h264_result.stdout:
            print("✅ H.264 encoder (libx264) is available")
        else:
            print("❌ H.264 encoder (libx264) is NOT available")
        
        # Check for H.265 encoder
        if "libx265" in h264_result.stdout:
            print("✅ H.265/HEVC encoder (libx265) is available")
        else:
            print("❌ H.265/HEVC encoder (libx265) is NOT available")
        
        # Check for VP9 encoder
        if "libvpx-vp9" in h264_result.stdout:
            print("✅ VP9 encoder (libvpx-vp9) is available")
        else:
            print("❌ VP9 encoder (libvpx-vp9) is NOT available")
        
        return True
        
    except FileNotFoundError:
        print("❌ FFmpeg is NOT installed or not in your PATH.")
        print_installation_instructions()
        return False

def print_installation_instructions():
    """Print FFmpeg installation instructions based on the operating system."""
    system = platform.system()
    
    print("\nInstallation Instructions:")
    
    if system == "Windows":
        print("""
Windows:
1. Download FFmpeg from https://ffmpeg.org/download.html
   - Choose a Windows build like https://github.com/BtbN/FFmpeg-Builds/releases
2. Extract the ZIP file to a location on your computer (e.g., C:\\ffmpeg)
3. Add FFmpeg to your PATH:
   - Right-click on 'This PC' or 'My Computer' and select 'Properties'
   - Click on 'Advanced system settings'
   - Click on 'Environment Variables'
   - Under 'System variables', find and select 'Path', then click 'Edit'
   - Click 'New' and add the path to the 'bin' folder (e.g., C:\\ffmpeg\\bin)
   - Click 'OK' on all dialogs
4. Restart your command prompt or terminal

Alternatively, you can install FFmpeg using Chocolatey:
   choco install ffmpeg
""")
    elif system == "Darwin":  # macOS
        print("""
macOS:
1. Install Homebrew if you don't have it already:
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
2. Install FFmpeg:
   brew install ffmpeg
""")
    elif system == "Linux":
        print("""
Linux (Ubuntu/Debian):
   sudo apt update
   sudo apt install ffmpeg

Linux (CentOS/RHEL):
   sudo yum install epel-release
   sudo yum install ffmpeg
""")
    else:
        print(f"Please visit https://ffmpeg.org/download.html for instructions on how to install FFmpeg on {system}.")

if __name__ == "__main__":
    print("FFmpeg Installation Test")
    print("=======================")
    
    if check_ffmpeg():
        print("\n✅ Your system is ready to use the video compressor!")
        
        # Check if video_compressor.py exists
        if os.path.exists("video_compressor.py"):
            print("✅ video_compressor.py is present in the current directory")
            print("\nYou can now use the video compressor:")
            print("  python video_compressor.py input_video.mp4 -o compressed_video.mp4")
            
            # Check if batch_compress.py exists
            if os.path.exists("batch_compress.py"):
                print("\nOr use the GUI for batch processing:")
                print("  python batch_compress.py")
        else:
            print("❌ video_compressor.py is NOT found in the current directory")
    else:
        print("\n❌ Please install FFmpeg before using the video compressor.")
        sys.exit(1) 