from gtts import gTTS
from django.core.files.base import ContentFile
import io


def mime_dictionary():
    return {
        "text/plain": "txt",
        "application/pdf": "pdf",
        "image/jpeg": "jpg",
        "image/png": "png"    
        }

def generate_tts_file(text):
    mp3 = gTTS(text=text, tld="com", lang='en')
    buffer = io.bytesIO()
    mp3.write_to_fp(buffer)
    buffer.seek(0)
    return buffer.getvalue()