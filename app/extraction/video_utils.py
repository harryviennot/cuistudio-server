from moviepy import VideoFileClip
import os
import cv2

def extract_audio(video_path: str) -> str:
    clip = VideoFileClip(video_path)
    audio_path = video_path.replace(".mp4", ".wav")
    clip.audio.write_audiofile(audio_path)
    return audio_path

def extract_frames(video_path: str, max_frames: int = 10) -> list[str]:
    """
    Optimized frame extraction that extracts fewer frames more efficiently
    """
    cap = cv2.VideoCapture(video_path)
    frame_paths = []
    
    # Get video properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps
    
    # Calculate frame intervals to get max_frames evenly distributed
    if total_frames <= max_frames:
        # If video has fewer frames than max_frames, extract all
        frame_indices = list(range(0, total_frames))
    else:
        # Extract frames evenly distributed throughout the video
        step = total_frames // max_frames
        frame_indices = [i * step for i in range(max_frames)]
    
    # Extract only the selected frames
    for i, frame_idx in enumerate(frame_indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if ret:
            frame_path = f"frames/frame_{i}.jpg"
            # Reduce image quality for faster processing
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            frame_paths.append(frame_path)
    
    cap.release()
    return frame_paths
