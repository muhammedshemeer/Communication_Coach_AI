import streamlit as st
from gtts import gTTS
import tempfile
import os
import io
import base64

def text_to_speech(text: str, lang: str = "en") -> str:
    """Convert text to speech and return base64 audio for autoplay"""
    try:
        # Clean text for TTS (remove emojis and special chars)
        import re
        clean_text = re.sub(r'[^\w\s.,!?;:\-\']', ' ', text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        if not clean_text:
            return None

        tts = gTTS(text=clean_text, lang=lang, slow=False)
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)

        audio_b64 = base64.b64encode(audio_bytes.read()).decode()
        audio_html = f"""
        <audio autoplay style="display:none">
            <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
        </audio>
        """
        return audio_html
    except Exception as e:
        return None

def transcribe_audio_whisper(audio_bytes: bytes, api_key: str) -> str:
    """Transcribe audio using Groq's Whisper API (handles Tamil + English)"""
    try:
        from groq import Groq
        client = Groq(api_key=api_key)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=("audio.wav", audio_file, "audio/wav"),
                language=None,  # Auto-detect Tamil or English
                response_format="text"
            )
        os.unlink(tmp_path)
        return transcription if isinstance(transcription, str) else transcription.text

    except Exception as e:
        return f"[Transcription error: {str(e)}]"

def get_audio_recorder_html() -> str:
    """Returns HTML/JS for browser-based audio recording"""
    return """
    <style>
    .recorder-container {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px;
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.1);
        margin: 8px 0;
    }
    #recordBtn {
        background: linear-gradient(135deg, #FF6B6B, #FF8E53);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        font-size: 14px;
        transition: all 0.2s;
    }
    #recordBtn.recording {
        background: linear-gradient(135deg, #56CFE1, #9B59B6);
        animation: pulse 1s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    #status { color: #aaa; font-size: 13px; }
    </style>

    <div class="recorder-container">
        <button id="recordBtn" onclick="toggleRecording()">🎙️ Start Recording</button>
        <span id="status">Click to speak in English or Tamil</span>
    </div>

    <script>
    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;

    async function toggleRecording() {
        if (!isRecording) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
                mediaRecorder.onstop = async () => {
                    const blob = new Blob(audioChunks, { type: 'audio/wav' });
                    const reader = new FileReader();
                    reader.onload = () => {
                        const b64 = reader.result.split(',')[1];
                        window.parent.postMessage({type: 'audio_recorded', data: b64}, '*');
                    };
                    reader.readAsDataURL(blob);
                };
                mediaRecorder.start();
                isRecording = true;
                document.getElementById('recordBtn').textContent = '⏹️ Stop Recording';
                document.getElementById('recordBtn').classList.add('recording');
                document.getElementById('status').textContent = '🔴 Recording... speak now';
            } catch(e) {
                document.getElementById('status').textContent = 'Microphone access denied';
            }
        } else {
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(t => t.stop());
            isRecording = false;
            document.getElementById('recordBtn').textContent = '🎙️ Start Recording';
            document.getElementById('recordBtn').classList.remove('recording');
            document.getElementById('status').textContent = '✅ Processing audio...';
        }
    }
    </script>
    """
