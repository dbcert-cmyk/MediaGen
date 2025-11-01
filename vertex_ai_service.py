import os
import time
import base64
from typing import List, Optional
from PIL import Image
from io import BytesIO
import vertexai
try:
    from vertexai.preview.vision_models import VideoGenerationModel
except ImportError:
    # Fallback for newer SDK versions
    try:
        from vertexai.vision_models import VideoGenerationModel
    except ImportError:
        # If still not available, we'll define a placeholder
        VideoGenerationModel = None
from vertexai.generative_models import GenerativeModel, Part


class VertexAIMediaGenerator:
    """Service class for generating images and videos using Vertex AI"""

    def __init__(self, project_id: str, location: str = "us-central1"):
        """
        Initialize the Vertex AI Media Generator

        Args:
            project_id: Google Cloud project ID
            location: GCP location (default: us-central1)
        """
        self.project_id = project_id
        self.location = location

        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)

    def generate_image(
        self,
        prompt: str,
        number_of_images: int = 1,
        aspect_ratio: str = "1:1",
        model: str = "gemini-2.5-flash-image",
        temperature: float = 1.0,
        top_p: float = 0.95,
        top_k: int = 64,
        output_mime_type: str = "image/png",
        input_images: List[bytes] = None,
        safety_settings: dict = None
    ) -> List[Image.Image]:
        """
        Generate images using Vertex AI Gemini 2.5 Flash Image (Nano Banana)

        Args:
            prompt: Text description of the image to generate
            number_of_images: Number of images to generate (1-10)
            aspect_ratio: Aspect ratio (1:1, 3:2, 2:3, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9)
            model: Model to use (gemini-2.5-flash-image)
            temperature: Controls randomness (0.0-2.0, default 1.0). Higher = more creative
            top_p: Nucleus sampling parameter (0.0-1.0, default 0.95)
            top_k: Top-k sampling parameter (default 64)
            output_mime_type: Output format (image/png, image/jpeg)
            input_images: List of input image bytes (up to 3 images)
            safety_settings: Safety filter settings dict

        Returns:
            List of PIL Image objects
        """
        try:
            print(f"Generating {number_of_images} image(s) with Gemini 2.5 Flash Image (Nano Banana)")
            print(f"Model: {model}")
            print(f"Prompt: {prompt}")
            print(f"Aspect Ratio: {aspect_ratio}")
            print(f"Temperature: {temperature}, Top-P: {top_p}, Top-K: {top_k}")

            # Initialize the model
            image_model = GenerativeModel(model)

            # Build the content parts
            content_parts = []

            # Add input images if provided (up to 3)
            if input_images:
                for idx, img_bytes in enumerate(input_images[:3]):
                    content_parts.append(Part.from_data(img_bytes, mime_type="image/png"))
                print(f"📷 Using {len(input_images[:3])} input image(s)")

            # Add text prompt
            content_parts.append(prompt)

            # Configure generation parameters (minimal config for compatibility)
            generation_config = {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "candidate_count": number_of_images,
                "response_modalities": ["TEXT", "IMAGE"]
            }

            # Build request parameters
            generate_params = {
                "contents": content_parts,
                "generation_config": generation_config
            }

            # Add safety settings if provided
            if safety_settings:
                generate_params["safety_settings"] = safety_settings

            # Generate images
            # Note: aspect_ratio is not directly supported in newer SDK versions for Gemini
            # The model will generate images in a suitable aspect ratio based on the prompt
            response = image_model.generate_content(**generate_params)

            # Extract images from response
            images = []
            timestamp = int(time.time())

            for idx, candidate in enumerate(response.candidates):
                for part in candidate.content.parts:
                    # Check if this part contains image data
                    if hasattr(part, 'inline_data') and part.inline_data:
                        img_bytes = part.inline_data.data

                        # Convert to PIL Image
                        pil_image = Image.open(BytesIO(img_bytes))
                        images.append(pil_image)

                        # Save locally for reference
                        file_ext = "png" if output_mime_type == "image/png" else "jpg"
                        output_path = f"generated_media/image_{timestamp}_{idx}.{file_ext}"

                        # Ensure directory exists
                        os.makedirs("generated_media", exist_ok=True)

                        pil_image.save(output_path)
                        print(f"Saved image to: {output_path}")

            if not images:
                raise Exception("No images were generated in the response")

            return images

        except Exception as e:
            print(f"Error generating image: {str(e)}")
            raise

    def generate_video(
        self,
        prompt: str = "",
        model: str = "veo-3.1-generate-001",
        aspect_ratio: str = "16:9",
        duration_seconds: int = 8,
        resolution: str = "720p",
        compression_quality: str = "optimized",
        enhance_prompt: bool = True,
        generate_audio: bool = False,
        negative_prompt: str = "",
        person_generation: str = "allow_adult",
        sample_count: int = 1,
        seed: int = None,
        resize_mode: str = "pad",
        storage_uri: str = None,
        # Image/Video inputs
        image_bytes: bytes = None,
        image_path: str = None,
        last_frame_bytes: bytes = None,
        last_frame_path: str = None,
        video_bytes: bytes = None,
        video_path: str = None,
        reference_images: List[dict] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate a video using Vertex AI Veo (Video Generation)

        Args:
            prompt: Text description of the video to generate (required for text-to-video, optional with image input)
            model: Model to use (veo-3.1-generate-001, veo-2.0-generate-001, or veo-001)
            aspect_ratio: Aspect ratio (16:9, 9:16)
            duration_seconds: Duration in seconds (4, 6, or 8)
            resolution: Video resolution (720p, 1080p) - Veo 3 only
            compression_quality: Compression quality (optimized, lossless)
            enhance_prompt: Use Gemini to refine prompt (True/False)
            generate_audio: Generate audio for the video (True/False) - Veo 3 only
            negative_prompt: Things to avoid in the video
            person_generation: Person generation policy (allow_adult, dont_allow)
            sample_count: Number of videos to generate (1-4)
            seed: Seed for deterministic results (0-4294967295, None for random)
            resize_mode: How to resize input images (pad, crop) - Veo 3 image-to-video only
            storage_uri: Cloud Storage URI (gs://bucket/path) for output
            image_bytes: Image bytes for image-to-video
            image_path: Path to image file for image-to-video
            last_frame_bytes: Last frame image bytes
            last_frame_path: Path to last frame image file
            video_bytes: Video bytes for video extension
            video_path: Path to video file for video extension
            reference_images: List of reference images [{"bytes": b"...", "type": "asset"|"style"}]
            output_path: Optional custom output path

        Returns:
            Path to the generated video file
        """
        try:
            print(f"Generating video with Veo")
            print(f"Model: {model}")

            # Handle image input
            input_image = None
            if image_bytes:
                input_image = Image.open(BytesIO(image_bytes))
                print("📷 Using provided image for image-to-video")
            elif image_path:
                input_image = Image.open(image_path)
                print(f"📷 Using image from: {image_path}")

            # Handle last frame
            last_frame_image = None
            if last_frame_bytes:
                last_frame_image = Image.open(BytesIO(last_frame_bytes))
                print("🎞️  Using provided last frame")
            elif last_frame_path:
                last_frame_image = Image.open(last_frame_path)
                print(f"🎞️  Using last frame from: {last_frame_path}")

            if prompt:
                print(f"Prompt: {prompt}")
            print(f"Aspect Ratio: {aspect_ratio}")
            print(f"Duration: {duration_seconds}s")
            print(f"Resolution: {resolution}")

            # Initialize video generation model
            if VideoGenerationModel is None:
                raise ImportError(
                    "VideoGenerationModel is not available in your version of the Vertex AI SDK. "
                    "This may be due to SDK version incompatibility. "
                    "Please try: pip install google-cloud-aiplatform==1.38.0\n"
                    "Or use MOCK_MODE=true in your .env file for testing without GCP."
                )
            video_model = VideoGenerationModel.from_pretrained(model)

            # Build parameters dict
            generation_params = {
                "aspect_ratio": aspect_ratio
            }

            # Add prompt (required for text-to-video, optional for image-to-video)
            if prompt:
                generation_params["prompt"] = prompt

            # Add Veo 3 specific parameters
            if "veo-3" in model.lower() or "veo-2" in model.lower():
                generation_params["duration_seconds"] = duration_seconds
                generation_params["compression_quality"] = compression_quality
                generation_params["enhance_prompt"] = enhance_prompt
                generation_params["person_generation"] = person_generation
                generation_params["sample_count"] = sample_count

                if "veo-3" in model.lower():
                    generation_params["resolution"] = resolution
                    generation_params["generate_audio"] = generate_audio

                    # Veo 3 image-to-video specific
                    if input_image:
                        generation_params["resize_mode"] = resize_mode

                if negative_prompt:
                    generation_params["negative_prompt"] = negative_prompt

                if seed is not None:
                    generation_params["seed"] = seed

                if storage_uri:
                    generation_params["storage_uri"] = storage_uri

            # Add image input if provided
            if input_image:
                img_byte_arr = BytesIO()
                input_image.save(img_byte_arr, format='PNG')
                generation_params["image_bytes"] = img_byte_arr.getvalue()

            # Add last frame if provided
            if last_frame_image:
                last_frame_byte_arr = BytesIO()
                last_frame_image.save(last_frame_byte_arr, format='PNG')
                generation_params["last_frame_bytes"] = last_frame_byte_arr.getvalue()

            # Add reference images if provided
            if reference_images:
                generation_params["reference_images"] = reference_images
                print(f"🖼️  Using {len(reference_images)} reference image(s)")

            # Generate video
            response = video_model.generate_video(**generation_params)

            # Save video
            timestamp = int(time.time())
            if output_path is None:
                output_path = f"generated_media/video_{timestamp}.mp4"

            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path) or "generated_media", exist_ok=True)

            # Get video bytes and save
            video_bytes = response.video_bytes
            with open(output_path, 'wb') as f:
                f.write(video_bytes)

            print(f"Saved video to: {output_path}")
            return output_path

        except AttributeError as e:
            # Video generation may not be available in all regions/accounts
            print(f"Video generation not available: {str(e)}")
            raise Exception(
                "Video generation is currently in preview and may not be available "
                "in your project/region. Please check Vertex AI documentation for availability."
            )
        except Exception as e:
            print(f"Error generating video: {str(e)}")
            raise

    def generate_video_from_image(
        self,
        prompt: str,
        image: Image.Image,
        model: str = "veo-3.1-generate-001",
        aspect_ratio: str = "16:9",
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate a video from a base image using Vertex AI Veo

        Args:
            prompt: Text description for video generation
            image: Base PIL Image to animate
            model: Model to use (veo-3.1-generate-001 for Veo 3.1, veo-2.0-generate-001 for Veo 2)
            aspect_ratio: Aspect ratio (16:9, 9:16, 1:1)
            output_path: Optional custom output path

        Returns:
            Path to the generated video file
        """
        try:
            print(f"Generating video from image with Veo")
            print(f"Model: {model}")
            print(f"Prompt: {prompt}")

            # Initialize video generation model
            video_model = VideoGenerationModel.from_pretrained(model)

            # Convert PIL Image to bytes
            img_byte_arr = BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()

            # Generate video from image
            response = video_model.generate_video(
                prompt=prompt,
                image_bytes=img_bytes,
                aspect_ratio=aspect_ratio
            )

            # Save video
            timestamp = int(time.time())
            if output_path is None:
                output_path = f"generated_media/video_from_image_{timestamp}.mp4"

            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path) or "generated_media", exist_ok=True)

            # Get video bytes and save
            video_bytes = response.video_bytes
            with open(output_path, 'wb') as f:
                f.write(video_bytes)

            print(f"Saved video to: {output_path}")
            return output_path

        except Exception as e:
            print(f"Error generating video from image: {str(e)}")
            raise
