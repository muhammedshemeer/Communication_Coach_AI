import os
from groq import Groq

# API Key is now loaded from environment variables for security
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

def get_client():
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found in environment variables. Please set it before running the app.")
    return Groq(api_key=GROQ_API_KEY)

def chat_with_groq(messages: list, system_prompt: str) -> str:
    try:
        client = get_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"system","content":system_prompt}] + messages,
            max_tokens=600,
            temperature=0.75,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ AI Error: {str(e)}"

def generate_roadmap(role, target_days, daily_minutes, scenarios):
    try:
        client = get_client()
        prompt = f"""Create a {target_days}-day English communication learning roadmap for a VDart {role}.
Daily time available: {daily_minutes} minutes/day.
Practice scenarios: {', '.join(scenarios)}.
Format: Week-by-week plan with specific daily tasks. Be concise, practical, motivating. Max 380 words."""
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":prompt}],
            max_tokens=500, temperature=0.7
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"Could not generate roadmap: {e}"

def transcribe_audio_bytes(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """Transcribe audio — supports Tamil + English via Groq Whisper"""
    try:
        import tempfile, os
        client = get_client()
        ext = filename.split(".")[-1] if "." in filename else "webm"
        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        with open(tmp_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=(filename, f, f"audio/{ext}"),
                language=None,
                response_format="text"
            )
        os.unlink(tmp_path)
        return result if isinstance(result, str) else result.text
    except Exception as e:
        return f"[Error: {e}]"

def extract_score(text: str):
    import re
    for pat in [r"(\d+(?:\.\d+)?)/10", r"[Ss]core[:\s]+(\d+(?:\.\d+)?)", r"(\d+(?:\.\d+)?)\s*out of\s*10"]:
        m = re.search(pat, text)
        if m:
            s = float(m.group(1))
            if 0 <= s <= 10:
                return s
    return None
