# Video Compressor

A Python script for compressing large video files while maintaining high visual quality. This tool is designed to reduce file sizes from hundreds of megabytes to 20-30MB while preserving HD quality.

## Features

- Maintains high visual quality after compression
- Supports common video formats (MP4, MOV, AVI, MKV, etc.)
- Uses efficient compression techniques (H.264, H.265/HEVC, VP9)
- Batch processing of multiple videos
- Parallel processing support
- Customizable compression settings
- Graphical user interface for easy batch processing
- Web API and browser interface for remote access
- Ability to cancel compression jobs in progress

## Requirements

- Python 3.6 or higher
- FFmpeg installed and available in your system PATH
- For GUI: Tkinter (included with most Python installations)
- For Web API: Flask and Flask-CORS (installed via requirements.txt)

### Installing FFmpeg

#### Windows
1. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html) or use a package manager like [Chocolatey](https://chocolatey.org/):
   ```
   choco install ffmpeg
   ```

#### macOS
Using Homebrew:
```
brew install ffmpeg
```

#### Linux
Using apt (Ubuntu/Debian):
```
sudo apt update
sudo apt install ffmpeg
```

Using yum (CentOS/RHEL):
```
sudo yum install ffmpeg
```

## Usage

### Command Line Usage

Compress a single video file:

```
python video_compressor.py input_video.mp4 -o compressed_video.mp4
```

Compress all videos in a directory:

```
python video_compressor.py /path/to/videos/ -o /path/to/output/
```

### GUI Usage

For a more user-friendly experience, you can use the graphical interface:

```
python batch_compress.py
```

The GUI allows you to:
- Add multiple video files or entire folders
- Set compression parameters
- Monitor progress with a progress bar
- View real-time logs of the compression process
- Process multiple videos in parallel

### Web API and Browser Interface

For remote access or using the compressor in a web browser:

```
# Windows
run_api_server.bat

# macOS/Linux
./run_api_server.sh
```

Then open your browser and navigate to:
```
http://localhost:5000
```

The web interface allows you to:
- Upload videos directly from your browser
- Customize compression settings
- Monitor compression progress
- Cancel compression jobs in progress
- Download compressed videos
- View compression history

#### API Endpoints

The web API provides the following endpoints:

- `POST /api/compress` - Upload and compress a video
- `GET /api/status/<job_id>` - Get the status of a compression job
- `POST /api/cancel/<job_id>` - Cancel a compression job in progress
- `GET /api/download/<job_id>` - Download a compressed video
- `GET /api/jobs` - List all active compression jobs

### Helper Scripts

For quick compression of a single file:

**Windows:**
```
compress_video.bat input_video.mp4 [output_file.mp4]
```

**macOS/Linux:**
```
./compress_video.sh input_video.mp4 [output_file.mp4]
```
(Make sure to make the script executable with `chmod +x compress_video.sh`)

### Command Line Options

```
python video_compressor.py [-h] [-o OUTPUT] [-s SIZE] [-c {libx264,libx265,vp9}]
                          [--crf CRF] [-p {ultrafast,superfast,veryfast,faster,fast,medium,slow,slower,veryslow}]
                          [-a AUDIO] [-w MAX_WIDTH] [-j JOBS]
                          input [input ...]
```

#### Arguments:

- `input`: Input video file(s) or directory
- `-o, --output`: Output directory or file (if single input)
- `-s, --size`: Target size in MB (default: 30)
- `-c, --codec`: Video codec (default: libx265/HEVC)
  - Options: libx264 (H.264), libx265 (H.265/HEVC), vp9
- `--crf`: Constant Rate Factor - quality (lower is better, default: 28)
- `-p, --preset`: Encoding preset (default: medium)
  - Options: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
- `-a, --audio`: Audio bitrate (default: 128k)
- `-w, --max-width`: Maximum width to scale video to (keeps aspect ratio)
- `-j, --jobs`: Number of parallel jobs (default: 1)

## Examples

### Compress a video to 20MB using H.265/HEVC

```
python video_compressor.py large_video.mp4 -o small_video.mp4 -s 20 -c libx265
```

### Compress a video with higher quality (lower CRF)

```
python video_compressor.py large_video.mp4 -o high_quality.mp4 --crf 23
```

### Compress a video and resize to 720p max width

```
python video_compressor.py large_video.mp4 -o resized_video.mp4 -w 1280
```

### Batch process multiple videos with 2 parallel jobs

```
python video_compressor.py /path/to/videos/ -o /path/to/output/ -j 2
```

### Use H.264 for better compatibility

```
python video_compressor.py large_video.mp4 -o compatible_video.mp4 -c libx264
```

## Tips for Best Results

1. **Codec Selection**:
   - Use `libx265` (H.265/HEVC) for best compression ratio
   - Use `libx264` (H.264) for better compatibility with older devices
   - Use `vp9` for web-optimized videos

2. **Quality vs. File Size**:
   - Lower CRF values (18-23) give higher quality but larger files
   - Higher CRF values (28-32) give smaller files but lower quality
   - The default (28) is a good balance for most cases

3. **Encoding Speed vs. Compression Efficiency**:
   - Faster presets (ultrafast, superfast) encode quickly but produce larger files
   - Slower presets (slow, slower, veryslow) take longer but produce smaller files
   - The default (medium) is a good balance for most cases

4. **Resizing**:
   - Use the `-w` option to downscale very high-resolution videos
   - For 1080p output, use `-w 1920`
   - For 720p output, use `-w 1280`

## License

This project is open source and available under the MIT License. 