import time
import os
from typing import List
from PIL import Image, ImageDraw, ImageFont
import random


class MockMediaGenerator:
    """Mock service for testing without GCP credentials - generates placeholder media"""

    def __init__(self, project_id: str = "mock-project", location: str = "mock-location"):
        """
        Initialize the Mock Media Generator

        Args:
            project_id: Placeholder project ID
            location: Placeholder location
        """
        self.project_id = project_id
        self.location = location
        print("🎭 MOCK MODE: Using placeholder media generation (no GCP charges)")

    def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        number_of_images: int = 1,
        aspect_ratio: str = "1:1",
        **kwargs
    ) -> List[Image.Image]:
        """
        Generate mock images with placeholder content

        Args:
            prompt: Text description (will be displayed on image)
            negative_prompt: Not used in mock mode
            number_of_images: Number of images to generate
            aspect_ratio: Aspect ratio for images

        Returns:
            List of PIL Image objects with placeholder content
        """
        print(f"🎭 MOCK: Generating {number_of_images} placeholder image(s)")
        print(f"📝 Prompt: {prompt}")

        # Simulate API delay
        time.sleep(1)

        # Parse aspect ratio
        aspect_map = {
            "1:1": (512, 512),
            "16:9": (768, 432),
            "9:16": (432, 768),
            "4:3": (640, 480),
            "3:4": (480, 640)
        }
        size = aspect_map.get(aspect_ratio, (512, 512))

        images = []
        for i in range(number_of_images):
            # Create a colorful gradient background
            img = Image.new('RGB', size, color='white')
            draw = ImageDraw.Draw(img)

            # Create gradient background with random colors
            r1, g1, b1 = random.randint(50, 150), random.randint(100, 200), random.randint(150, 255)
            r2, g2, b2 = random.randint(100, 200), random.randint(50, 150), random.randint(100, 200)

            for y in range(size[1]):
                ratio = y / size[1]
                r = int(r1 * (1 - ratio) + r2 * ratio)
                g = int(g1 * (1 - ratio) + g2 * ratio)
                b = int(b1 * (1 - ratio) + b2 * ratio)
                draw.line([(0, y), (size[0], y)], fill=(r, g, b))

            # Add decorative elements
            for _ in range(10):
                x = random.randint(0, size[0])
                y = random.randint(0, size[1])
                r = random.randint(10, 50)
                color = (
                    random.randint(100, 255),
                    random.randint(100, 255),
                    random.randint(100, 255),
                    100
                )
                draw.ellipse([x-r, y-r, x+r, y+r], fill=color)

            # Add text overlay
            try:
                # Try to use a default font, fallback to basic if not available
                font_size = max(16, size[0] // 25)
                font = ImageFont.load_default()
            except:
                font = None

            # Add "MOCK MODE" watermark
            draw.rectangle([(10, 10), (size[0]-10, 50)], fill=(0, 0, 0, 180))
            draw.text((20, 20), "🎭 MOCK MODE - Demo Image", fill='white', font=font)

            # Add prompt text
            prompt_text = prompt[:60] + "..." if len(prompt) > 60 else prompt
            text_y = size[1] - 80
            draw.rectangle([(10, text_y), (size[0]-10, size[1]-10)], fill=(0, 0, 0, 200))

            # Word wrap the prompt
            words = prompt_text.split()
            lines = []
            current_line = []
            for word in words:
                current_line.append(word)
                if len(' '.join(current_line)) > 40:
                    lines.append(' '.join(current_line[:-1]))
                    current_line = [word]
            if current_line:
                lines.append(' '.join(current_line))

            for idx, line in enumerate(lines[:2]):  # Max 2 lines
                draw.text((20, text_y + 10 + idx * 25), line, fill='white', font=font)

            # Add image number
            draw.text((20, text_y + 50), f"Image {i+1}/{number_of_images}", fill='lightgray', font=font)

            images.append(img)

            # Save locally for reference
            timestamp = int(time.time())
            output_path = f"generated_media/mock_image_{timestamp}_{i}.png"
            os.makedirs('generated_media', exist_ok=True)
            img.save(output_path)
            print(f"💾 Saved mock image to: {output_path}")

        return images

    def generate_video(
        self,
        prompt: str,
        duration: int = 5,
        output_path: str = None
    ) -> str:
        """
        Generate a mock video (creates a simple image sequence)

        Args:
            prompt: Text description
            duration: Duration in seconds
            output_path: Optional custom output path

        Returns:
            Path to the generated video file
        """
        print(f"🎭 MOCK: Generating placeholder video")
        print(f"📝 Prompt: {prompt}")
        print(f"⏱️  Duration: {duration}s")

        # Simulate longer processing time for video
        time.sleep(2)

        # Create a simple animated placeholder
        # In mock mode, we'll create a video file with a static image
        # For a real mock video, you'd need opencv-python, but we'll keep dependencies minimal

        timestamp = int(time.time())
        if output_path is None:
            output_path = f"generated_media/mock_video_{timestamp}.mp4"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Create a mock video file by generating frames and creating a simple MP4
        # Since we want to avoid heavy dependencies, we'll create a minimal placeholder
        try:
            # Try to create a simple video with opencv if available
            import cv2
            import numpy as np

            # Video settings
            fps = 24
            size = (768, 432)  # 16:9 aspect ratio
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, size)

            # Generate frames
            total_frames = duration * fps
            for frame_num in range(total_frames):
                # Create frame with gradient
                frame = np.zeros((size[1], size[0], 3), dtype=np.uint8)

                # Animated gradient
                ratio = frame_num / total_frames
                r1 = int(100 + 100 * ratio)
                g1 = int(150 - 50 * ratio)
                b1 = int(200 - 100 * ratio)

                for y in range(size[1]):
                    y_ratio = y / size[1]
                    r = int(r1 * (1 - y_ratio) + 50 * y_ratio)
                    g = int(g1 * (1 - y_ratio) + 100 * y_ratio)
                    b = int(b1 * (1 - y_ratio) + 200 * y_ratio)
                    frame[y, :] = [b, g, r]  # OpenCV uses BGR

                # Add text
                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(frame, "MOCK MODE - Demo Video", (20, 40),
                           font, 1, (255, 255, 255), 2, cv2.LINE_AA)

                prompt_text = prompt[:50] + "..." if len(prompt) > 50 else prompt
                cv2.putText(frame, prompt_text, (20, size[1] - 40),
                           font, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

                cv2.putText(frame, f"Frame {frame_num}/{total_frames}", (20, size[1] - 10),
                           font, 0.5, (200, 200, 200), 1, cv2.LINE_AA)

                out.write(frame)

            out.release()
            print(f"💾 Saved mock video to: {output_path}")

        except ImportError:
            # If opencv is not available, create a static image as fallback
            print("⚠️  OpenCV not installed - creating static image placeholder")

            # Generate a single frame as PNG
            size = (768, 432)
            img = Image.new('RGB', size)
            draw = ImageDraw.Draw(img)

            # Gradient background
            for y in range(size[1]):
                ratio = y / size[1]
                r = int(150 * (1 - ratio) + 50 * ratio)
                g = int(100 * (1 - ratio) + 150 * ratio)
                b = int(200 * (1 - ratio) + 100 * ratio)
                draw.line([(0, y), (size[0], y)], fill=(r, g, b))

            # Text
            font = ImageFont.load_default()
            draw.text((20, 20), "🎭 MOCK MODE - Video Placeholder", fill='white', font=font)
            draw.text((20, size[1] - 50), prompt[:50], fill='white', font=font)
            draw.text((20, size[1] - 20),
                     "Install opencv-python for animated mock videos",
                     fill='lightgray', font=font)

            # Save as PNG (change extension)
            output_path = output_path.replace('.mp4', '.png')
            img.save(output_path)
            print(f"💾 Saved mock video placeholder to: {output_path}")

        return output_path

    def generate_video_from_image(
        self,
        prompt: str,
        image: Image.Image,
        output_path: str = None
    ) -> str:
        """
        Mock version of video generation from image

        Args:
            prompt: Text description
            image: Base image
            output_path: Optional custom output path

        Returns:
            Path to the generated video file
        """
        print(f"🎭 MOCK: Generating placeholder video from image")
        return self.generate_video(prompt, duration=5, output_path=output_path)
