"""
Storyboard Mode for MediaGen
Create multi-scene videos by chaining Veo generations together
"""

import os
import json
import time
from typing import List, Dict, Optional
from video_editor import VideoEditor


class Scene:
    """Represents a single scene in a storyboard"""

    def __init__(self, scene_id: str, prompt: str, duration: int = 8, **kwargs):
        """
        Initialize a scene

        Args:
            scene_id: Unique identifier for this scene
            prompt: Text prompt for video generation
            duration: Duration in seconds (4, 6, or 8)
            **kwargs: Additional Veo parameters (resolution, etc.)
        """
        self.id = scene_id
        self.prompt = prompt
        self.duration = duration
        self.resolution = kwargs.get('resolution', '720p')
        self.aspect_ratio = kwargs.get('aspect_ratio', '16:9')
        self.video_path = None  # Set after generation
        self.video_data = None  # Base64 encoded video
        self.generated = False
        self.timestamp = int(time.time())

    def to_dict(self) -> dict:
        """Convert scene to dictionary"""
        return {
            'id': self.id,
            'prompt': self.prompt,
            'duration': self.duration,
            'resolution': self.resolution,
            'aspect_ratio': self.aspect_ratio,
            'video_path': self.video_path,
            'generated': self.generated,
            'timestamp': self.timestamp
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Scene':
        """Create scene from dictionary"""
        scene = cls(
            scene_id=data['id'],
            prompt=data['prompt'],
            duration=data['duration'],
            resolution=data.get('resolution', '720p'),
            aspect_ratio=data.get('aspect_ratio', '16:9')
        )
        scene.video_path = data.get('video_path')
        scene.generated = data.get('generated', False)
        scene.timestamp = data.get('timestamp', int(time.time()))
        return scene


class Storyboard:
    """Manages a collection of scenes"""

    def __init__(self, storyboard_id: str = None, title: str = "Untitled Storyboard"):
        """
        Initialize storyboard

        Args:
            storyboard_id: Unique identifier
            title: Storyboard title
        """
        self.id = storyboard_id or f"storyboard_{int(time.time())}"
        self.title = title
        self.scenes: List[Scene] = []
        self.created_at = int(time.time())
        self.updated_at = int(time.time())

    def add_scene(self, scene: Scene) -> None:
        """Add a scene to the storyboard"""
        self.scenes.append(scene)
        self.updated_at = int(time.time())

    def remove_scene(self, scene_id: str) -> bool:
        """Remove a scene by ID"""
        original_length = len(self.scenes)
        self.scenes = [s for s in self.scenes if s.id != scene_id]
        self.updated_at = int(time.time())
        return len(self.scenes) < original_length

    def reorder_scenes(self, scene_ids: List[str]) -> None:
        """Reorder scenes based on provided ID list"""
        scene_map = {s.id: s for s in self.scenes}
        self.scenes = [scene_map[sid] for sid in scene_ids if sid in scene_map]
        self.updated_at = int(time.time())

    def get_total_duration(self) -> int:
        """Get total duration of all scenes in seconds"""
        return sum(scene.duration for scene in self.scenes)

    def get_total_cost(self) -> float:
        """Estimate total cost for all scenes (at $0.40/second)"""
        return self.get_total_duration() * 0.40

    def get_scene(self, scene_id: str) -> Optional[Scene]:
        """Get a scene by ID"""
        for scene in self.scenes:
            if scene.id == scene_id:
                return scene
        return None

    def to_dict(self) -> dict:
        """Convert storyboard to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'scenes': [scene.to_dict() for scene in self.scenes],
            'total_duration': self.get_total_duration(),
            'total_cost': self.get_total_cost(),
            'scene_count': len(self.scenes),
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Storyboard':
        """Create storyboard from dictionary"""
        storyboard = cls(
            storyboard_id=data['id'],
            title=data['title']
        )
        storyboard.scenes = [Scene.from_dict(s) for s in data.get('scenes', [])]
        storyboard.created_at = data.get('created_at', int(time.time()))
        storyboard.updated_at = data.get('updated_at', int(time.time()))
        return storyboard

    def save(self, directory: str = "storyboards") -> str:
        """Save storyboard to JSON file"""
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, f"{self.id}.json")

        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

        return filepath

    @classmethod
    def load(cls, storyboard_id: str, directory: str = "storyboards") -> Optional['Storyboard']:
        """Load storyboard from JSON file"""
        filepath = os.path.join(directory, f"{storyboard_id}.json")

        if not os.path.exists(filepath):
            return None

        with open(filepath, 'r') as f:
            data = json.load(f)

        return cls.from_dict(data)


class StoryboardRenderer:
    """Renders storyboard scenes into final video"""

    def __init__(self, mock_mode: bool = False):
        """
        Initialize renderer

        Args:
            mock_mode: Use mock mode for testing
        """
        self.mock_mode = mock_mode
        self.video_editor = VideoEditor(mock_mode=mock_mode)

    def combine_scenes(
        self,
        storyboard: Storyboard,
        output_path: Optional[str] = None
    ) -> str:
        """
        Combine all generated scenes into final video

        Args:
            storyboard: Storyboard with generated scenes
            output_path: Optional output path

        Returns:
            Path to combined video
        """
        if output_path is None:
            timestamp = int(time.time())
            output_path = f"generated_media/storyboard_{storyboard.id}_{timestamp}.mp4"

        # Collect video paths from generated scenes
        video_paths = []
        for scene in storyboard.scenes:
            if scene.generated and scene.video_path:
                video_paths.append(scene.video_path)

        if not video_paths:
            raise ValueError("No generated scenes to combine")

        if len(video_paths) == 1:
            # Only one scene, just copy it
            import shutil
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            shutil.copy(video_paths[0], output_path)
            return output_path

        # Combine multiple videos
        print(f"🎬 Combining {len(video_paths)} scenes into storyboard...")
        combined_path = self.video_editor.combine_videos(video_paths, output_path)
        print(f"✅ Storyboard complete: {combined_path}")

        return combined_path


# Utility functions
def create_scene(prompt: str, duration: int = 8, **kwargs) -> Scene:
    """Helper to create a scene"""
    scene_id = f"scene_{int(time.time() * 1000)}"
    return Scene(scene_id, prompt, duration, **kwargs)


def estimate_storyboard_cost(scenes: List[Scene]) -> dict:
    """Estimate cost for a list of scenes"""
    total_duration = sum(s.duration for s in scenes)
    total_cost = total_duration * 0.40  # $0.40 per second

    return {
        'scene_count': len(scenes),
        'total_duration': total_duration,
        'total_cost': round(total_cost, 2),
        'cost_per_scene': [round(s.duration * 0.40, 2) for s in scenes]
    }


if __name__ == "__main__":
    # Test storyboard system
    print("=" * 60)
    print("Storyboard Mode - Test")
    print("=" * 60)

    # Create a storyboard
    sb = Storyboard(title="My First Short Film")

    # Add scenes
    scene1 = create_scene("A sunrise over mountains", duration=4)
    scene2 = create_scene("A hiker walking through a forest", duration=6)
    scene3 = create_scene("Close-up of a campfire at night", duration=8)

    sb.add_scene(scene1)
    sb.add_scene(scene2)
    sb.add_scene(scene3)

    print(f"\n📋 Storyboard: {sb.title}")
    print(f"   Scenes: {len(sb.scenes)}")
    print(f"   Total Duration: {sb.get_total_duration()}s")
    print(f"   Estimated Cost: ${sb.get_total_cost():.2f}")

    print("\n🎬 Scenes:")
    for i, scene in enumerate(sb.scenes, 1):
        print(f"   {i}. {scene.prompt} ({scene.duration}s) - ${scene.duration * 0.40:.2f}")

    # Test save/load
    saved_path = sb.save()
    print(f"\n💾 Saved to: {saved_path}")

    loaded_sb = Storyboard.load(sb.id)
    if loaded_sb:
        print(f"✅ Loaded: {loaded_sb.title} ({len(loaded_sb.scenes)} scenes)")

    # Test cost estimation
    cost_info = estimate_storyboard_cost(sb.scenes)
    print(f"\n💰 Cost Breakdown:")
    print(f"   Total: ${cost_info['total_cost']:.2f}")
    print(f"   Per scene: {cost_info['cost_per_scene']}")

    print("=" * 60)
