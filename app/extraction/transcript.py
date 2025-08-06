from openai import OpenAI
from app.config import Settings

def transcribe_audio(audio_path: str) -> str:
    
    client = OpenAI(api_key=Settings.OPENAI_API_KEY, organization=Settings.OPENAI_ORGANIZATION_ID, project=Settings.OPENAI_PROJECT_ID)
    audio_file = open(audio_path, "rb")
    transcription = client.audio.transcriptions.create(
        model=Settings.GPT_TRANSCRIPT_MODEL, 
        file=audio_file
    )
    return transcription.text
