from pathlib import Path
import asyncio
from typing import List, Dict
import google.generativeai as genai
import ffmpeg
import json
import time
from src import config
from src.schemas import Chapter, ChapterBreakdown, TweetThread

system_prompt = config.load_prompt('system_prompt')
feature_explanation_prompt = config.load_prompt('feature_explanation')
enhance_audio_prompt = config.load_prompt('enhance_audio')

class GeminiVideoProcessor:
    def __init__(self):
        # Initialize Gemini
        genai.configure(api_key=config.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp")
    
    async def process_video(self, video_path: str, split_chapters: bool = True) -> Dict:
        """Main processing pipeline"""
        video_path = Path(video_path).resolve()
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Get output directory
        output_dir = config.get_result_dir(video_path)
        output_dir.mkdir(exist_ok=True)
        
        print(f"Uploading video file...")
        video_file = genai.upload_file(path=str(video_path), mime_type="video/mp4")
        print(f"Completed upload: {video_file.uri}")
        
        # Wait for file to be ready
        print("Waiting for file processing...")
        while video_file.state.name == "PROCESSING":
            print('.', end='', flush=True)
            time.sleep(10)
            video_file = genai.get_file(video_file.name)
        print("\nFile ready!")
        
        if video_file.state.name == "FAILED":
            raise ValueError(f"File processing failed: {video_file.state}")
        
        if split_chapters:
            # Get chapters from Gemini
            chapters = await self.get_chapters_from_gemini(video_file)
            # Split video into chunks
            await self.split_video(video_path, chapters, output_dir)
            # Analyze each chunk
            results = await self.analyze_chunks(chapters, output_dir)
        else:
            # Create single chapter for entire video
            duration = self.get_video_duration(video_path)
            chapters = [{
                "start_time": 0,
                "end_time": duration,
                "title": "Full Video",
                "description": "Complete video analysis"
            }]
            # Create symbolic link or copy to results directory
            output_path = output_dir / f"chapter_1.mp4"
            if not output_path.exists():
                output_path.symlink_to(video_path)
            
            # Generate post from full video
            results = await self.analyze_video(video_file, duration)
        
        # Save results
        results_data = {
            "chapters": chapters,
            "tweet_threads": results
        }
        results_file = output_dir / "analysis.json"
        results_file.write_text(json.dumps(results_data, indent=2))
        
        return results_data
    
    def get_video_duration(self, video_path: str) -> float:
        """Get video duration using FFmpeg"""
        probe = ffmpeg.probe(video_path)
        duration = float(probe['streams'][0]['duration'])
        return duration
    
    async def get_chapters_from_gemini(self, video_file) -> List[Chapter]:
        """Get chapter information from Gemini"""
        chapter_prompt = config.load_prompt('chapter_breakdown')
        
        print("Requesting chapter breakdown...")
        response = self.model.generate_content(
            [video_file, system_prompt, chapter_prompt],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=ChapterBreakdown
            ),
            request_options={"timeout": 600}
        )
        print(f"Response: {response.text}")
        chapters_data = json.loads(response.text) 
        print(f"Chapters: {chapters_data}")
        return chapters_data
    
    def get_appropriate_prompt(self, duration: float) -> str:
        """Select appropriate prompt based on video duration"""
        if duration <= 60:  # 60 seconds threshold
            return config.load_prompt('feature_to_post_short')
        return config.load_prompt('feature_to_post_long')

    async def analyze_video(self, video_file, duration: float) -> TweetThread:
        """Analyze video"""        
        # Load appropriate prompt based on duration
        post_prompt = self.get_appropriate_prompt(duration)
        
        print("Analyzing video...")
        # response = self.model.generate_content(
        #     [video_file, system_prompt, post_prompt],
        #     generation_config=genai.GenerationConfig(
        #         response_mime_type="application/json",
        #         response_schema=TweetThread
        #     ),
        #     request_options={"timeout": 600}
        # )
        response = self.model.generate_content(
            [video_file, system_prompt, enhance_audio_prompt],
            request_options={"timeout": 600}
        )

        print(f"Response: {response.text}")
        
        return json.loads(response.text)
    
    async def split_video(self, video_path: str, chapters: List[Chapter], output_dir: Path):
        """Split video into chunks based on chapters using FFmpeg"""
        tasks = []
        
        for i, chapter in enumerate(chapters):
            output_path = output_dir / f"chapter_{i+1}.mp4"
            
            if not output_path.exists():
                # Prepare FFmpeg command
                stream = ffmpeg.input(str(video_path))
                stream = stream.trim(start=chapter["start_time"], end=chapter["end_time"])
                stream = stream.setpts('PTS-STARTPTS')
                stream = stream.output(str(output_path))
                
                # Create task for async execution
                process = asyncio.create_subprocess_exec(
                    *stream.compile(),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                tasks.append(process)
        
        if tasks:
            # Run all FFmpeg tasks concurrently
            await asyncio.gather(*tasks)
    
    async def analyze_chunks(self, chapters: List[Chapter], output_dir: Path) -> List[TweetThread]:
        """Analyze each video chunk with Gemini"""
        results = []
        post_prompt = config.load_prompt('feature_to_post')
        
        for i in range(len(chapters)):
            video_path = output_dir / f"chapter_{i+1}.mp4"
            
            print(f"Uploading chapter {i+1}...")
            chunk_file = genai.upload_file(path=str(video_path), mime_type="video/mp4")
            
            # Wait for file to be ready
            while chunk_file.state.name == "PROCESSING":
                print('.', end='', flush=True)
                time.sleep(10)
                chunk_file = genai.get_file(chunk_file.name)
            print("\nChunk ready!")
            
            if chunk_file.state.name == "FAILED":
                raise ValueError(f"Chunk processing failed: {chunk_file.state}")
            
            # Generate post from chunk
            print(f"Generating post for chapter {i+1}...")
            response = self.model.generate_content(
                [chunk_file, system_prompt, post_prompt],
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=TweetThread
                ),
                request_options={"timeout": 600}
            )
            
            thread = json.loads(response.text)
            results.append(thread)
        
        return results