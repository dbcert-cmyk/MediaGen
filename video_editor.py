"""
Video Editing Module for MediaGen
Provides video editing capabilities using FFmpeg
"""

import os
import time
import subprocess
from typing import Optional, List, Tuple
from PIL import Image, ImageDraw, ImageFont
import random


class VideoEditor:
    """Video editing operations using FFmpeg"""

    def __init__(self, mock_mode: bool = False):
        """
        Initialize Video Editor

        Args:
            mock_mode: If True, use mock operations instead of FFmpeg
        """
        self.mock_mode = mock_mode

        if not mock_mode:
            # Check if FFmpeg is installed
            try:
                subprocess.run(['ffmpeg', '-version'],
                             capture_output=True,
                             check=True)
                print("✅ FFmpeg detected and ready")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("⚠️  FFmpeg not found - install with: sudo apt-get install ffmpeg")
                print("⚠️  Falling back to MOCK MODE for video editing")
                self.mock_mode = True
        else:
            print("🎭 MOCK MODE: Video editing will use placeholders")

    def trim_video(
        self,
        input_path: str,
        start_time: float,
        end_time: float,
        output_path: Optional[str] = None
    ) -> str:
        """
        Trim/cut a video to specified time range

        Args:
            input_path: Path to input video
            start_time: Start time in seconds
            end_time: End time in seconds
            output_path: Optional output path

        Returns:
            Path to trimmed video
        """
        if output_path is None:
            timestamp = int(time.time())
            output_path = f"generated_media/trimmed_video_{timestamp}.mp4"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if self.mock_mode:
            return self._mock_trim_video(input_path, start_time, end_time, output_path)

        # Calculate duration
        duration = end_time - start_time

        # FFmpeg command to trim video (using re-encoding for reliability)
        cmd = [
            'ffmpeg',
            '-ss', str(start_time),  # Seek to start time
            '-i', input_path,
            '-t', str(duration),  # Duration to extract
            '-c:v', 'libx264',  # Re-encode video (more reliable than copy)
            '-c:a', 'aac',  # Re-encode audio
            '-strict', 'experimental',
            '-y',  # Overwrite output file
            output_path
        ]

        print(f"✂️  Trimming video: {start_time}s to {end_time}s")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"💾 Saved trimmed video to: {output_path}")
        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg error: {e.stderr}")
            raise Exception(f"FFmpeg failed to trim video: {e.stderr}")

        # Verify output file exists
        if not os.path.exists(output_path):
            raise Exception(f"Trimmed video was not created at {output_path}")

        return output_path

    def add_text_overlay(
        self,
        input_path: str,
        text: str,
        position: str = "bottom",
        font_size: int = 24,
        font_color: str = "white",
        start_time: float = 0,
        duration: Optional[float] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        Add text overlay to video

        Args:
            input_path: Path to input video
            text: Text to overlay
            position: Position (top, bottom, center)
            font_size: Font size in pixels
            font_color: Font color (white, black, red, etc.)
            start_time: When to show text (seconds)
            duration: How long to show text (None = entire video)
            output_path: Optional output path

        Returns:
            Path to video with text overlay
        """
        if output_path is None:
            timestamp = int(time.time())
            output_path = f"generated_media/text_overlay_{timestamp}.mp4"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if self.mock_mode:
            return self._mock_add_text_overlay(input_path, text, output_path)

        # Position mapping
        position_map = {
            "top": "x=(w-text_w)/2:y=30",
            "center": "x=(w-text_w)/2:y=(h-text_h)/2",
            "bottom": "x=(w-text_w)/2:y=h-text_h-30"
        }
        pos = position_map.get(position, position_map["bottom"])

        # Build drawtext filter
        drawtext = f"drawtext=text='{text}':fontsize={font_size}:fontcolor={font_color}:{pos}"

        # Add timing if duration is specified
        if duration is not None:
            end_time = start_time + duration
            drawtext += f":enable='between(t,{start_time},{end_time})'"

        # FFmpeg command
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vf', drawtext,
            '-codec:a', 'copy',
            '-y',
            output_path
        ]

        print(f"📝 Adding text overlay: '{text}' at {position}")
        subprocess.run(cmd, capture_output=True, check=True)
        print(f"💾 Saved video with text to: {output_path}")

        return output_path

    def combine_videos(
        self,
        video_paths: List[str],
        output_path: Optional[str] = None
    ) -> str:
        """
        Combine multiple videos into one

        Args:
            video_paths: List of video file paths to combine
            output_path: Optional output path

        Returns:
            Path to combined video
        """
        if output_path is None:
            timestamp = int(time.time())
            output_path = f"generated_media/combined_video_{timestamp}.mp4"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if self.mock_mode:
            return self._mock_combine_videos(video_paths, output_path)

        # Create a temporary file list for FFmpeg concat
        concat_file = f"generated_media/concat_list_{int(time.time())}.txt"
        with open(concat_file, 'w') as f:
            for video_path in video_paths:
                # Convert to absolute path
                abs_path = os.path.abspath(video_path)
                f.write(f"file '{abs_path}'\n")

        # FFmpeg concat command
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',
            '-y',
            output_path
        ]

        print(f"🔗 Combining {len(video_paths)} videos")
        subprocess.run(cmd, capture_output=True, check=True)

        # Clean up concat file
        os.remove(concat_file)

        print(f"💾 Saved combined video to: {output_path}")
        return output_path

    def change_speed(
        self,
        input_path: str,
        speed: float = 1.0,
        output_path: Optional[str] = None
    ) -> str:
        """
        Change video playback speed

        Args:
            input_path: Path to input video
            speed: Speed multiplier (0.5 = half speed, 2.0 = double speed)
            output_path: Optional output path

        Returns:
            Path to speed-adjusted video
        """
        if output_path is None:
            timestamp = int(time.time())
            output_path = f"generated_media/speed_{speed}x_{timestamp}.mp4"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if self.mock_mode:
            return self._mock_change_speed(input_path, speed, output_path)

        # Calculate PTS (presentation timestamp) multiplier
        # Inverse of speed (0.5x speed = 2.0 PTS, 2x speed = 0.5 PTS)
        pts_multiplier = 1.0 / speed

        # FFmpeg command for speed change
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-filter:v', f'setpts={pts_multiplier}*PTS',
            '-filter:a', f'atempo={speed}',  # Adjust audio speed
            '-y',
            output_path
        ]

        print(f"⚡ Changing video speed to {speed}x")
        subprocess.run(cmd, capture_output=True, check=True)
        print(f"💾 Saved speed-adjusted video to: {output_path}")

        return output_path

    # Mock mode implementations
    def _mock_trim_video(self, input_path: str, start_time: float, end_time: float, output_path: str) -> str:
        """Mock implementation of trim video"""
        print(f"🎭 MOCK: Trimming video from {start_time}s to {end_time}s")
        time.sleep(1)

        # Create a placeholder video frame
        self._create_mock_video_frame(
            output_path,
            f"Trimmed Video\n{start_time}s - {end_time}s\nDuration: {end_time - start_time}s"
        )

        return output_path

    def _mock_add_text_overlay(self, input_path: str, text: str, output_path: str) -> str:
        """Mock implementation of text overlay"""
        print(f"🎭 MOCK: Adding text overlay: '{text}'")
        time.sleep(1)

        self._create_mock_video_frame(
            output_path,
            f"Video with Text Overlay\n\n'{text}'"
        )

        return output_path

    def _mock_combine_videos(self, video_paths: List[str], output_path: str) -> str:
        """Mock implementation of combine videos"""
        print(f"🎭 MOCK: Combining {len(video_paths)} videos")
        time.sleep(1)

        self._create_mock_video_frame(
            output_path,
            f"Combined Video\n{len(video_paths)} clips merged"
        )

        return output_path

    def _mock_change_speed(self, input_path: str, speed: float, output_path: str) -> str:
        """Mock implementation of speed change"""
        print(f"🎭 MOCK: Changing speed to {speed}x")
        time.sleep(1)

        self._create_mock_video_frame(
            output_path,
            f"Speed Adjusted Video\n{speed}x speed"
        )

        return output_path

    def _create_mock_video_frame(self, output_path: str, text: str):
        """Create a mock video frame as a placeholder"""
        # Try to create with opencv if available
        try:
            import cv2
            import numpy as np

            size = (768, 432)
            fps = 24
            duration = 3

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, size)

            for frame_num in range(duration * fps):
                frame = np.zeros((size[1], size[0], 3), dtype=np.uint8)

                # Gradient background
                for y in range(size[1]):
                    ratio = y / size[1]
                    r = int(80 + 100 * ratio)
                    g = int(120 - 50 * ratio)
                    b = int(180 - 80 * ratio)
                    frame[y, :] = [b, g, r]

                # Add text
                font = cv2.FONT_HERSHEY_SIMPLEX
                y_pos = 60
                for line in text.split('\n'):
                    cv2.putText(frame, line, (30, y_pos),
                               font, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
                    y_pos += 50

                cv2.putText(frame, "MOCK MODE - Edited Video", (30, size[1] - 30),
                           font, 0.6, (200, 200, 200), 1, cv2.LINE_AA)

                out.write(frame)

            out.release()
            print(f"💾 Saved mock video to: {output_path}")

        except ImportError:
            # Fallback to image if opencv not available
            print("⚠️  OpenCV not installed - creating static image placeholder")
            output_path = output_path.replace('.mp4', '.png')

            img = Image.new('RGB', (768, 432))
            draw = ImageDraw.Draw(img)

            # Gradient
            for y in range(432):
                ratio = y / 432
                r = int(80 + 100 * ratio)
                g = int(120 - 50 * ratio)
                b = int(180 - 80 * ratio)
                draw.line([(0, y), (768, y)], fill=(r, g, b))

            # Text
            font = ImageFont.load_default()
            y_pos = 60
            for line in text.split('\n'):
                draw.text((30, y_pos), line, fill='white', font=font)
                y_pos += 30

            draw.text((30, 400), "MOCK MODE - Edited Video", fill='lightgray', font=font)
            img.save(output_path)
            print(f"💾 Saved mock image to: {output_path}")
