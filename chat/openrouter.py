import os
from openai import OpenAI
import mimetypes
import base64
import hashlib
import logging
from django.core.cache import cache
from .models import ChatSession

logger = logging.getLogger(__name__)

# look up an API key for OpenRouter; strip any surrounding quotes/spaces so
# users can write the value either with or without quotes in the .env file
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "").strip().strip('"')

MODEL = "openai/gpt-oss-120b:free"

# the base_url had an accidental encoded quote at the end which prevented the
# client from calling the proper host
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)


def build_user_content(message_obj):
    content = [{"type" : "text", "text" : message_obj.content}]

    for att in message_obj.attachements.all():
        file_path = att.file.path
        mime, _ = mimetypes.guess_type(file_path)
        mime = mime or 'application/octet-stream'
        with open(file_path, 'rb')  as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
        if att.file_type == "img":
            content.append({"type" : "image_url",
                            "image_url" : {"url" : f"data:{mime};base64,{b64}"}})
        else:
            content.append({"type" : "file", 
                            "file" : {
                                "filename" : att.file.name,
                                "file_data" : f"data:{mime};base64,{b64}"
                                }})
    return content

def make_cache_key(message_obj, model: str) -> str:
    files_sig = "|".join(
        f"{a.file.name}:{a.size}:{a.file_type}"
        for a in message_obj.attachments.all().order_by("id")
    )
    raw = f"{model}|{message_obj.content}|{files_sig}"
    return "ai:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def ask_openrouter(message_obj):
    key = make_cache_key(message_obj, MODEL)
    cached = cache.get(key)
    if cached:
        return cached
    
    if not OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY is not configured; skipping OpenRouter call")
        return "Klucz API nie jest skonfigurowany. Proszę dodaj OPENROUTER_API_KEY do pliku .env"
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", 
                       "content": build_user_content(message_obj)}],
            extra_body={"reasoning": {"enabled": True}},
        )

        answer = response.choices[0].message.content
        cache.set(key, answer, timeout=600)
        return answer
    except Exception as e:
        logger.error(f"OpenRouter error: {str(e)}")
        return "Przepraszamy, nie udało się przetworzyć Twojej wiadomości. Spróbuj ponownie."
    
