import os
import time
import base64
from io import BytesIO
from flask import Flask, render_template, request, jsonify, send_file
from dotenv import load_dotenv
from video_editor import VideoEditor
from pricing import estimate_image_cost, estimate_video_cost, VertexAIPricing
from storyboard import Storyboard, Scene, StoryboardRenderer, create_scene, estimate_storyboard_cost

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

# Initialize storyboard renderer
storyboard_renderer = StoryboardRenderer(mock_mode=mock_mode)


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
        model = data.get('model', 'veo-3.1-generate-preview')
        # Ensure model is a string (in case form sends wrong type)
        if not isinstance(model, str):
            model = 'veo-3.1-generate-preview'
        # Map legacy model names
        if model == 'veo-3.1-generate-001':
            model = 'veo-3.1-generate-preview'

        aspect_ratio = data.get('aspect_ratio', '16:9')
        duration_seconds = int(data.get('duration_seconds', 8))
        resolution = data.get('resolution', '720p')
        compression_quality = data.get('compression_quality', 'optimized')

        # Convert string booleans to actual booleans
        enhance_prompt_val = data.get('enhance_prompt', 'true')
        enhance_prompt = enhance_prompt_val if isinstance(enhance_prompt_val, bool) else (str(enhance_prompt_val).lower() == 'true')

        generate_audio_val = data.get('generate_audio', 'false')
        generate_audio = generate_audio_val if isinstance(generate_audio_val, bool) else (str(generate_audio_val).lower() == 'true')
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
        # Try both file upload format and base64 format
        for i in range(3):
            # Try file upload format (reference_image_1, reference_image_2, reference_image_3)
            field_name_file = f'reference_image_{i+1}'
            if field_name_file in request.files:
                file = request.files[field_name_file]
                if file.filename:
                    ref_type = data.get(f'reference_type_{i+1}', 'asset')
                    ref_imgs.append({
                        'bytes': file.read(),
                        'type': ref_type
                    })
            # Try base64 format from storyboard (reference_image_0, reference_image_1, reference_image_2)
            field_name_base64 = f'reference_image_{i}'
            if field_name_base64 in data:
                import base64
                base64_data = data.get(field_name_base64)
                ref_type = data.get(f'reference_image_{i}_type', 'asset')
                ref_imgs.append({
                    'bytes': base64.b64decode(base64_data),
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

        # Handle both single path (string) and multiple paths (list)
        video_paths = video_path if isinstance(video_path, list) else [video_path]

        # Read all video files and convert to base64
        videos_data = []
        for path in video_paths:
            with open(path, 'rb') as video_file:
                video_data = base64.b64encode(video_file.read()).decode()
                videos_data.append(video_data)

        return jsonify({
            'success': True,
            'video': videos_data[0],  # For backward compatibility (first video)
            'videos': videos_data,  # Array format for multiple videos
            'file_paths': video_paths,  # File paths for scene tracking
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


@app.route('/api/storyboard/save', methods=['POST'])
def save_storyboard():
    """Save a storyboard"""
    try:
        data = request.get_json()

        # Create or load existing storyboard
        storyboard_id = data.get('id')
        if storyboard_id:
            storyboard = Storyboard.load(storyboard_id) or Storyboard(storyboard_id=storyboard_id)
        else:
            storyboard = Storyboard()

        storyboard.title = data.get('title', storyboard.title)

        # Add scenes
        storyboard.scenes = []
        for scene_data in data.get('scenes', []):
            scene = Scene(
                scene_id=scene_data.get('id', f"scene_{int(time.time() * 1000)}"),
                prompt=scene_data['prompt'],
                duration=scene_data.get('duration', 8),
                resolution=scene_data.get('resolution', '720p'),
                aspect_ratio=scene_data.get('aspect_ratio', '16:9')
            )
            storyboard.add_scene(scene)

        # Save to file
        filepath = storyboard.save()

        return jsonify({
            'success': True,
            'storyboard': storyboard.to_dict(),
            'filepath': filepath
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/storyboard/load/<storyboard_id>')
def load_storyboard(storyboard_id):
    """Load a storyboard"""
    try:
        storyboard = Storyboard.load(storyboard_id)

        if not storyboard:
            return jsonify({
                'success': False,
                'error': 'Storyboard not found'
            }), 404

        return jsonify({
            'success': True,
            'storyboard': storyboard.to_dict()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/storyboard/estimate-cost', methods=['POST'])
def estimate_storyboard_cost_api():
    """Estimate cost for a storyboard"""
    try:
        data = request.get_json()
        scenes_data = data.get('scenes', [])

        # Create scene objects
        scenes = []
        for scene_data in scenes_data:
            scene = Scene(
                scene_id=scene_data.get('id', f"scene_{int(time.time() * 1000)}"),
                prompt=scene_data['prompt'],
                duration=scene_data.get('duration', 8)
            )
            scenes.append(scene)

        cost_info = estimate_storyboard_cost(scenes)

        return jsonify({
            'success': True,
            'cost': cost_info
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/storyboard/combine', methods=['POST'])
def combine_storyboard():
    """Combine storyboard scenes into final video"""
    try:
        data = request.get_json()
        storyboard_id = data.get('storyboard_id')
        title = data.get('title', 'Untitled Storyboard')
        scenes = data.get('scenes', [])

        if not scenes:
            return jsonify({
                'success': False,
                'error': 'No scenes provided'
            }), 400

        # Create temporary video files from base64 data for scenes that need it
        import time as time_module
        import tempfile
        import shutil

        video_paths = []
        temp_files = []

        for i, scene in enumerate(scenes):
            if not scene.get('generated'):
                continue

            # If scene has video_path and file exists, use it
            if scene.get('video_path') and os.path.exists(scene['video_path']):
                video_paths.append(scene['video_path'])
            # Otherwise, create temp file from base64 data
            elif scene.get('video_data'):
                # Create temporary file
                temp_fd, temp_path = tempfile.mkstemp(suffix='.mp4', dir='generated_media')
                os.close(temp_fd)

                # Decode and write video data
                video_bytes = base64.b64decode(scene['video_data'])
                with open(temp_path, 'wb') as f:
                    f.write(video_bytes)

                video_paths.append(temp_path)
                temp_files.append(temp_path)

        if not video_paths:
            return jsonify({
                'success': False,
                'error': 'No generated scenes to combine'
            }), 400

        # Use video editor to combine
        timestamp = int(time_module.time())
        output_path = f"generated_media/storyboard_{storyboard_id or timestamp}.mp4"

        combined_path = video_editor.combine_videos(video_paths, output_path)

        # Clean up temporary files
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except:
                pass

        # Read combined video and convert to base64
        with open(combined_path, 'rb') as f:
            video_data = base64.b64encode(f.read()).decode()

        return jsonify({
            'success': True,
            'video': video_data,
            'path': combined_path,
            'message': f'Combined {len(video_paths)} scenes successfully'
        })

    except Exception as e:
        # Clean up temp files on error
        if 'temp_files' in locals():
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except:
                    pass

        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/storyboard/suggest-prompt', methods=['POST'])
def suggest_scene_prompt():
    """AI-powered scene prompt suggestions using Gemini with advanced context analysis"""
    try:
        data = request.get_json()
        previous_scenes = data.get('previous_scenes', [])
        partial_prompt = data.get('partial_prompt', '')
        scene_position = data.get('scene_position', 'middle')  # beginning, middle, end

        # Analyze ALL existing scenes for better context
        context_analysis = ""
        if previous_scenes:
            # Build comprehensive context
            context_analysis = f"Existing storyboard ({len(previous_scenes)} scenes):\n"
            for i, scene in enumerate(previous_scenes, 1):
                context_analysis += f"{i}. {scene.get('prompt', '')}\n"
        else:
            context_analysis = "This is the FIRST scene. Set the tone and establish the story."

        # Determine what kind of shots are needed
        shot_guidance = ""
        if previous_scenes:
            # Count shot types in existing scenes
            prompts_lower = ' '.join([s.get('prompt', '').lower() for s in previous_scenes])

            # Suggest varied shots
            if len(previous_scenes) % 3 == 0:
                shot_guidance = "Suggest a WIDE or ESTABLISHING shot to reset the scene."
            elif len(previous_scenes) % 3 == 1:
                shot_guidance = "Suggest a MEDIUM shot to show action or interaction."
            else:
                shot_guidance = "Suggest a CLOSE-UP or DETAIL shot for emotional impact."
        else:
            shot_guidance = "First scene should be a WIDE ESTABLISHING SHOT to set the scene and mood."

        # Build the enhanced prompt for Gemini
        system_instruction = f"""You are an expert cinematographer and creative director helping create compelling video storyboards.

{context_analysis}

{shot_guidance}

{"User's idea: '" + partial_prompt + "'" if partial_prompt else ""}

Task: Suggest 3 CREATIVE, SPECIFIC, and VISUALLY COMPELLING scene prompts.

Requirements:
✓ BE SPECIFIC about camera angles, movements, lighting, and mood
✓ VARY the shot types (wide, medium, close-up, tracking, dolly, crane, etc.)
✓ Include CINEMATIC DETAILS (golden hour, dramatic shadows, bokeh, lens flare, etc.)
✓ Ensure STORY CONTINUITY with previous scenes
✓ Make each suggestion VISUALLY DISTINCT from others
✓ Use VIVID, DESCRIPTIVE language
✓ Consider pacing: {scene_position} scene should {"establish tone and setting" if scene_position == "beginning" else "build energy and transitions" if scene_position == "middle" else "provide resolution or climax"}

Shot Type Examples:
- Wide: "Aerial drone shot rising above...", "Wide establishing shot of..."
- Medium: "Medium tracking shot following...", "Over-the-shoulder view of..."
- Close-up: "Extreme close-up on...", "Macro shot revealing..."
- Movement: "Slow dolly push into...", "Smooth crane shot descending from..."

Lighting Examples:
- "Golden hour sunlight streaming through..."
- "Dramatic side lighting with deep shadows..."
- "Soft diffused morning light..."
- "Neon glow reflecting off..."

IMPORTANT: Each suggestion should feel like a real film scene, not generic descriptions.

Format as numbered list:
1. [First suggestion]
2. [Second suggestion]
3. [Third suggestion]"""

        # Use the media generator's text generation capability
        if mock_mode:
            # Enhanced mock suggestions with variety
            suggestions = [
                f"Aerial drone shot slowly circling a secluded mountain lake at sunrise, morning mist hovering over glassy water, soft golden light illuminating distant peaks, cinematic color grading with teal and orange tones.",
                f"Medium tracking shot following a person's silhouette walking through a rain-soaked city street at night, neon signs reflecting in puddles, bokeh lights in background, moody cyberpunk atmosphere.",
                f"Extreme close-up macro shot of dewdrops on a spider web, early morning sunlight creating rainbow refractions, shallow depth of field with dreamy background, slow motion as a gentle breeze causes the web to shimmer."
            ]
        else:
            # Use Gemini to generate suggestions
            try:
                import vertexai
                from vertexai.generative_models import GenerativeModel

                model = GenerativeModel("gemini-2.0-flash-exp")
                response = model.generate_content(system_instruction)

                # Parse the response into individual suggestions
                suggestions_text = response.text.strip()
                suggestions = []
                for line in suggestions_text.split('\n'):
                    line = line.strip()
                    # Remove number and period from start
                    if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                        # Remove leading number, period, dash, or bullet
                        cleaned = line.lstrip('0123456789.-•) ').strip()
                        if cleaned:
                            suggestions.append(cleaned)

                # Ensure we have exactly 3 suggestions
                if len(suggestions) < 3:
                    # Intelligent fallback based on scene count
                    if len(previous_scenes) == 0:
                        suggestions = [
                            "Wide aerial establishing shot of the location at golden hour, cinematic color grading with warm tones, slow reveal of the landscape.",
                            "Medium shot introducing the main subject with natural lighting, shallow depth of field, smooth camera movement following the action.",
                            "Close-up detail shot capturing an important object or emotion, dramatic side lighting with soft shadows."
                        ]
                    elif len(previous_scenes) < 3:
                        suggestions = [
                            "Tracking medium shot following the subject's movement, dynamic camera work with natural lighting and cinematic framing.",
                            "Wide shot revealing new environment or context, establishing spatial relationships, golden hour or dramatic lighting.",
                            "Extreme close-up on facial expression or detail, shallow depth of field, emotionally resonant moment."
                        ]
                    else:
                        suggestions = [
                            "Dramatic wide shot showing conflict or climax, dynamic camera movement, high contrast lighting with deep shadows.",
                            "Intimate close-up capturing resolution or emotion, soft focus background, gentle natural lighting.",
                            "Sweeping crane or dolly shot providing visual conclusion, cinematic composition with balanced elements."
                        ]
                suggestions = suggestions[:3]  # Take only first 3

            except Exception as e:
                print(f"Error generating AI suggestions: {e}")
                # Context-aware fallback suggestions
                if len(previous_scenes) == 0:
                    suggestions = [
                        "Wide aerial establishing shot of a misty valley at sunrise, golden light breaking through clouds, cinematic reveal of the landscape with smooth drone movement.",
                        "Medium tracking shot following a lone figure walking through tall grass, shallow depth of field with bokeh in background, warm natural lighting.",
                        "Close-up detail shot of hands reaching out to touch morning dew on leaves, macro focus with soft blur, peaceful morning atmosphere."
                    ]
                else:
                    suggestions = [
                        "Dynamic tracking shot following the action with fluid camera movement, natural lighting with cinematic color grading, medium frame composition.",
                        "Wide establishing shot showing change in location or time, dramatic lighting shift, smooth transition from previous scene.",
                        "Intimate close-up capturing emotional beat, shallow focus with dreamy bokeh, soft directional lighting highlighting the subject."
                    ]

        return jsonify({
            'success': True,
            'suggestions': suggestions
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'suggestions': [
                "A cinematic wide aerial shot establishing the location at golden hour, smooth drone movement revealing the landscape with dramatic lighting.",
                "A dynamic medium tracking shot following the subject with natural lighting, shallow depth of field, and fluid camera movement.",
                "An intimate extreme close-up highlighting emotion or detail, soft focus background with cinematic bokeh, dramatic side lighting."
            ]
        }), 500


@app.route('/api/storyboard/auto-generate-complete', methods=['POST'])
def auto_generate_complete_storyboard():
    """
    FULL AUTOMATION: AI generates everything from just a concept
    - Analyzes concept and identifies characters/subjects
    - Generates detailed character descriptions
    - Creates 1-3 reference images using Imagen
    - Generates complete storyboard with Veo 3.1 best practices
    - Returns complete package ready for video generation
    """
    try:
        data = request.get_json()
        concept = data.get('concept', '')
        num_scenes = data.get('num_scenes', 5)
        style = data.get('style', 'cinematic')
        pacing = data.get('pacing', 'medium')

        if not concept:
            return jsonify({
                'success': False,
                'error': 'Concept description is required'
            }), 400

        # Step 1: AI Character Analysis & Description Generation
        print("🤖 Step 1: Analyzing concept and generating character descriptions...")

        character_analysis_prompt = f"""Analyze this video concept and create detailed character descriptions:

CONCEPT: {concept}

TASK: Identify the main character(s) or subject(s) and create a highly detailed description.

OUTPUT FORMAT (JSON):
{{
  "has_characters": true/false,
  "character_description": "Detailed description of main character (age, gender, ethnicity, hair, clothing, accessories, personality, features) OR subject/object description if no human character",
  "character_type": "human" / "animal" / "object" / "abstract",
  "reference_image_prompts": [
    "Prompt for reference image 1 (front view/portrait)",
    "Prompt for reference image 2 (side profile/different angle)",
    "Prompt for reference image 3 (in action/context)"
  ]
}}

GUIDELINES:
- If human: Include age, gender, ethnicity, hair (color, length, style), facial features, clothing (specific colors and items), accessories (jewelry, watches, glasses), personality traits
- If animal: Species, breed, size, color, markings, personality
- If object: Type, material, color, style, condition
- Be EXTREMELY specific - this ensures consistency across all scenes
- Reference image prompts should be detailed and photorealistic
- Each reference image should show the same character from different angles

Generate the analysis now:"""

        if mock_mode:
            # Mock response for testing
            character_data = {
                "has_characters": True,
                "character_description": "A 35-year-old male chef with short dark hair, white chef's jacket, black apron",
                "character_type": "human",
                "reference_image_prompts": [
                    "Professional portrait of a chef",
                    "Side profile of a chef in kitchen",
                    "Chef cooking in action"
                ]
            }
        else:
            import vertexai
            from vertexai.generative_models import GenerativeModel
            import json
            import re

            model = GenerativeModel("gemini-2.0-flash-exp")
            response = model.generate_content(character_analysis_prompt)
            response_text = response.text.strip()

            print(f"📄 Raw AI Response (first 500 chars): {response_text[:500]}")

            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
                print("✅ Found JSON in code block")
            else:
                print("⚠️  No code block found, trying to parse response directly")

            # Try to parse JSON
            try:
                character_data = json.loads(response_text)
                print("✅ JSON parsed successfully")
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {e}")
                print(f"📄 Response text: {response_text}")

                # Fallback: Create character data from concept
                print("🔄 Using fallback character creation...")
                character_data = {
                    "has_characters": True,
                    "character_description": f"Main subject from the concept: {concept}",
                    "character_type": "human",
                    "reference_image_prompts": [
                        f"Professional portrait photograph of the main character from: {concept}, photorealistic, high quality, studio lighting",
                        f"Side profile photograph of the character from: {concept}, natural lighting, detailed",
                        f"Action shot of the character from: {concept}, in motion, dynamic composition"
                    ]
                }

        character_description = character_data.get('character_description', '')
        reference_prompts = character_data.get('reference_image_prompts', [])

        print(f"✅ Character Description: {character_description[:100]}...")

        # Step 2: Generate Reference Images using Imagen
        print("🎨 Step 2: Generating reference images using Imagen...")

        reference_images = []
        for i, ref_prompt in enumerate(reference_prompts[:3]):  # Max 3 images
            try:
                print(f"   Generating reference image {i+1}/3...")

                # Generate image using existing media_generator
                # Note: generate_image returns list of PIL Images, need to save first
                images = media_generator.generate_image(
                    prompt=ref_prompt,
                    number_of_images=1,
                    aspect_ratio="1:1"  # Square for reference images
                )

                # Save the image and get path
                timestamp = int(time.time())
                image_path = f"generated_media/reference_{timestamp}_{i}.png"
                os.makedirs('generated_media', exist_ok=True)
                images[0].save(image_path)

                # Read image and convert to base64
                with open(image_path, 'rb') as img_file:
                    image_data = base64.b64encode(img_file.read()).decode()
                    reference_images.append({
                        'data': image_data,
                        'filename': f'reference_{i+1}.png',
                        'type': 'asset',
                        'prompt': ref_prompt
                    })

                print(f"   ✅ Reference image {i+1} generated")

            except Exception as e:
                print(f"   ⚠️  Failed to generate reference image {i+1}: {e}")
                # Continue even if one image fails

        print(f"✅ Generated {len(reference_images)} reference image(s)")

        # Step 3: Generate Complete Storyboard with Character Consistency
        print("📝 Step 3: Generating storyboard scenes with Veo 3.1 best practices...")

        shot_rotation = ['wide', 'medium', 'close-up'] * ((num_scenes // 3) + 1)

        storyboard_generation_prompt = f"""Create {num_scenes} video scene prompts for: {concept}

Character: {character_description}

Style: {style}. Pacing: {pacing}.
Shots: {', '.join([f"{i+1}={shot_rotation[i]}" for i in range(num_scenes)])}

Include character description in EVERY prompt. Use camera movements and lighting.

Return ONLY valid JSON array (no markdown):
[{{"prompt": "scene description", "shot_type": "wide", "duration": 8, "resolution": "720p", "aspect_ratio": "16:9"}}, ...]"""

        if mock_mode:
            scenes = []
            for i in range(num_scenes):
                scenes.append({
                    'prompt': f"Scene {i+1}: {shot_rotation[i]} shot featuring {character_description}, cinematic lighting and composition",
                    'shot_type': shot_rotation[i],
                    'duration': 8,
                    'resolution': '720p',
                    'aspect_ratio': '16:9'
                })
        else:
            model = GenerativeModel("gemini-2.0-flash-exp")
            generation_config = {
                "temperature": 0.9,
                "top_p": 0.95,
                "max_output_tokens": 8192,
            }

            response = model.generate_content(
                storyboard_generation_prompt,
                generation_config=generation_config
            )

            response_text = response.text.strip()

            print(f"📄 Storyboard AI Response (first 500 chars): {response_text[:500] if response_text else '(empty response)'}")

            # If response is empty, use fallback immediately
            if not response_text:
                print("❌ Empty response from AI, using fallback")
                scenes = []
                for i in range(num_scenes):
                    scenes.append({
                        'prompt': f"Scene {i+1}: {shot_rotation[i]} cinematic shot of {character_description}, professional lighting and composition, {style} style with {pacing} pacing",
                        'shot_type': shot_rotation[i],
                        'duration': 8,
                        'resolution': '720p',
                        'aspect_ratio': '16:9'
                    })
            else:
                # Try to extract JSON from markdown code blocks or parse directly
                json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)
                    print("✅ Found JSON array in code block")
                else:
                    # Try to find JSON array directly
                    json_array_match = re.search(r'(\[.*?\])', response_text, re.DOTALL)
                    if json_array_match:
                        response_text = json_array_match.group(1)
                        print("✅ Found JSON array in response")
                    else:
                        print("⚠️  No JSON array found, trying to parse response directly")

                # Try to parse JSON
                try:
                    scenes = json.loads(response_text)
                    print(f"✅ JSON parsed successfully - {len(scenes)} scenes")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing failed: {e}")
                    print(f"📄 Response text (full): {response_text}")

                    # Fallback: Create basic scenes from character description
                    print("🔄 Using fallback scene creation...")
                    scenes = []
                    for i in range(num_scenes):
                        scenes.append({
                            'prompt': f"Scene {i+1}: {shot_rotation[i]} cinematic shot of {character_description}, professional lighting and composition, {style} style with {pacing} pacing",
                            'shot_type': shot_rotation[i],
                            'duration': 8,
                            'resolution': '720p',
                            'aspect_ratio': '16:9'
                        })

            # Validate and set defaults
            for i, scene in enumerate(scenes):
                if 'prompt' not in scene:
                    raise ValueError(f"Scene {i+1} missing 'prompt' field")
                scene.setdefault('duration', 8)
                scene.setdefault('resolution', '720p')
                scene.setdefault('aspect_ratio', '16:9')
                scene.setdefault('shot_type', shot_rotation[i % len(shot_rotation)])

        print(f"✅ Generated {len(scenes)} scene(s)")

        # Return complete package
        return jsonify({
            'success': True,
            'concept': concept,
            'character_description': character_description,
            'character_data': character_data,
            'reference_images': reference_images,
            'scenes': scenes,
            'num_scenes': len(scenes),
            'style': style,
            'pacing': pacing,
            'message': f'🤖 AI generated complete storyboard: {len(reference_images)} reference images + {len(scenes)} scenes'
        })

    except Exception as e:
        print(f"❌ Error in auto_generate_complete_storyboard: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/storyboard/generate-from-concept', methods=['POST'])
def generate_storyboard_from_concept():
    """Generate complete storyboard from a high-level concept using Veo 3.1 best practices"""
    try:
        data = request.get_json()
        concept = data.get('concept', '')
        character_description = data.get('character_description', '')
        num_scenes = data.get('num_scenes', 5)
        style = data.get('style', 'cinematic')
        pacing = data.get('pacing', 'medium')

        if not concept:
            return jsonify({
                'success': False,
                'error': 'Concept description is required'
            }), 400

        # Note: style and pacing are passed directly to keep prompt concise

        # Veo 3.1 Best Practices System Instruction (Concise)
        shot_rotation = ['wide', 'medium', 'close-up'] * ((num_scenes // 3) + 1)

        # Add character description for consistency (Solution 3)
        character_section = ""
        if character_description:
            character_section = f"\n\nCHARACTER CONSISTENCY: Include these exact details in EVERY scene prompt: {character_description}"

        system_instruction = f"""Create {num_scenes} cinematic video scenes for: {concept}

Style: {style}. Pacing: {pacing}.{character_section}

Each scene formula: [Camera] + [Subject] + [Action] + [Context] + [Lighting/Mood]

Rotate shots: {', '.join([f"Scene {i+1}={shot_rotation[i]}" for i in range(num_scenes)])}

Guidelines:
- Specific camera movements (dolly, tracking, crane, aerial, POV)
- Detailed lighting (golden hour, dramatic shadows, soft diffused)
- One clear action per scene
- 50-150 words per prompt
- Ensure story continuity
{"- CRITICAL: Include the exact character description in every scene prompt" if character_description else ""}

Return JSON:
[{{"prompt": "...", "shot_type": "wide/medium/close-up", "duration": 8, "resolution": "720p", "aspect_ratio": "16:9"}}, ...]"""

        # Use Gemini to generate the storyboard
        if mock_mode:
            # Mock scenes for testing
            shot_types = ['wide', 'medium', 'close-up'] * ((num_scenes // 3) + 1)
            scenes = []
            for i in range(num_scenes):
                scenes.append({
                    'prompt': f"Scene {i+1}: Cinematic {shot_types[i]} shot with dramatic lighting and smooth camera movement, capturing the essence of the story concept with professional framing and composition.",
                    'shot_type': shot_types[i],
                    'duration': 8,
                    'resolution': '720p',
                    'aspect_ratio': '16:9'
                })
        else:
            try:
                import vertexai
                from vertexai.generative_models import GenerativeModel
                import json
                import re

                model = GenerativeModel("gemini-2.0-flash-exp")

                # Configure for JSON output
                generation_config = {
                    "temperature": 0.9,  # Higher creativity for varied scenes
                    "top_p": 0.95,
                    "max_output_tokens": 8192,
                }

                response = model.generate_content(
                    system_instruction,
                    generation_config=generation_config
                )

                # Parse JSON response
                response_text = response.text.strip()

                # Extract JSON from markdown code blocks if present
                json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)

                # Parse JSON
                scenes = json.loads(response_text)

                # Validate and ensure all required fields
                for i, scene in enumerate(scenes):
                    if 'prompt' not in scene:
                        raise ValueError(f"Scene {i+1} missing 'prompt' field")
                    # Set defaults for optional fields
                    scene.setdefault('duration', 8)
                    scene.setdefault('resolution', '720p')
                    scene.setdefault('aspect_ratio', '16:9')
                    scene.setdefault('shot_type', ['wide', 'medium', 'close-up'][i % 3])

            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                print(f"Response text: {response_text}")
                # Fallback: Create scenes from text
                scenes = []
                shot_types = ['wide', 'medium', 'close-up'] * ((num_scenes // 3) + 1)
                lines = [line.strip() for line in response_text.split('\n') if line.strip()]
                for i in range(min(num_scenes, len(lines))):
                    prompt = lines[i].lstrip('0123456789.-•) ').strip()
                    if prompt:
                        scenes.append({
                            'prompt': prompt,
                            'shot_type': shot_types[i],
                            'duration': 8,
                            'resolution': '720p',
                            'aspect_ratio': '16:9'
                        })

            except Exception as e:
                print(f"Error generating storyboard: {e}")
                # Generate fallback scenes based on concept
                shot_types = ['wide', 'medium', 'close-up'] * ((num_scenes // 3) + 1)
                camera_movements = ['Aerial drone shot', 'Tracking shot', 'Close-up', 'Dolly push', 'Crane shot', 'POV shot']
                lighting = ['golden hour sunlight', 'dramatic side lighting', 'soft diffused light', 'neon glow', 'natural daylight']

                scenes = []
                for i in range(num_scenes):
                    scenes.append({
                        'prompt': f"{camera_movements[i % len(camera_movements)]} capturing {concept}, {lighting[i % len(lighting)]}, cinematic composition with {shot_types[i]} framing, smooth camera movement, professional color grading",
                        'shot_type': shot_types[i],
                        'duration': 8,
                        'resolution': '720p',
                        'aspect_ratio': '16:9'
                    })

        return jsonify({
            'success': True,
            'scenes': scenes,
            'concept': concept,
            'num_scenes': len(scenes),
            'style': style,
            'pacing': pacing
        })

    except Exception as e:
        print(f"Error in generate_storyboard_from_concept: {e}")
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
