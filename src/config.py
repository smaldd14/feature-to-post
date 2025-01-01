from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# API Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Path Configuration
ROOT_DIR = Path(__file__).parent.parent
PROMPTS_DIR = ROOT_DIR / "prompts"
RESULTS_DIR = ROOT_DIR / "results"

# Ensure directories exist
RESULTS_DIR.mkdir(exist_ok=True)

def load_prompt(prompt_name: str) -> str:
    """Load prompt from file"""
    prompt_path = PROMPTS_DIR / f"{prompt_name}.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    
    return prompt_path.read_text().strip()

def get_result_dir(video_path: str) -> Path:
    """Get result directory path based on video filename"""
    video_path = Path(video_path)
    result_dir = RESULTS_DIR / video_path.stem
    result_dir.mkdir(exist_ok=True)
    return result_dir