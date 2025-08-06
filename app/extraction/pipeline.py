import time
import concurrent.futures
from app.extraction.downloader import download_video
from app.extraction.video_utils import extract_audio, extract_frames
from app.extraction.transcript import transcribe_audio
from app.extraction.ocr import run_ocr_on_frames
from app.extraction.parser import parse_recipe
from app.config import Settings

def run_extraction_pipeline(link: str) -> dict:
    
    video_path, description = download_video(link)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=Settings.MAX_WORKERS) as executor:
        # Submit all independent tasks
        audio_future = executor.submit(extract_audio, video_path)
        frames_future = executor.submit(extract_frames, video_path)
        
        # Get results
        audio_path = audio_future.result()
        frame_paths = frames_future.result()
        
        
        transcript_future = executor.submit(transcribe_audio, audio_path)
        ocr_future = executor.submit(run_ocr_on_frames, frame_paths)
        
        # Get results
        transcript = transcript_future.result()
        ocr_text = ocr_future.result()

    
    full_input = f"{description}\n\n{transcript}\n\n{ocr_text}"
    
    parsed_recipe = parse_recipe(full_input)
    parsed_recipe["video_link"] = link
    
    return parsed_recipe

