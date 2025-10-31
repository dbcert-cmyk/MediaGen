"""
Vertex AI Pricing Configuration for MediaGen
Pricing data based on Google Cloud Vertex AI pricing (as of 2025)

IMPORTANT: Prices may change. Always verify current pricing at:
https://cloud.google.com/vertex-ai/generative-ai/pricing
"""


class VertexAIPricing:
    """Vertex AI pricing calculator for image and video generation"""

    # Gemini 2.5 Flash Image (Nano Banana) Pricing
    # Price per image generated
    GEMINI_FLASH_IMAGE_PER_IMAGE = 0.0025  # $0.0025 per image

    # Veo 3.1 Video Generation Pricing
    # $0.040 per second of generated video
    VEO_PRICE_PER_SECOND = 0.040

    # Calculated prices by duration (for quick reference)
    VEO_PRICING = {
        # Duration in seconds: price
        4: 0.16,   # 4 seconds × $0.040
        6: 0.24,   # 6 seconds × $0.040
        8: 0.32,   # 8 seconds × $0.040
    }

    @classmethod
    def estimate_image_cost(
        cls,
        number_of_images: int = 1,
        **kwargs
    ) -> dict:
        """
        Estimate cost for image generation with Gemini 2.5 Flash Image

        Args:
            number_of_images: Number of images to generate (1-10)

        Returns:
            dict: Cost breakdown with total, per_image, and details
        """
        per_image_cost = cls.GEMINI_FLASH_IMAGE_PER_IMAGE
        total_cost = per_image_cost * number_of_images

        return {
            "total": round(total_cost, 4),
            "per_image": round(per_image_cost, 4),
            "number_of_images": number_of_images,
            "model": "gemini-2.5-flash-image",
            "breakdown": f"{number_of_images} image(s) × ${per_image_cost:.4f} = ${total_cost:.4f}"
        }

    @classmethod
    def estimate_video_cost(
        cls,
        duration_seconds: int = 8,
        resolution: str = "720p",
        sample_count: int = 1,
        **kwargs
    ) -> dict:
        """
        Estimate cost for video generation with Veo 3.1
        Pricing: $0.040 per second of generated video

        Args:
            duration_seconds: Video duration (4, 6, or 8 seconds)
            resolution: Video resolution (720p or 1080p) - for display only, doesn't affect price
            sample_count: Number of videos to generate (1-4)

        Returns:
            dict: Cost breakdown with total, per_video, and details
        """
        # Calculate cost based on duration
        # Use pre-calculated prices if available, otherwise calculate
        if duration_seconds in cls.VEO_PRICING:
            per_video_cost = cls.VEO_PRICING[duration_seconds]
        else:
            # Calculate for custom duration
            per_video_cost = duration_seconds * cls.VEO_PRICE_PER_SECOND

        total_cost = per_video_cost * sample_count

        return {
            "total": round(total_cost, 2),
            "per_video": round(per_video_cost, 2),
            "per_second": cls.VEO_PRICE_PER_SECOND,
            "sample_count": sample_count,
            "duration": duration_seconds,
            "resolution": resolution,
            "model": "veo-3.1-generate-001",
            "breakdown": f"{sample_count} video(s) × ${per_video_cost:.2f} ({duration_seconds}s @ ${cls.VEO_PRICE_PER_SECOND}/sec) = ${total_cost:.2f}"
        }

    @classmethod
    def get_pricing_info(cls) -> dict:
        """
        Get all pricing information for display

        Returns:
            dict: Complete pricing data
        """
        return {
            "image": {
                "model": "gemini-2.5-flash-image",
                "per_image": cls.GEMINI_FLASH_IMAGE_PER_IMAGE,
                "description": "Gemini 2.5 Flash Image (Nano Banana)",
                "notes": "Price per image generated"
            },
            "video": {
                "model": "veo-3.1-generate-001",
                "per_second": cls.VEO_PRICE_PER_SECOND,
                "pricing_examples": cls.VEO_PRICING,
                "description": "Veo 3.1 Video Generation",
                "notes": "Price is $0.040 per second of generated video (resolution doesn't affect price)"
            },
            "disclaimer": "Prices shown are estimates. Actual costs may vary. "
                         "Always verify current pricing at cloud.google.com/vertex-ai/generative-ai/pricing"
        }


# Convenience functions
def estimate_image_cost(number_of_images: int = 1, **kwargs) -> dict:
    """Shorthand for VertexAIPricing.estimate_image_cost()"""
    return VertexAIPricing.estimate_image_cost(number_of_images, **kwargs)


def estimate_video_cost(duration_seconds: int = 8, resolution: str = "720p", sample_count: int = 1, **kwargs) -> dict:
    """Shorthand for VertexAIPricing.estimate_video_cost()"""
    return VertexAIPricing.estimate_video_cost(duration_seconds, resolution, sample_count, **kwargs)


if __name__ == "__main__":
    # Test the pricing calculator
    print("=" * 60)
    print("Vertex AI Cost Estimator - Test")
    print("=" * 60)

    # Test image pricing
    print("\n📷 IMAGE GENERATION COSTS:")
    print("-" * 60)
    for num_images in [1, 4, 8, 10]:
        cost = estimate_image_cost(num_images)
        print(f"{num_images} image(s): ${cost['total']:.4f} ({cost['breakdown']})")

    # Test video pricing
    print("\n🎬 VIDEO GENERATION COSTS ($0.040/second):")
    print("-" * 60)
    for duration in [4, 6, 8]:
        cost = estimate_video_cost(duration, "720p", 1)
        print(f"{duration}s video: ${cost['total']:.2f} ({duration} × $0.040)")

    print("\nNote: Resolution (720p/1080p) doesn't affect pricing")

    print("\n💰 SAMPLE SCENARIOS:")
    print("-" * 60)

    # Scenario 1: Typical image generation
    img_cost = estimate_image_cost(4)
    print(f"Generate 4 images: ${img_cost['total']:.4f}")

    # Scenario 2: Typical video generation
    vid_cost = estimate_video_cost(8, "720p", 1)
    print(f"Generate 1 video (8s): ${vid_cost['total']:.2f}")

    # Scenario 3: Multiple videos
    multi_vid_cost = estimate_video_cost(8, "1080p", 2)
    print(f"Generate 2 videos (8s each): ${multi_vid_cost['total']:.2f}")

    # Get all pricing info
    print("\n📋 COMPLETE PRICING INFO:")
    print("-" * 60)
    pricing_info = VertexAIPricing.get_pricing_info()
    print(f"Image Model: {pricing_info['image']['model']}")
    print(f"  Price: ${pricing_info['image']['per_image']:.4f} per image")
    print(f"Video Model: {pricing_info['video']['model']}")
    print(f"  Price: ${pricing_info['video']['per_second']:.3f} per second")
    print(f"  Note: {pricing_info['video']['notes']}")
    print(f"\n⚠️  {pricing_info['disclaimer']}")
    print("=" * 60)
