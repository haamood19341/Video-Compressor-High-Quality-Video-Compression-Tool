#!/bin/bash

echo "Video Compressor"
echo "==============="

if [ -z "$1" ]; then
    echo "Error: No input file specified."
    echo "Usage: ./compress_video.sh input_file [output_file]"
    exit 1
fi

INPUT="$1"
OUTPUT="compressed_$(basename "$INPUT")"

if [ ! -z "$2" ]; then
    OUTPUT="$2"
fi

echo "Input: $INPUT"
echo "Output: $OUTPUT"
echo ""
echo "Starting compression..."
python3 video_compressor.py "$INPUT" -o "$OUTPUT"

echo ""
echo "Done!" 