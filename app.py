import os
import base64
from io import BytesIO
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size

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


@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')


@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    """Generate an image using Vertex AI Imagen 3"""
    try:
        data = request.get_json()
        prompt = data.get('prompt')

        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        # Optional parameters
        negative_prompt = data.get('negative_prompt', '')
        number_of_images = data.get('number_of_images', 1)
        aspect_ratio = data.get('aspect_ratio', '1:1')
        model = data.get('model', 'imagen-3.0-generate-001')
        safety_filter_level = data.get('safety_filter_level', 'block_some')
        person_generation = data.get('person_generation', 'allow_adult')
        language = data.get('language', 'auto')
        output_mime_type = data.get('output_mime_type', 'image/png')

        # Generate image
        images = media_generator.generate_image(
            prompt=prompt,
            negative_prompt=negative_prompt,
            number_of_images=number_of_images,
            aspect_ratio=aspect_ratio,
            model=model,
            safety_filter_level=safety_filter_level,
            person_generation=person_generation,
            language=language,
            output_mime_type=output_mime_type
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
