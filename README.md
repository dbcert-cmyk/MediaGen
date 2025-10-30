# MediaGen - AI Image & Video Generator

A web application for generating images and videos using Google Cloud's Vertex AI. This app provides an intuitive interface to create AI-generated media using state-of-the-art models like Imagen for image generation and Veo for video generation.

## Features

- **Image Generation**: Generate high-quality images using Vertex AI Imagen
  - Support for multiple images per request (1-8 images)
  - Customizable aspect ratios (1:1, 9:16, 16:9, 4:3, 3:4)
  - Negative prompts to exclude unwanted elements
  - Safety filters

- **Video Generation**: Create AI-generated videos using Vertex AI
  - Text-to-video generation
  - Customizable duration
  - High-quality video output

- **Modern Web Interface**: Clean, responsive UI with:
  - Tabbed interface for image and video generation
  - Real-time preview of generated media
  - Loading states and error handling

## Prerequisites

Before you begin, ensure you have the following:

1. **Python 3.8+** installed
2. **Google Cloud Platform (GCP) Account** with:
   - A GCP project with billing enabled
   - Vertex AI API enabled
   - Appropriate permissions to use Vertex AI

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd MediaGen
```

### 2. Set Up Google Cloud Authentication

#### Option A: Using Application Default Credentials (Recommended for Development)

```bash
# Install Google Cloud SDK if not already installed
# Then authenticate:
gcloud auth application-default login

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

#### Option B: Using a Service Account Key

1. Go to [GCP Console > IAM & Admin > Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Create a new service account or select an existing one
3. Grant the service account the following roles:
   - Vertex AI User
   - Storage Object Viewer (if accessing Cloud Storage)
4. Create and download a JSON key file
5. Set the environment variable:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-service-account-key.json"
```

### 3. Enable Required APIs

Enable the Vertex AI API in your GCP project:

```bash
gcloud services enable aiplatform.googleapis.com
```

Or via the [GCP Console](https://console.cloud.google.com/apis/library/aiplatform.googleapis.com)

### 4. Install Python Dependencies

```bash
# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit the `.env` file with your configuration:

```env
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1
```

### 6. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

## Usage

### Generating Images

1. Navigate to the **Image Generator** tab
2. Enter a detailed prompt describing the image you want to generate
3. (Optional) Add a negative prompt to specify what to avoid
4. Select the number of images (1-8)
5. Choose an aspect ratio
6. Click "Generate Images"
7. Wait for the images to be generated and displayed

**Example Prompts:**
- "A serene mountain landscape at sunset with a lake reflection"
- "A futuristic city with flying cars and neon lights"
- "A cute robot reading a book in a cozy library"

### Generating Videos

1. Navigate to the **Video Generator** tab
2. Enter a detailed prompt describing the video you want to generate
3. Select the duration (5-10 seconds)
4. Click "Generate Video"
5. Wait for the video to be generated (this may take 1-2 minutes)

**Example Prompts:**
- "A slow-motion shot of ocean waves crashing on a beach"
- "A time-lapse of a flower blooming"
- "A camera flying through a cyberpunk city at night"

**Note:** Video generation is currently in preview and may not be available in all regions. Check [Vertex AI documentation](https://cloud.google.com/vertex-ai/docs) for availability.

## API Endpoints

### Health Check
```
GET /health
```

### Generate Image
```
POST /api/generate-image
Content-Type: application/json

{
  "prompt": "A beautiful landscape",
  "negative_prompt": "blurry, low quality",
  "number_of_images": 4,
  "aspect_ratio": "16:9"
}
```

### Generate Video
```
POST /api/generate-video
Content-Type: application/json

{
  "prompt": "A serene ocean scene",
  "duration": 5
}
```

## Project Structure

```
MediaGen/
├── app.py                    # Main Flask application
├── vertex_ai_service.py      # Vertex AI integration service
├── requirements.txt          # Python dependencies
├── .env.example             # Example environment variables
├── .gitignore               # Git ignore file
├── README.md                # This file
├── templates/
│   └── index.html           # Web UI
└── generated_media/         # Generated images and videos (created at runtime)
```

## Configuration Options

### Image Generation Parameters

- **prompt** (required): Text description of the image
- **negative_prompt** (optional): Things to avoid in the image
- **number_of_images**: 1-8 images (default: 1)
- **aspect_ratio**: "1:1", "9:16", "16:9", "4:3", "3:4" (default: "1:1")
- **safety_filter_level**: "block_some", "block_few", "block_most" (default: "block_some")
- **person_generation**: "allow_adult", "allow_all" (default: "allow_adult")

### Video Generation Parameters

- **prompt** (required): Text description of the video
- **duration**: Duration in seconds, typically 5-10 (default: 5)

## Troubleshooting

### Authentication Errors

If you see authentication errors:
1. Verify your GCP credentials are set up correctly
2. Check that the service account has the required permissions
3. Ensure the Vertex AI API is enabled in your project

### API Not Available Errors

If video generation is not available:
- Video generation (Veo) is in preview and may not be available in all regions
- Check [Vertex AI documentation](https://cloud.google.com/vertex-ai/docs) for regional availability
- Try changing the `GCP_LOCATION` in your `.env` file to a supported region

### Module Import Errors

If you see import errors:
```bash
pip install --upgrade -r requirements.txt
```

### Quota Errors

If you exceed quotas:
- Check your [GCP Quotas page](https://console.cloud.google.com/iam-admin/quotas)
- Request quota increases if needed
- Note that Vertex AI has default quotas for API calls

## Cost Considerations

**Important:** Using Vertex AI incurs costs. Check the [Vertex AI pricing page](https://cloud.google.com/vertex-ai/pricing) for current rates.

Approximate costs (as of 2024):
- Image generation: ~$0.02-0.08 per image
- Video generation: Higher cost, varies by duration

Always monitor your [GCP Billing](https://console.cloud.google.com/billing) to avoid unexpected charges.

## Security Best Practices

1. **Never commit credentials**: The `.gitignore` file excludes credential files
2. **Use service accounts**: Create dedicated service accounts with minimal permissions
3. **Rotate keys regularly**: If using service account keys, rotate them periodically
4. **Enable audit logs**: Monitor Vertex AI API usage in Cloud Logging
5. **Set up billing alerts**: Get notified when costs exceed thresholds

## Development

### Running in Debug Mode

The app runs in debug mode by default. For production, use a WSGI server:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Environment Variables

- `GCP_PROJECT_ID`: Your GCP project ID (required)
- `GCP_LOCATION`: GCP region (default: us-central1)
- `PORT`: Port to run the app (default: 5000)
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account key (optional)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is provided as-is for educational and development purposes.

## Resources

- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Imagen Documentation](https://cloud.google.com/vertex-ai/docs/generative-ai/image/overview)
- [Veo Video Generation](https://cloud.google.com/vertex-ai/docs/generative-ai/video/overview)
- [Flask Documentation](https://flask.palletsprojects.com/)

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review [Vertex AI documentation](https://cloud.google.com/vertex-ai/docs)
3. Open an issue in this repository

---

Built with Vertex AI, Flask, and Python
