import asyncio
import argparse
from src.video_processor import GeminiVideoProcessor

async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process video with Gemini AI')
    parser.add_argument('video_path', type=str, help='Absolute path to the video file')
    parser.add_argument('--no-split', action='store_true', help='Process video as a single chunk without splitting')
    
    args = parser.parse_args()
    
    # Process video
    processor = GeminiVideoProcessor()
    try:
        results = await processor.process_video(
            video_path=args.video_path,
            split_chapters=not args.no_split
        )
        print(f"Processing complete. Results saved in results/{results['chapters'][0]['title']}")
    except Exception as e:
        print(f"Error processing video: {e}")

if __name__ == "__main__":
    asyncio.run(main())