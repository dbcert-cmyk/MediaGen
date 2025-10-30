import os
import time
from typing import List, Optional
from PIL import Image
from io import BytesIO
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel, VideoGenerationModel


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
        negative_prompt: str = "",
        number_of_images: int = 1,
        aspect_ratio: str = "1:1",
        model: str = "imagen-3.0-generate-001",
        safety_filter_level: str = "block_some",
        person_generation: str = "allow_adult",
        language: str = "auto",
        output_mime_type: str = "image/png"
    ) -> List[Image.Image]:
        """
        Generate images using Vertex AI Imagen 3

        Args:
            prompt: Text description of the image to generate
            negative_prompt: Things to avoid in the generated image
            number_of_images: Number of images to generate (1-8)
            aspect_ratio: Aspect ratio (1:1, 9:16, 16:9, 4:3, 3:4)
            model: Model to use (imagen-3.0-generate-001, imagen-3.0-fast-generate-001)
            safety_filter_level: Safety filter level (block_some, block_few, block_most, block_fewest)
            person_generation: Person generation policy (allow_adult, allow_all, dont_allow)
            language: Language code (auto, en, es, fr, de, it, ja, ko, pt, hi, etc.)
            output_mime_type: Output format (image/png, image/jpeg)

        Returns:
            List of PIL Image objects
        """
        try:
            print(f"Generating {number_of_images} image(s) with Imagen 3")
            print(f"Model: {model}")
            print(f"Prompt: {prompt}")

            # Initialize the model
            image_model = ImageGenerationModel.from_pretrained(model)

            # Generate images
            response = image_model.generate_images(
                prompt=prompt,
                negative_prompt=negative_prompt if negative_prompt else None,
                number_of_images=number_of_images,
                aspect_ratio=aspect_ratio,
                safety_filter_level=safety_filter_level,
                person_generation=person_generation,
                language=language,
                output_mime_type=output_mime_type
            )

            # Convert to PIL Images
            images = []
            for idx, image in enumerate(response.images):
                # Get image bytes
                img_bytes = image._image_bytes

                # Convert to PIL Image
                pil_image = Image.open(BytesIO(img_bytes))
                images.append(pil_image)

                # Save locally for reference
                timestamp = int(time.time())
                file_ext = "png" if output_mime_type == "image/png" else "jpg"
                output_path = f"generated_media/image_{timestamp}_{idx}.{file_ext}"
                pil_image.save(output_path)
                print(f"Saved image to: {output_path}")

            return images

        except Exception as e:
            print(f"Error generating image: {str(e)}")
            raise

    def generate_video(
        self,
        prompt: str,
        model: str = "veo-3.1-generate-001",
        aspect_ratio: str = "16:9",
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate a video using Vertex AI Veo (Video Generation)

        Args:
            prompt: Text description of the video to generate
            model: Model to use (veo-3.1-generate-001 for Veo 3.1, veo-2.0-generate-001 for Veo 2, or veo-001 for Veo 1)
            aspect_ratio: Aspect ratio (16:9, 9:16, 1:1)
            output_path: Optional custom output path

        Returns:
            Path to the generated video file
        """
        try:
            print(f"Generating video with Veo")
            print(f"Model: {model}")
            print(f"Prompt: {prompt}")
            print(f"Aspect Ratio: {aspect_ratio}")

            # Initialize video generation model
            video_model = VideoGenerationModel.from_pretrained(model)

            # Generate video
            response = video_model.generate_video(
                prompt=prompt,
                aspect_ratio=aspect_ratio
            )

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
