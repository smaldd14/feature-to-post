# feature-to-post
A Python-based tool that automatically generates social media content from feature demonstration videos. The tool processes screen recordings of new features, breaks them into logical chapters if needed, and generates professional tweet threads describing the features and their benefits.

## Features
- Processes screen recordings of any length
- Optional chapter detection and video segmentation
- Generates structured, professional tweet threads
- Handles both short demos (1-2 tweets) and longer features (4-6 tweets)
- Saves all results and processed videos in organized directories

## Prerequisites
```bash
Python 3.8+
FFmpeg installed on your system
Google Gemini API key
uv package manager (recommended)
```

## Setup
- Install uv if you haven't already:
`bashCopycurl -LsSf https://astral.sh/uv/install.sh | sh`

- Clone the repository:
```bash
git clone https://github.com/yourusername/feature-to-post.git
cd feature-to-post
```

- Create and activate virtual environment:
```bash
uv venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
```

- Install dependencies:
```bash
uv pip install -r requirements.txt
```

- Create a .env file in the project root:

```bash
GOOGLE_API_KEY=your_gemini_api_key_here
```

## Usage
- Process a video with chapter detection:
`python main.py /path/to/your/video.mp4`
- Process a video as a single unit (no chapters):
`python main.py /path/to/your/video.mp4 --no-split`
- Results will be saved in results/video_name/:
```bash
analysis.json: Contains the generated tweets and chapter information
chapter_*.mp4: Individual chapter videos (if splitting was enabled)
```