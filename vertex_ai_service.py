import os
import time
import base64
from typing import List, Optional
from PIL import Image
from io import BytesIO
import vertexai

# New Google GenAI SDK for video generation (Veo 3.1)
try:
    from google import genai
    from google.genai.types import GenerateVideosConfig, Image as GenAIImage
    print("✅ Google GenAI SDK imported (for Veo 3.1 video generation)")
    VIDEO_GEN_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Google GenAI SDK not available: {e}")
    print("   Install with: pip install google-genai")
    VIDEO_GEN_AVAILABLE = False

# Cloud Storage for video downloads
try:
    from google.cloud import storage
    print("✅ Google Cloud Storage SDK imported")
    STORAGE_AVAILABLE = True
except ImportError:
    print("⚠️  Google Cloud Storage SDK not available")
    STORAGE_AVAILABLE = False

# Try importing GenerativeModel from different locations (for image generation)
GenerativeModel = None
Part = None
try:
    from vertexai.generative_models import GenerativeModel, Part
    print("✅ GenerativeModel imported from vertexai.generative_models")
except ImportError as e:
    print(f"⚠️  Cannot import from vertexai.generative_models: {e}")
    try:
        from vertexai.preview.generative_models import GenerativeModel, Part
        print("✅ GenerativeModel imported from vertexai.preview.generative_models")
    except ImportError as e2:
        print(f"⚠️  Cannot import from vertexai.preview.generative_models: {e2}")
        GenerativeModel = None
        Part = None
        print("❌ GenerativeModel is not available")


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

            # Check if GenerativeModel is available
            if GenerativeModel is None or Part is None:
                raise ImportError(
                    "GenerativeModel is not available in your Vertex AI SDK version. "
                    "For SDK 1.38.0, image generation with Gemini may not be fully supported. "
                    "Please use MOCK_MODE=true in your .env file for testing, "
                    "or upgrade to a newer SDK version."
                )

            # Initialize the model
            image_model = GenerativeModel(model)

            # Gemini image generation only supports 1 candidate at a time
            # So we'll generate images in a loop if multiple are requested
            images = []
            timestamp = int(time.time())

            for img_num in range(number_of_images):
                print(f"Generating image {img_num + 1}/{number_of_images}...")

                # Build the content parts
                content_parts = []

                # Add input images if provided (up to 3)
                if input_images:
                    for idx, img_bytes in enumerate(input_images[:3]):
                        content_parts.append(Part.from_data(img_bytes, mime_type="image/png"))
                    if img_num == 0:  # Only print once
                        print(f"📷 Using {len(input_images[:3])} input image(s)")

                # Add text prompt
                content_parts.append(prompt)

                # Configure generation parameters (minimal config for compatibility)
                generation_config = {
                    "temperature": temperature,
                    "top_p": top_p,
                    "top_k": top_k,
                    "candidate_count": 1,  # Only 1 candidate supported for image generation
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

                # Generate image
                # Note: aspect_ratio is not directly supported in newer SDK versions for Gemini
                # The model will generate images in a suitable aspect ratio based on the prompt
                response = image_model.generate_content(**generate_params)

                # Extract images from response
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
                            output_path = f"generated_media/image_{timestamp}_{img_num}.{file_ext}"

                            # Ensure directory exists
                            os.makedirs("generated_media", exist_ok=True)

                            pil_image.save(output_path)
                            print(f"💾 Saved image to: {output_path}")

            if not images:
                raise Exception("No images were generated in the response")

            return images

        except Exception as e:
            print(f"Error generating image: {str(e)}")
            raise

    def generate_video(
        self,
        prompt: str = "",
        model: str = "veo-3.1-generate-preview",
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
        Generate a video using Vertex AI Veo (Video Generation) via Google GenAI SDK

        Args:
            prompt: Text description of the video to generate (required for text-to-video, optional with image input)
            model: Model to use (veo-3.1-generate-preview, veo-3.1-fast-generate-preview)
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
            print(f"🎬 Generating video with Veo (New GenAI SDK)")
            print(f"Model: {model}")

            # Check if video generation is available
            if not VIDEO_GEN_AVAILABLE:
                raise ImportError(
                    "Google GenAI SDK is not available. "
                    "Install with: pip install google-genai\n"
                    "Or use MOCK_MODE=true in your .env file for testing without GCP."
                )

            if not STORAGE_AVAILABLE:
                raise ImportError(
                    "Google Cloud Storage SDK is not available. "
                    "Install with: pip install google-cloud-storage"
                )

            # Set up environment variables for Vertex AI
            os.environ['GOOGLE_CLOUD_PROJECT'] = self.project_id
            os.environ['GOOGLE_CLOUD_LOCATION'] = 'global'  # Veo requires 'global' location
            os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'True'

            # Initialize GenAI client
            client = genai.Client()

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

            # Create temporary Cloud Storage path for output
            timestamp = int(time.time())
            bucket_name = os.environ.get('GCS_BUCKET_NAME', f"{self.project_id}-mediagen")
            if not storage_uri:
                storage_uri = f"gs://{bucket_name}/generated_videos/video_{timestamp}/"

            print(f"Output GCS URI: {storage_uri}")

            # Build generation config with all supported parameters
            config_params = {
                "aspect_ratio": aspect_ratio,
                "output_gcs_uri": storage_uri,
                "number_of_videos": sample_count,  # Key parameter for multiple videos!
            }

            # Add optional parameters for Veo 3.1
            if duration_seconds:
                config_params["duration_seconds"] = duration_seconds

            if resolution:
                config_params["resolution"] = resolution

            if enhance_prompt is not None:
                config_params["enhance_prompt"] = enhance_prompt

            if person_generation:
                config_params["person_generation"] = person_generation

            if negative_prompt:
                config_params["negative_prompt"] = negative_prompt

            # Add last frame to config if provided (for first+last frame video generation)
            if last_frame_image:
                # Convert PIL Image to bytes
                last_frame_byte_arr = BytesIO()
                last_frame_image.save(last_frame_byte_arr, format='PNG')
                last_frame_img_bytes = last_frame_byte_arr.getvalue()
                config_params["last_frame"] = GenAIImage(
                    image_bytes=last_frame_img_bytes,
                    mime_type="image/png"
                )
                print("🎞️  Added last frame to config")

            # Add reference images to config (Veo 3.1 "Ingredients to Video" feature)
            if reference_images and len(reference_images) > 0:
                ref_image_list = []
                for i, ref_img in enumerate(reference_images[:3]):  # Max 3 reference images
                    ref_bytes = ref_img.get('bytes')
                    ref_type = ref_img.get('type', 'asset')  # 'asset' or 'style'

                    if ref_bytes:
                        # Convert bytes to PIL Image to ensure proper format
                        ref_pil_image = Image.open(BytesIO(ref_bytes))
                        ref_byte_arr = BytesIO()
                        ref_pil_image.save(ref_byte_arr, format='PNG')
                        ref_image_bytes = ref_byte_arr.getvalue()

                        # Each reference image must be a dict with 'image' and 'referenceType' fields
                        ref_image_obj = {
                            "image": GenAIImage(
                                image_bytes=ref_image_bytes,
                                mime_type="image/png"
                            ),
                            "referenceType": ref_type.upper()  # Must be uppercase: ASSET or STYLE
                        }

                        ref_image_list.append(ref_image_obj)
                        print(f"🎭 Added reference image {i+1} (referenceType: {ref_type.upper()}) to config for character consistency")

                if ref_image_list:
                    config_params["reference_images"] = ref_image_list
                    print(f"✅ {len(ref_image_list)} reference image(s) added to GenerateVideosConfig")

            print(f"📊 Config: {sample_count} video(s), {duration_seconds}s duration, {resolution} resolution")

            generation_config = GenerateVideosConfig(**config_params)

            # Build request parameters
            request_params = {
                "model": model,
                "config": generation_config
            }

            # Add prompt if provided
            if prompt:
                request_params["prompt"] = prompt

            # Add image if provided (for image-to-video - first frame)
            if input_image:
                # Convert PIL Image to bytes
                img_byte_arr = BytesIO()
                input_image.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()
                request_params["image"] = GenAIImage(
                    image_bytes=img_bytes,
                    mime_type="image/png"
                )
                print("📷 Added first frame image to request")

            # Generate video (async operation)
            print("⏳ Starting video generation (this may take 1-3 minutes)...")
            operation = client.models.generate_videos(**request_params)

            # Poll for completion
            poll_count = 0
            max_polls = 60  # 15 minutes max (60 * 15 seconds)
            while not operation.done:
                poll_count += 1
                if poll_count > max_polls:
                    raise TimeoutError("Video generation timed out after 15 minutes")

                time.sleep(15)  # Poll every 15 seconds
                operation = client.operations.get(operation)
                print(f"⏳ Polling... ({poll_count * 15}s elapsed)")

            # Check if generation succeeded
            if not operation.response:
                raise Exception("Video generation failed - no response from API")

            # Get all video URIs from response
            result = operation.result
            if not result.generated_videos or len(result.generated_videos) == 0:
                raise Exception("No videos were generated")

            print(f"✅ Generated {len(result.generated_videos)} video(s)")

            # Download all videos from Cloud Storage
            local_paths = []
            for idx, generated_video in enumerate(result.generated_videos):
                video_gcs_uri = generated_video.video.uri
                print(f"⬇️  Downloading video {idx + 1}/{len(result.generated_videos)} from Cloud Storage...")

                # Create unique output path for each video
                if output_path and len(result.generated_videos) == 1:
                    video_output_path = output_path
                else:
                    video_output_path = f"generated_media/video_{timestamp}_{idx}.mp4"

                local_path = self._download_from_gcs(video_gcs_uri, video_output_path, timestamp)
                local_paths.append(local_path)
                print(f"💾 Saved video to: {local_path}")

            # Return single path for backwards compatibility if only 1 video, otherwise return first path
            # (app.py will need to be updated to handle multiple videos properly)
            return local_paths[0] if len(local_paths) == 1 else local_paths

        except Exception as e:
            print(f"❌ Error generating video: {str(e)}")
            raise

    def _download_from_gcs(self, gcs_uri: str, output_path: Optional[str], timestamp: int) -> str:
        """Download a file from Google Cloud Storage to local path"""
        try:
            # Parse GCS URI (gs://bucket/path)
            if not gcs_uri.startswith('gs://'):
                raise ValueError(f"Invalid GCS URI: {gcs_uri}")

            uri_parts = gcs_uri[5:].split('/', 1)  # Remove 'gs://' and split
            bucket_name = uri_parts[0]
            blob_name = uri_parts[1] if len(uri_parts) > 1 else ''

            # Initialize storage client
            storage_client = storage.Client(project=self.project_id)
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)

            # Determine local output path
            if output_path is None:
                output_path = f"generated_media/video_{timestamp}.mp4"

            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path) or "generated_media", exist_ok=True)

            # Download the file
            blob.download_to_filename(output_path)

            return output_path

        except Exception as e:
            print(f"❌ Error downloading from GCS: {str(e)}")
            raise

    def generate_video_from_image(
        self,
        prompt: str,
        image: Image.Image,
        model: str = "veo-3.1-generate-preview",
        aspect_ratio: str = "16:9",
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate a video from a base image using Vertex AI Veo

        Args:
            prompt: Text description for video generation
            image: Base PIL Image to animate
            model: Model to use (veo-3.1-generate-preview, veo-3.1-fast-generate-preview)
            aspect_ratio: Aspect ratio (16:9, 9:16)
            output_path: Optional custom output path

        Returns:
            Path to the generated video file
        """
        # Use the main generate_video method with image input
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()

        return self.generate_video(
            prompt=prompt,
            model=model,
            aspect_ratio=aspect_ratio,
            image_bytes=img_bytes,
            output_path=output_path
        )
