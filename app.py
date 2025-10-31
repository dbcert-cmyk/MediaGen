import os
import base64
from io import BytesIO
from flask import Flask, render_template, request, jsonify, send_file
from dotenv import load_dotenv
from video_editor import VideoEditor
from pricing import estimate_image_cost, estimate_video_cost, VertexAIPricing

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max request size (for video uploads)

# Check if running in mock mode
mock_mode = os.getenv('MOCK_MODE', 'false').lower() == 'true'

if mock_mode:
    # Use mock service for testing without GCP
    from mock_service import MockMediaGenerator
    media_generator = MockMediaGenerator()
    print("\n" + "="*60)
    print("🎭 MOCK MODE ENABLED - Testing without GCP credentials")
    print("   No costs will be incurred, placeholder media will be generated")
    print("="*60 + "\n")
else:
    # Use real Vertex AI service
    from vertex_ai_service import VertexAIMediaGenerator
    project_id = os.getenv('GCP_PROJECT_ID')
    location = os.getenv('GCP_LOCATION', 'us-central1')

    if not project_id:
        raise ValueError("GCP_PROJECT_ID environment variable is required (or set MOCK_MODE=true to test without GCP)")

    media_generator = VertexAIMediaGenerator(project_id, location)
    print(f"\n✅ Vertex AI initialized for project: {project_id}\n")

# Initialize video editor
video_editor = VideoEditor(mock_mode=mock_mode)


@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')


@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    """Generate an image using Vertex AI Gemini 2.5 Flash Image (Nano Banana)"""
    try:
        # Handle both JSON and form data (for file uploads)
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()

        prompt = data.get('prompt')

        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        # Optional parameters
        number_of_images = int(data.get('number_of_images', 1))
        aspect_ratio = data.get('aspect_ratio', '1:1')
        temperature = float(data.get('temperature', 1.0))
        top_p = float(data.get('top_p', 0.95))
        top_k = int(data.get('top_k', 64))
        output_mime_type = data.get('output_mime_type', 'image/png')

        # Handle input image file uploads (up to 3 images)
        input_images = []
        for i in range(1, 4):
            field_name = f'input_image_{i}'
            if field_name in request.files:
                file = request.files[field_name]
                if file.filename:
                    input_images.append(file.read())

        # Generate image
        images = media_generator.generate_image(
            prompt=prompt,
            number_of_images=number_of_images,
            aspect_ratio=aspect_ratio,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            output_mime_type=output_mime_type,
            input_images=input_images if input_images else None
        )

        # Convert images to base64 for response
        image_data = []
        for img in images:
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            image_data.append(img_str)

        return jsonify({
            'success': True,
            'images': image_data,
            'prompt': prompt
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/generate-video', methods=['POST'])
def generate_video():
    """Generate a video using Vertex AI Veo"""
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()

        prompt = data.get('prompt', '')

        # Prompt is optional if image is provided
        has_image = 'input_image' in request.files
        if not prompt and not has_image:
            return jsonify({'error': 'Either prompt or input image is required'}), 400

        # Optional parameters
        model = data.get('model', 'veo-3.1-generate-001')
        aspect_ratio = data.get('aspect_ratio', '16:9')
        duration_seconds = int(data.get('duration_seconds', 8))
        resolution = data.get('resolution', '720p')
        compression_quality = data.get('compression_quality', 'optimized')
        enhance_prompt = data.get('enhance_prompt', 'true').lower() == 'true'
        generate_audio = data.get('generate_audio', 'false').lower() == 'true'
        negative_prompt = data.get('negative_prompt', '')
        person_generation = data.get('person_generation', 'allow_adult')
        sample_count = int(data.get('sample_count', 1))
        seed_val = data.get('seed', None)
        seed = int(seed_val) if seed_val and seed_val != 'null' else None
        resize_mode = data.get('resize_mode', 'pad')
        storage_uri = data.get('storage_uri', None)

        # Handle file uploads
        image_bytes = None
        last_frame_bytes = None
        reference_images = None

        if 'input_image' in request.files:
            file = request.files['input_image']
            if file.filename:
                image_bytes = file.read()

        if 'last_frame' in request.files:
            file = request.files['last_frame']
            if file.filename:
                last_frame_bytes = file.read()

        # Handle reference images (up to 3)
        ref_imgs = []
        for i in range(1, 4):
            field_name = f'reference_image_{i}'
            if field_name in request.files:
                file = request.files[field_name]
                if file.filename:
                    ref_type = data.get(f'reference_type_{i}', 'asset')
                    ref_imgs.append({
                        'bytes': file.read(),
                        'type': ref_type
                    })
        if ref_imgs:
            reference_images = ref_imgs

        # Generate video
        video_path = media_generator.generate_video(
            prompt=prompt,
            model=model,
            aspect_ratio=aspect_ratio,
            duration_seconds=duration_seconds,
            resolution=resolution,
            compression_quality=compression_quality,
            enhance_prompt=enhance_prompt,
            generate_audio=generate_audio,
            negative_prompt=negative_prompt,
            person_generation=person_generation,
            sample_count=sample_count,
            seed=seed,
            resize_mode=resize_mode,
            storage_uri=storage_uri,
            image_bytes=image_bytes,
            last_frame_bytes=last_frame_bytes,
            reference_images=reference_images
        )

        # Read video file and convert to base64
        with open(video_path, 'rb') as video_file:
            video_data = base64.b64encode(video_file.read()).decode()

        return jsonify({
            'success': True,
            'video': video_data,
            'prompt': prompt
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/trim-video', methods=['POST'])
def trim_video():
    """Trim/cut a video to specified time range"""
    try:
        # Get uploaded video file
        if 'video' not in request.files:
            return jsonify({'error': 'No video file uploaded'}), 400

        video_file = request.files['video']
        if not video_file.filename:
            return jsonify({'error': 'Empty video file'}), 400

        # Get parameters
        start_time = float(request.form.get('start_time', 0))
        end_time = float(request.form.get('end_time', 5))

        # Save uploaded video temporarily
        timestamp = int(time.time())
        temp_input = f"generated_media/temp_input_{timestamp}.mp4"
        os.makedirs('generated_media', exist_ok=True)
        video_file.save(temp_input)

        # Trim the video
        output_path = video_editor.trim_video(temp_input, start_time, end_time)

        # Read trimmed video and convert to base64
        with open(output_path, 'rb') as f:
            video_data = base64.b64encode(f.read()).decode()

        # Clean up temporary file
        if os.path.exists(temp_input):
            os.remove(temp_input)

        return jsonify({
            'success': True,
            'video': video_data,
            'message': f'Video trimmed from {start_time}s to {end_time}s'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/add-text-overlay', methods=['POST'])
def add_text_overlay():
    """Add text overlay to a video"""
    try:
        # Get uploaded video file
        if 'video' not in request.files:
            return jsonify({'error': 'No video file uploaded'}), 400

        video_file = request.files['video']
        if not video_file.filename:
            return jsonify({'error': 'Empty video file'}), 400

        # Get parameters
        text = request.form.get('text', 'Sample Text')
        position = request.form.get('position', 'bottom')
        font_size = int(request.form.get('font_size', 24))
        font_color = request.form.get('font_color', 'white')

        # Save uploaded video temporarily
        import time as time_module
        timestamp = int(time_module.time())
        temp_input = f"generated_media/temp_input_{timestamp}.mp4"
        os.makedirs('generated_media', exist_ok=True)
        video_file.save(temp_input)

        # Add text overlay
        output_path = video_editor.add_text_overlay(
            temp_input,
            text=text,
            position=position,
            font_size=font_size,
            font_color=font_color
        )

        # Read video with text and convert to base64
        with open(output_path, 'rb') as f:
            video_data = base64.b64encode(f.read()).decode()

        # Clean up temporary file
        if os.path.exists(temp_input):
            os.remove(temp_input)

        return jsonify({
            'success': True,
            'video': video_data,
            'message': f'Text "{text}" added to video'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/combine-videos', methods=['POST'])
def combine_videos():
    """Combine multiple videos into one"""
    try:
        # Get uploaded video files
        video_files = []
        for key in request.files:
            if key.startswith('video'):
                video_files.append(request.files[key])

        if len(video_files) < 2:
            return jsonify({'error': 'At least 2 videos required'}), 400

        # Save uploaded videos temporarily
        import time as time_module
        timestamp = int(time_module.time())
        temp_paths = []

        for idx, video_file in enumerate(video_files):
            temp_path = f"generated_media/temp_video_{timestamp}_{idx}.mp4"
            video_file.save(temp_path)
            temp_paths.append(temp_path)

        # Combine videos
        output_path = video_editor.combine_videos(temp_paths)

        # Read combined video and convert to base64
        with open(output_path, 'rb') as f:
            video_data = base64.b64encode(f.read()).decode()

        # Clean up temporary files
        for temp_path in temp_paths:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        return jsonify({
            'success': True,
            'video': video_data,
            'message': f'{len(video_files)} videos combined successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/change-speed', methods=['POST'])
def change_speed():
    """Change video playback speed"""
    try:
        # Get uploaded video file
        if 'video' not in request.files:
            return jsonify({'error': 'No video file uploaded'}), 400

        video_file = request.files['video']
        if not video_file.filename:
            return jsonify({'error': 'Empty video file'}), 400

        # Get speed parameter
        speed = float(request.form.get('speed', 1.0))

        # Validate speed range
        if speed < 0.25 or speed > 4.0:
            return jsonify({'error': 'Speed must be between 0.25x and 4.0x'}), 400

        # Save uploaded video temporarily
        import time as time_module
        timestamp = int(time_module.time())
        temp_input = f"generated_media/temp_input_{timestamp}.mp4"
        os.makedirs('generated_media', exist_ok=True)
        video_file.save(temp_input)

        # Change video speed
        output_path = video_editor.change_speed(temp_input, speed)

        # Read speed-adjusted video and convert to base64
        with open(output_path, 'rb') as f:
            video_data = base64.b64encode(f.read()).decode()

        # Clean up temporary file
        if os.path.exists(temp_input):
            os.remove(temp_input)

        return jsonify({
            'success': True,
            'video': video_data,
            'message': f'Video speed changed to {speed}x'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/estimate-image-cost', methods=['POST'])
def api_estimate_image_cost():
    """Estimate cost for image generation"""
    try:
        data = request.get_json()
        number_of_images = int(data.get('number_of_images', 1))

        cost_estimate = estimate_image_cost(number_of_images)

        return jsonify({
            'success': True,
            'cost': cost_estimate
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/estimate-video-cost', methods=['POST'])
def api_estimate_video_cost():
    """Estimate cost for video generation"""
    try:
        data = request.get_json()
        duration_seconds = int(data.get('duration_seconds', 8))
        resolution = data.get('resolution', '720p')
        sample_count = int(data.get('sample_count', 1))

        cost_estimate = estimate_video_cost(duration_seconds, resolution, sample_count)

        return jsonify({
            'success': True,
            'cost': cost_estimate
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/pricing-info')
def api_pricing_info():
    """Get all pricing information"""
    try:
        pricing_info = VertexAIPricing.get_pricing_info()
        return jsonify({
            'success': True,
            'pricing': pricing_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'MediaGen API'})


if __name__ == '__main__':
    # Create output directory if it doesn't exist
    os.makedirs('generated_media', exist_ok=True)

    # Run the app
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
