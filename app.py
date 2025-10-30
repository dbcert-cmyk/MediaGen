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
    """Generate an image using Vertex AI Imagen"""
    try:
        data = request.get_json()
        prompt = data.get('prompt')

        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        # Optional parameters
        negative_prompt = data.get('negative_prompt', '')
        number_of_images = data.get('number_of_images', 1)
        aspect_ratio = data.get('aspect_ratio', '1:1')

        # Generate image
        images = media_generator.generate_image(
            prompt=prompt,
            negative_prompt=negative_prompt,
            number_of_images=number_of_images,
            aspect_ratio=aspect_ratio
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
    """Generate a video using Vertex AI"""
    try:
        data = request.get_json()
        prompt = data.get('prompt')

        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        # Optional parameters
        duration = data.get('duration', 5)  # seconds

        # Generate video
        video_path = media_generator.generate_video(
            prompt=prompt,
            duration=duration
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
