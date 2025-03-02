#!/usr/bin/env python3
"""
Video Compressor API Server

A web API and interface for the video compressor.
"""

import os
import time
import uuid
import json
import threading
import logging
import signal
import subprocess
from typing import Dict, List, Optional
from pathlib import Path
from functools import wraps

from flask import Flask, request, jsonify, send_from_directory, render_template, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Import the video compressor functions
from video_compressor import compress_video, get_video_info, check_ffmpeg

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Configuration
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['OUTPUT_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'compressed')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 * 1024  # 5GB max upload size
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'mov', 'avi', 'mkv', 'wmv', 'flv'}

# Create upload and output directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Store active compression jobs
active_jobs = {}
job_lock = threading.Lock()

# Store active processes for cancellation
active_processes = {}
process_lock = threading.Lock()

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_job_status(job_id):
    """Get the status of a compression job."""
    with job_lock:
        return active_jobs.get(job_id, {})

def update_job_status(job_id, status, **kwargs):
    """Update the status of a compression job."""
    with job_lock:
        if job_id not in active_jobs:
            active_jobs[job_id] = {}
        
        active_jobs[job_id].update({
            'status': status,
            'updated_at': time.time(),
            **kwargs
        })

def clean_old_jobs():
    """Remove completed jobs older than 1 hour."""
    current_time = time.time()
    with job_lock:
        for job_id in list(active_jobs.keys()):
            job = active_jobs[job_id]
            if job.get('status') in ['completed', 'failed', 'cancelled'] and current_time - job.get('updated_at', 0) > 3600:
                del active_jobs[job_id]

def register_process(job_id, process):
    """Register a process for potential cancellation."""
    with process_lock:
        active_processes[job_id] = process

def unregister_process(job_id):
    """Unregister a process after completion or cancellation."""
    with process_lock:
        if job_id in active_processes:
            del active_processes[job_id]

def cancel_process(job_id):
    """Cancel a running process."""
    with process_lock:
        process = active_processes.get(job_id)
        if process:
            try:
                # On Windows, we need to use taskkill to kill the process tree
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(process.pid)], 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                else:
                    # On Unix-like systems, we can use process group
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                return True
            except Exception as e:
                logger.error(f"Error cancelling process: {e}")
                return False
        return False

def process_video_async(job_id, input_path, output_path, compression_options):
    """Process a video asynchronously."""
    try:
        update_job_status(job_id, 'processing', progress=0)
        
        # Get original video info
        original_info = get_video_info(input_path)
        original_size = original_info.get('size_mb', 0)
        
        update_job_status(
            job_id, 
            'processing', 
            progress=10, 
            original_info=original_info
        )
        
        # Prepare FFmpeg command
        cmd = ["ffmpeg", "-i", input_path]
        
        # Add scaling if max_width is specified
        max_width = compression_options.get('max_width')
        if max_width:
            cmd.extend(["-vf", f"scale='min({max_width},iw)':-2"])
        
        # Add video codec settings
        cmd.extend([
            "-c:v", compression_options.get('codec', 'libx265'),
            "-crf", str(compression_options.get('crf', 28)),
            "-preset", compression_options.get('preset', 'medium')
        ])
        
        # Add audio settings
        cmd.extend([
            "-c:a", "aac",
            "-b:a", compression_options.get('audio_bitrate', '128k')
        ])
        
        # Add additional optimization flags based on codec
        if compression_options.get('codec') == 'libx265':
            cmd.extend(["-x265-params", "log-level=error"])
        
        # Output file
        cmd.extend(["-y", output_path])
        
        # Run FFmpeg with process tracking for cancellation
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
            # Create a new process group on Unix-like systems
            preexec_fn=os.setpgrp if os.name != 'nt' else None
        )
        
        # Register the process for potential cancellation
        register_process(job_id, process)
        
        # Wait for the process to complete
        stdout, stderr = process.communicate()
        
        # Unregister the process
        unregister_process(job_id)
        
        # Check if the job was cancelled
        job_status = get_job_status(job_id)
        if job_status.get('status') == 'cancelled':
            # Clean up the output file if it exists
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
            return
        
        if process.returncode != 0:
            update_job_status(job_id, 'failed', message=f"FFmpeg error: {stderr}")
            return
        
        # Get compressed file info
        compressed_info = get_video_info(output_path)
        compressed_size = compressed_info.get('size_mb', 0)
        compression_ratio = original_size / compressed_size if compressed_size > 0 else 0
        compression_percent = ((original_size - compressed_size) / original_size) * 100 if original_size > 0 else 0
        
        update_job_status(
            job_id, 
            'completed', 
            progress=100,
            message="Compression complete",
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            compression_percent=compression_percent,
            output_filename=os.path.basename(output_path)
        )
            
    except Exception as e:
        logger.exception(f"Error processing video for job {job_id}")
        update_job_status(job_id, 'failed', message=str(e))
        
        # Unregister the process if an exception occurred
        unregister_process(job_id)

@app.route('/')
def index():
    """Render the web interface."""
    return render_template('index.html')

@app.route('/api/compress', methods=['POST'])
def compress_video_api():
    """API endpoint to compress a video."""
    # Check if FFmpeg is installed
    if not check_ffmpeg():
        return jsonify({
            'success': False,
            'message': 'FFmpeg is not installed or not in PATH'
        }), 500
    
    # Check if a file was uploaded
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'message': 'No file part in the request'
        }), 400
    
    file = request.files['file']
    
    # Check if the file is empty
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': 'No file selected'
        }), 400
    
    # Check if the file extension is allowed
    if not allowed_file(file.filename):
        return jsonify({
            'success': False,
            'message': f'File type not allowed. Allowed types: {", ".join(app.config["ALLOWED_EXTENSIONS"])}'
        }), 400
    
    # Generate a unique job ID and secure filename
    job_id = str(uuid.uuid4())
    filename = secure_filename(file.filename)
    base_name, extension = os.path.splitext(filename)
    
    # Save the uploaded file
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}_{filename}")
    file.save(input_path)
    
    # Prepare output path
    output_filename = f"compressed_{base_name}{extension}"
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{job_id}_{output_filename}")
    
    # Get compression options from the request
    compression_options = {
        'target_size_mb': int(request.form.get('target_size_mb', 30)),
        'codec': request.form.get('codec', 'libx265'),
        'crf': int(request.form.get('crf', 28)),
        'preset': request.form.get('preset', 'medium'),
        'audio_bitrate': request.form.get('audio_bitrate', '128k'),
    }
    
    # Add max_width if provided
    max_width = request.form.get('max_width')
    if max_width and max_width.isdigit():
        compression_options['max_width'] = int(max_width)
    
    # Initialize job status
    update_job_status(
        job_id, 
        'queued',
        filename=filename,
        input_path=input_path,
        output_path=output_path,
        compression_options=compression_options
    )
    
    # Start compression in a background thread
    threading.Thread(
        target=process_video_async,
        args=(job_id, input_path, output_path, compression_options),
        daemon=True
    ).start()
    
    # Return job ID
    return jsonify({
        'success': True,
        'job_id': job_id,
        'message': 'Video compression started'
    })

@app.route('/api/status/<job_id>', methods=['GET'])
def get_job_status_api(job_id):
    """API endpoint to get the status of a compression job."""
    job = get_job_status(job_id)
    
    if not job:
        return jsonify({
            'success': False,
            'message': 'Job not found'
        }), 404
    
    return jsonify({
        'success': True,
        'job': job
    })

@app.route('/api/cancel/<job_id>', methods=['POST'])
def cancel_job(job_id):
    """API endpoint to cancel a compression job."""
    job = get_job_status(job_id)
    
    if not job:
        return jsonify({
            'success': False,
            'message': 'Job not found'
        }), 404
    
    if job.get('status') not in ['queued', 'processing']:
        return jsonify({
            'success': False,
            'message': f'Cannot cancel job with status: {job.get("status")}'
        }), 400
    
    # Cancel the process
    cancelled = cancel_process(job_id)
    
    # Update job status
    update_job_status(job_id, 'cancelled', message='Job cancelled by user')
    
    return jsonify({
        'success': True,
        'message': 'Job cancelled successfully'
    })

@app.route('/api/download/<job_id>', methods=['GET'])
def download_file(job_id):
    """API endpoint to download a compressed video."""
    job = get_job_status(job_id)
    
    if not job or job.get('status') != 'completed':
        return jsonify({
            'success': False,
            'message': 'Job not found or not completed'
        }), 404
    
    output_path = job.get('output_path')
    
    if not output_path or not os.path.exists(output_path):
        return jsonify({
            'success': False,
            'message': 'Output file not found'
        }), 404
    
    directory = os.path.dirname(output_path)
    filename = os.path.basename(output_path)
    
    return send_from_directory(
        directory,
        filename,
        as_attachment=True,
        download_name=job.get('output_filename', filename)
    )

@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """API endpoint to list all active jobs."""
    clean_old_jobs()
    
    with job_lock:
        jobs = {job_id: job for job_id, job in active_jobs.items()}
    
    return jsonify({
        'success': True,
        'jobs': jobs
    })

if __name__ == '__main__':
    # Check if FFmpeg is installed
    if not check_ffmpeg():
        logger.error("FFmpeg is not installed or not in PATH. Please install FFmpeg first.")
        exit(1)
    
    # Start the server
    app.run(host='0.0.0.0', port=5000, debug=True)