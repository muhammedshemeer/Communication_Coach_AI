import streamlit as st
import sys, random, time, base64, io
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from chatbot.role_prompts import ROLES, get_system_prompt
from chatbot.groq_client import chat_with_groq, generate_roadmap, transcribe_audio_bytes, extract_score
from database.db import (
    init_db, create_employee, get_employee, get_all_employees,
    start_session, end_session, save_message,
    get_session_history, get_session_messages, get_avg_score
)

# Custom Input Overlay Script (Injects Mic/Voice buttons over standard st.text_input)
INPUT_OVERLAY_HTML = """
<div id="vdart-input-overlay">
    <div id="ov-mic" class="overlay-mic" onclick="ovToggleVoice()" title="Voice Input">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>
    </div>
    <div id="ov-voice" class="overlay-voice" onclick="ovToggleVoice()">Voice</div>
</div>

<script>
var ovRecognition;
var ovIsListening = false;

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  ovRecognition = new SR();
  ovRecognition.continuous = true;
  ovRecognition.interimResults = true;
  ovRecognition.lang = 'en-IN';

  ovRecognition.onstart = function() { 
    ovIsListening = true; 
    document.getElementById('ov-mic').classList.add('active');
    document.getElementById('ov-voice').classList.add('active');
    document.getElementById('ov-voice').textContent = 'Listening...';
  };
  ovRecognition.onresult = function(event) {
    var final = '';
    for (var i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) final += event.results[i][0].transcript;
    }
    if (final) {
      // Find the Streamlit input directly in the parent DOM
      const inputs = window.parent.document.querySelectorAll('input');
      let target = Array.from(inputs).find(i => i.placeholder === 'Ask anything...');
      if (target) {
        target.value += (target.value ? ' ' : '') + final;
        target.dispatchEvent(new Event('input', { bubbles: true }));
      }
    }
  };
  ovRecognition.onend = function() { 
    ovIsListening = false; 
    document.getElementById('ov-mic').classList.remove('active');
    document.getElementById('ov-voice').classList.remove('active');
    document.getElementById('ov-voice').textContent = 'Voice';
  };
}

function ovToggleVoice() {
  if (!ovRecognition) return alert('Speech API not supported.');
  ovIsListening ? ovRecognition.stop() : ovRecognition.start();
}
</script>
"""

def speak(text):
    try:
        from gtts import gTTS
        import re
        clean = re.sub(r'[^\w\s.,!?;:\-\']', ' ', text)
        clean = re.sub(r'\s+', ' ', clean).strip()[:800]
        if not clean: return
        tts = gTTS(text=clean, lang="en", slow=False)
        buf = io.BytesIO(); tts.write_to_fp(buf); buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode()
        st.markdown(f'<audio autoplay style="display:none"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)
    except: pass

def send_message(user_text, emp, scenario, prefix=""):
    display = f"{prefix}{user_text}" if prefix else user_text
    st.session_state.messages.append({"role": "user", "content": display})
    save_message(emp["id"], st.session_state.session_id, "user", user_text)
    sp = get_system_prompt(emp["role"], emp["target_days"], emp["daily_minutes"], emp["total_sessions"]+1, scenario)
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    with st.spinner("CommBot is thinking..."):
        reply = chat_with_groq(history, sp)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    save_message(emp["id"], st.session_state.session_id, "assistant", reply)
    score = extract_score(reply)
    if score: st.session_state.session_scores.append(score)
    if st.session_state.tts_on: speak(reply)
    st.rerun()

# ── Page config: sidebar EXPANDED so arrow shows ──────────────
st.set_page_config(
    page_title="CommBot · VDart",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Session state ─────────────────────────────────────────────
init_db()
defs = {
    "page": "landing", "employee_id": None, "session_id": None,
    "messages": [], "session_active": False, "current_scenario": None,
    "session_start_time": None, "tts_on": True, "session_scores": [],
    "pending_text": "", "view_session_id": None,
}
for k, v in defs.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════
#  CSS — style Streamlit's own sidebar + hamburger button
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Serif+Display&family=DM+Mono:wght@400;500&display=swap');

:root {
  --bg:      #F7F5F0;
  --surface: #FFFFFF;
  --sf2:     #F0EDE6;
  --border:  #E2DDD6;
  --teal:    #1A6B6B;
  --teal-l:  #EAF4F4;
  --teal-d:  #134F4F;
  --text:    #1C1917;
  --text2:   #57534E;
  --text3:   #A8A29E;
  --r:       12px;
  --sh:      0 1px 4px rgba(0,0,0,.07), 0 4px 12px rgba(0,0,0,.04);
  --sh-t:    0 4px 14px rgba(26,107,107,.18);
}

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: var(--bg); color: var(--text); }

/* ── Hide Streamlit default header bar completely ── */
header[data-testid="stHeader"] { display: none !important; }
#MainMenu { display: none !important; }
footer { display: none !important; }
.stDeployButton { display: none !important; }

/* ── Style Streamlit's sidebar (White Theme) ── */
[data-testid="stSidebar"] {
  background: #FFFFFF !important;
  border-right: 1px solid var(--border) !important;
  box-shadow: 2px 0 10px rgba(0,0,0,0.05) !important;
}

/* Make sidebar text teal/dark */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
  color: var(--teal) !important;
}


/* ── The hamburger/arrow toggle button ── */
[data-testid="collapsedControl"] {
  background: #FFFFFF !important;
  border: 1px solid var(--border) !important;
  border-radius: 0 8px 8px 0 !important;
  width: 36px !important;
  height: 60px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  box-shadow: 2px 0 8px rgba(0,0,0,0.05) !important;
  top: 50vh !important;
  transform: translateY(-50%) !important;
  position: fixed !important;
  left: 0 !important;
  z-index: 9999 !important;
}
[data-testid="collapsedControl"] svg {
  fill: var(--teal) !important;
  width: 20px !important;
  height: 20px !important;
}


/* ── Sidebar buttons ── */
[data-testid="stSidebar"] .stButton > button {
  background: var(--teal-l) !important;
  color: var(--teal) !important;
  border: 1px solid rgba(26,107,107,0.2) !important;
  border-radius: 8px !important;
  font-size: 0.87rem !important;
  font-weight: 600 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: var(--teal) !important;
  color: #FFFFFF !important;
}


/* ── Sidebar toggle (the on/off switch) ── */
[data-testid="stSidebar"] .stToggle > label { color: #D1FAE5 !important; }

/* ── Main area ── */
.main .block-container {
  padding-top: 28px !important;
  padding-left: 32px !important;
  padding-right: 32px !important;
  max-width: 1100px;
}

/* ── ALL Buttons (Force High Visibility) ── */
div[data-testid="stButton"] > button,
button[kind="secondary"],
button[kind="primary"],
button {
  background-color: #FFFFFF !important;
  color: #1A6B6B !important;
  border: 2px solid #1A6B6B !important;
  border-radius: 12px !important;
  font-weight: 700 !important;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
}

/* Force text inside buttons to be teal */
div[data-testid="stButton"] > button p,
div[data-testid="stButton"] > button span,
button p, button span, button div {
  color: #1A6B6B !important;
  font-weight: 700 !important;
  opacity: 1 !important;
}

button:hover {
  background-color: #EAF4F4 !important;
  transform: translateY(-2px) !important;
}

/* ── DEEP WHITE PILL INPUT FIX ── */
[data-testid="stChatInput"], 
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] div,
[data-testid="stChatInput"] textarea {
    background-color: #FFFFFF !important;
    color: #1C1917 !important;
}

[data-testid="stChatInput"] {
    border-radius: 28px !important;
    border: 1.5px solid #E2DDD6 !important;
    padding: 2px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06) !important;
}

[data-testid="stChatInput"] button {
    background-color: #1A6B6B !important;
    color: #FFFFFF !important;
    border-radius: 50% !important;
}

.stChatInputContainer {
    background-color: transparent !important;
    border: none !important;
    padding-bottom: 25px !important;
}








/* ── Inputs ── */
.stTextInput > div > div > input {
  background: var(--surface) !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 26px !important;
  color: var(--text) !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 0.93rem !important;
  padding: 10px 18px !important;
}
.stTextInput > div > div > input:focus {
  border-color: var(--teal) !important;
  box-shadow: 0 0 0 3px rgba(26,107,107,0.12) !important;
}
.stSelectbox > div > div {
  background: var(--surface) !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--sf2) !important;
  border-radius: 10px !important;
  padding: 3px !important;
  border: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
  color: var(--text2) !important;
  border-radius: 7px !important;
  font-weight: 500 !important;
}
.stTabs [aria-selected="true"] {
  background: var(--surface) !important;
  color: var(--teal) !important;
  font-weight: 700 !important;
}

/* ── Cards ── */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 20px 24px;
  box-shadow: var(--sh);
}
.card-teal { background: var(--teal-l); border-color: rgba(26,107,107,0.2); }

/* ── Hero banner (White Theme) ── */
.hero {
  background: #FFFFFF !important;
  border: 2px solid var(--teal) !important;
  border-radius: 16px;
  padding: 34px 44px;
  color: var(--teal) !important;
  margin-bottom: 28px;
  position: relative;
  overflow: hidden;
  box-shadow: var(--sh-t);
}
.hero-title {
  font-family: 'DM Serif Display', serif;
  font-size: 2.3rem; margin: 0 0 8px;
  color: var(--teal) !important;
}
.hero-sub { font-size: 0.97rem; color: var(--text2) !important; margin: 0; line-height: 1.6; }
.hero::after {
  content: '';
  position: absolute; right: -40px; top: -40px;
  width: 220px; height: 220px; border-radius: 50%;
  background: rgba(255,255,255,0.05);
  pointer-events: none;
}
.hero-ey {
  font-size: 0.7rem; font-weight: 700; letter-spacing: 2px;
  text-transform: uppercase; opacity: 0.65; margin-bottom: 10px;
}
.hero-title {
  font-family: 'DM Serif Display', serif;
  font-size: 2.3rem; margin: 0 0 8px;
}
.hero-sub { font-size: 0.97rem; opacity: 0.82; margin: 0; line-height: 1.6; }

/* ── Chat bubbles ── */
.b-user {
  background: var(--teal); color: #fff;
  border-radius: 18px 18px 4px 18px;
  padding: 12px 18px; margin: 8px 0; margin-left: 18%;
  font-size: 0.93rem; line-height: 1.65; box-shadow: var(--sh-t);
}
.b-bot {
  background: var(--surface); color: var(--text);
  border: 1px solid var(--border);
  border-radius: 18px 18px 18px 4px;
  padding: 14px 18px; margin: 8px 0; margin-right: 10%;
  font-size: 0.93rem; line-height: 1.75; box-shadow: var(--sh);
}
.b-lbl {
  font-size: 0.66rem; font-weight: 700;
  letter-spacing: 1.2px; text-transform: uppercase;
  margin-bottom: 5px; opacity: 0.5;
}

/* ── Metrics ── */
.metric {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--r); padding: 18px; text-align: center; box-shadow: var(--sh);
}
.metric-val { font-family: 'DM Mono', monospace; font-size: 1.9rem; font-weight: 500; color: var(--teal); }
.metric-lbl { font-size: 0.74rem; color: var(--text3); margin-top: 3px; font-weight: 500; }

/* ── Role cards ── */
.role-card {
  background: var(--surface); border: 1.5px solid var(--border);
  border-radius: var(--r); padding: 18px 14px; text-align: center;
  transition: all 0.2s; box-shadow: var(--sh); height: 100%;
}
.role-card:hover { border-color: var(--teal); transform: translateY(-2px); box-shadow: var(--sh-t); }

/* ── Chips ── */
.chip {
  display: inline-block; background: var(--teal-l);
  border: 1px solid rgba(26,107,107,0.2);
  color: var(--teal); padding: 5px 12px;
  border-radius: 20px; font-size: 0.79rem; font-weight: 600; margin: 3px;
}

/* ── Progress bar ── */
.prog-bg { background: var(--sf2); border-radius: 8px; height: 10px; overflow: hidden; border: 1px solid var(--border); }
.prog-fill { height: 100%; border-radius: 8px; background: linear-gradient(90deg, var(--teal), #2DA8A8); }

/* ── Unified Input Bar ── */
.input-container {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  background: #fff;
  border: 1.5px solid var(--border);
  border-radius: 30px;
  padding: 6px 10px 6px 20px;
  box-shadow: var(--sh);
  transition: all 0.2s;
  margin: 10px 0;
}
.input-container:focus-within {
  border-color: var(--teal);
  box-shadow: 0 0 0 4px rgba(26,107,107,0.1);
}
#smi-input {
  flex: 1;
  border: none !important;
  outline: none !important;
  background: transparent !important;
  font-size: 0.95rem;
  color: var(--text);
  padding: 8px 0 !important;
  font-family: 'DM Sans', sans-serif;
}
#smi-input::placeholder { color: var(--text3); }

.input-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}
.icon-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  background: transparent;
  color: var(--text2);
}
.icon-btn:hover { background: var(--sf2); color: var(--teal); }
.icon-btn.active { background: #DC2626; color: #fff; animation: pulse 1.5s infinite; }

.voice-btn {
  background: var(--sf2);
  color: var(--teal);
  border: none;
  border-radius: 20px;
  padding: 8px 18px;
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}
.voice-btn:hover { background: var(--teal-l); }
.voice-btn.active { background: #DC2626; color: #fff; }

.send-btn {
  background: var(--teal);
  color: #fff;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(26,107,107,0.25);
}
.send-btn:hover { background: var(--teal-d); transform: scale(1.05); }

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(220, 38, 38, 0); }
  100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }
}


/* ── Sidebar history items ── */
.hist-item {
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px; padding: 9px 12px; margin-bottom: 5px;
}
.hist-sc { font-size: 0.82rem; font-weight: 600; color: #D1FAE5; }
.hist-meta { font-size: 0.7rem; color: rgba(255,255,255,0.35); margin-top: 2px; }

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--sf2); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
hr { border-color: var(--border) !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  SIDEBAR  — uses Streamlit's native sidebar (toggle works!)
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    # Logo
    st.markdown("""
    <div style="text-align:center;padding:10px 0 18px;">
      <div style="font-size:2.6rem;">🎙️</div>
      <div style="font-family:'DM Serif Display',serif;font-size:1.25rem;color:#1A6B6B;margin-top:4px;">CommBot</div>
      <div style="font-size:0.62rem;color:#A8A29E;letter-spacing:2.5px;font-weight:700;">VDART · AI COACH</div>
    </div>
    """, unsafe_allow_html=True)


    st.markdown('<hr style="border-color:rgba(255,255,255,0.12);margin:0 0 14px;">', unsafe_allow_html=True)

    # Voice toggle
    st.session_state.tts_on = st.toggle("🔊 Voice Responses", value=st.session_state.tts_on)

    st.markdown('<hr style="border-color:rgba(255,255,255,0.12);margin:14px 0;">', unsafe_allow_html=True)

    # Navigation
    st.markdown('<div style="font-size:0.66rem;font-weight:700;letter-spacing:2px;color:rgba(255,255,255,0.35);margin-bottom:8px;">NAVIGATE</div>', unsafe_allow_html=True)

    if st.button("🏠  Home", use_container_width=True, key="nav_home"):
        st.session_state.page = "landing"; st.rerun()

    if st.button("💬  Practice Chat", use_container_width=True, key="nav_chat"):
        st.session_state.page = "chat" if st.session_state.employee_id else "setup"; st.rerun()

    if st.button("📊  My Progress", use_container_width=True, key="nav_prog"):
        st.session_state.page = "progress"; st.rerun()

    if st.button("✏️  New Chat", use_container_width=True, key="nav_new"):
        st.session_state.session_active = False
        st.session_state.messages = []
        st.session_state.session_scores = []
        st.session_state.page = "chat" if st.session_state.employee_id else "setup"
        st.rerun()

    st.markdown('<hr style="border-color:rgba(255,255,255,0.12);margin:14px 0;">', unsafe_allow_html=True)

    # Profile card
    if st.session_state.employee_id:
        emp_sb = get_employee(st.session_state.employee_id)
        if emp_sb:
            rd_sb = ROLES.get(emp_sb["role"], ROLES["Custom / Other Role"])
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.14);
                 border-radius:10px;padding:13px;margin-bottom:12px;">
              <div style="display:flex;align-items:center;gap:10px;">
                <div style="font-size:1.8rem;">{rd_sb["icon"]}</div>
                <div>
                  <div style="font-weight:700;font-size:0.93rem;color:#D1FAE5;">{emp_sb["name"]}</div>
                  <div style="font-size:0.73rem;color:rgba(255,255,255,0.45);">{emp_sb["role"]}</div>
                </div>
              </div>
              <div style="margin-top:9px;display:flex;gap:14px;">
                <span style="font-size:0.73rem;color:#FCD34D;font-weight:600;">🔥 {emp_sb["streak"]} streak</span>
                <span style="font-size:0.73rem;color:rgba(255,255,255,0.4);">{emp_sb["total_sessions"]} sessions</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Chat history list
            st.markdown('<div style="font-size:0.66rem;font-weight:700;letter-spacing:2px;color:rgba(255,255,255,0.35);margin-bottom:8px;">RECENT CHATS</div>', unsafe_allow_html=True)
            hlist = get_session_history(st.session_state.employee_id)
            if hlist:
                for h in hlist[:8]:
                    ds = (h["date"] or "")[:10]
                    sc_s = f"· {h['score']}/10" if h["score"] else ""
                    label = (h["scenario"] or "Practice")[:24]
                    st.markdown(f"""
                    <div class="hist-item">
                      <div class="hist-sc">💬 {label}</div>
                      <div class="hist-meta">{ds} {sc_s}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"View", key=f"hv_{h['id']}", use_container_width=True):
                        st.session_state.view_session_id = h["id"]
                        st.session_state.page = "history"
                        st.rerun()
            else:
                st.markdown('<div style="font-size:0.78rem;color:rgba(255,255,255,0.3);padding:6px 0;">No sessions yet</div>', unsafe_allow_html=True)

            st.markdown('<hr style="border-color:rgba(255,255,255,0.12);margin:14px 0;">', unsafe_allow_html=True)
            if st.button("🔄  Switch Profile", use_container_width=True, key="nav_switch"):
                st.session_state.employee_id = None
                st.session_state.messages = []
                st.session_state.session_active = False
                st.session_state.page = "setup"
                st.rerun()
    else:
        st.markdown('<div style="font-size:0.82rem;color:rgba(255,255,255,0.4);padding:6px 0;">No profile selected</div>', unsafe_allow_html=True)
        if st.button("👤  Create Profile", use_container_width=True, key="nav_create"):
            st.session_state.page = "setup"; st.rerun()

# ══════════════════════════════════════════════════════════════
#  MIC + SEARCH BAR
# ══════════════════════════════════════════════════════════════
SEARCH_MIC = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
:root {
  --teal: #1A6B6B;
  --teal-d: #134F4F;
  --teal-l: #EAF4F4;
  --border: #E2DDD6;
  --text: #1C1917;
  --text2: #57534E;
  --text3: #A8A29E;
  --sf2: #F0EDE6;
}
body { margin: 0; padding: 0; font-family: 'DM Sans', sans-serif; background: transparent; overflow: hidden; }
.input-container {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #fff;
  border: 1.5px solid var(--border);
  border-radius: 30px;
  padding: 6px 12px 6px 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,.07);
  transition: all 0.2s;
}
.input-container:focus-within {
  border-color: var(--teal);
  box-shadow: 0 0 0 4px rgba(26,107,107,0.1);
}
#smi-input {
  flex: 1;
  border: none !important;
  outline: none !important;
  background: transparent !important;
  font-size: 0.95rem;
  color: var(--text);
  padding: 10px 0 !important;
  font-family: 'DM Sans', sans-serif;
}
#smi-input::placeholder { color: var(--text3); }
.input-actions { display: flex; align-items: center; gap: 8px; }
.icon-btn {
  width: 36px; height: 36px; border-radius: 50%; border: none;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: all 0.2s; background: transparent; color: var(--text2);
}
.icon-btn:hover { background: var(--sf2); color: var(--teal); }
.icon-btn.active { background: #DC2626; color: #fff; animation: pulse 1.5s infinite; }
.voice-btn {
  background: var(--sf2); color: var(--teal); border: none; border-radius: 20px;
  padding: 6px 14px; font-weight: 600; font-size: 0.82rem; cursor: pointer;
  transition: all 0.2s; display: flex; align-items: center; gap: 6px;
}
.voice-btn:hover { background: var(--teal-l); }
.voice-btn.active { background: #DC2626; color: #fff; }
.send-btn {
  background: var(--teal); color: #fff; width: 36px; height: 36px; border-radius: 50%;
  border: none; display: flex; align-items: center; justify-content: center;
  cursor: pointer; box-shadow: 0 2px 8px rgba(26,107,107,0.25);
}
.send-btn:hover { background: var(--teal-d); transform: scale(1.05); }
@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(220, 38, 38, 0); }
  100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }
}
</style>
<div class="input-container">
  <input id="smi-input" type="text" placeholder="Ask anything..." onkeydown="if(event.key==='Enter') doSend();" />
  <div class="input-actions">
    <button id="smi-mic" class="icon-btn" onclick="toggleVoice()" title="Voice Input">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>
    </button>
    <button id="smi-voice-btn" class="voice-btn" onclick="toggleVoice()">
      <span id="voice-text">Voice</span>
    </button>
    <button id="smi-send" class="send-btn" onclick="doSend()" title="Send Message">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
    </button>
  </div>
</div>

<script>
var recognition;
var isListening = false;

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = 'en-IN';

  recognition.onstart = function() { isListening = true; updateUI(true); };
  recognition.onresult = function(event) {
    var final_transcript = '';
    var interim_transcript = '';
    for (var i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) final_transcript += event.results[i][0].transcript;
      else interim_transcript += event.results[i][0].transcript;
    }
    var inp = document.getElementById('smi-input');
    if (final_transcript) inp.value += (inp.value ? ' ' : '') + final_transcript;
    if (interim_transcript) inp.placeholder = 'Heard: ' + interim_transcript + '...';
  };
  recognition.onerror = function(event) { stopListening(); };
  recognition.onend = function() { isListening = false; updateUI(false); };
}

function toggleVoice() {
  if (!recognition) return alert('Speech API not supported.');
  isListening ? stopListening() : startListening();
}
function startListening() { try { recognition.start(); } catch(e){} }
function stopListening() { recognition.stop(); }

function updateUI(active) {
  document.getElementById('smi-mic').classList.toggle('active', active);
  document.getElementById('smi-voice-btn').classList.toggle('active', active);
  document.getElementById('voice-text').textContent = active ? 'Listening...' : 'Voice';
  document.getElementById('smi-input').placeholder = active ? 'Listening...' : 'Ask anything...';
}

function doSend() {
  var v = document.getElementById('smi-input').value.trim();
  if (!v) return;
  if (isListening) stopListening();
  
  // Post message to parent (main Streamlit window)
  window.parent.postMessage({type:'smi_msg_trigger', val: v}, '*');
  
  document.getElementById('smi-input').value = '';
}

</script>
"""

# ══════════════════════════════════════════════════════════════
#  PAGES
# ══════════════════════════════════════════════════════════════

# ── LANDING ───────────────────────────────────────────────────
if st.session_state.page == "landing":
    st.markdown("""
    <div class="hero">
      <div class="hero-ey">VDart · Internal AI Tool</div>
      <div class="hero-title">🎙️ CommBot</div>
      <div class="hero-sub">Your personal AI English communication coach.<br>
      Practice by role · Speak or type · Tamil understood · Track your growth daily.</div>
    </div>
    """, unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns(4)
    for col,ic,ti,de in zip([c1,c2,c3,c4],
        ["🎭","🇮🇳","🎙️","📈"],
        ["Role Scenarios","Tamil Support","Live Mic","Progress Tracking"],
        ["Tailored to your VDart role","Type Tamil, learn English","Speak directly — no uploads","Scores, streaks & history"]):
        col.markdown(f"""
        <div class="role-card">
          <div style="font-size:2rem;margin-bottom:8px;">{ic}</div>
          <div style="font-weight:700;font-size:.9rem;">{ti}</div>
          <div style="font-size:.77rem;color:#A8A29E;margin-top:4px;">{de}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    ca, cb, _ = st.columns([1,1,2])
    with ca:
        if st.button("🚀 Start Practicing", use_container_width=True):
            st.session_state.page = "setup" if not st.session_state.employee_id else "chat"; st.rerun()
    with cb:
        if st.button("📊 My Progress", use_container_width=True):
            st.session_state.page = "progress"; st.rerun()

    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.markdown("### 🎯 Supported Roles at VDart")
    rcols = st.columns(3)
    for i,(rn,rd2) in enumerate(ROLES.items()):
        with rcols[i%3]:
            st.markdown(f"""
            <div class="role-card" style="text-align:left;border-left:4px solid #1A6B6B;margin-bottom:12px;padding:14px 16px;">
              <div style="font-size:1.5rem;">{rd2["icon"]}</div>
              <div style="font-weight:700;font-size:.88rem;margin-top:4px;">{rn}</div>
              <div style="font-size:.76rem;color:#A8A29E;">{rd2["description"]}</div>
            </div>""", unsafe_allow_html=True)

# ── SETUP ─────────────────────────────────────────────────────
elif st.session_state.page == "setup":
    st.markdown("## 👋 Create Your Profile")
    st.markdown('<div class="card card-teal" style="margin-bottom:20px;font-size:.9rem;">Tell us about yourself so CommBot can personalise your English practice journey at VDart.</div>', unsafe_allow_html=True)
    with st.form("sf"):
        c1,c2 = st.columns(2)
        with c1: name = st.text_input("📛 Full Name", placeholder="e.g. Priya Rajan")
        with c2: role = st.selectbox("💼 Your Role at VDart", list(ROLES.keys()))
        c3,c4 = st.columns(2)
        with c3: tdays = st.slider("🎯 Target Days", 7, 90, 30)
        with c4: dmins = st.slider("⏱️ Minutes/Day", 10, 60, 20)
        existing = get_all_employees()
        sel = "— Create new profile —"
        if existing:
            st.markdown("---"); st.markdown("**↩️ Or return as existing employee:**")
            opts = ["— Create new profile —"] + [f"{e['name']} ({e['role']})" for e in existing]
            sel = st.selectbox("Return as existing employee", opts, label_visibility="collapsed")

        if st.form_submit_button("✅ Start My Journey", use_container_width=True):
            if sel != "— Create new profile —" and existing:
                st.session_state.employee_id = existing[opts.index(sel)-1]["id"]
            elif name.strip():
                st.session_state.employee_id = create_employee(name.strip(), role, tdays, dmins)
            else:
                st.error("Please enter your name!"); st.stop()
            st.session_state.page = "chat"; st.rerun()
    if role:
        rd3 = ROLES.get(role, {})
        st.markdown(f"<br>**Scenarios for {rd3.get('icon','')} {role}:**", unsafe_allow_html=True)
        for sc in rd3.get("scenarios",[]): st.markdown(f"<span class='chip'>{sc}</span>", unsafe_allow_html=True)

# ── CHAT ──────────────────────────────────────────────────────
elif st.session_state.page == "chat":
    if not st.session_state.employee_id:
        st.session_state.page = "setup"; st.rerun()
    emp = get_employee(st.session_state.employee_id)
    rd  = ROLES.get(emp["role"], ROLES["Custom / Other Role"])

    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:14px;margin-bottom:20px;">
      <div style="font-size:2.6rem;">{rd["icon"]}</div>
      <div>
        <div style="font-family:'DM Serif Display',serif;font-size:1.3rem;">{emp["name"]}</div>
        <div style="color:#1A6B6B;font-size:.85rem;font-weight:600;">{emp["role"]}</div>
        <div style="color:#A8A29E;font-size:.77rem;">{emp["total_sessions"]} sessions · 🔥 {emp["streak"]} streak</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["💬 Practice Chat", "🗺️ My Roadmap"])

    with tab1:
        if not st.session_state.session_active:
            st.markdown("### 🎭 Choose Today's Scenario")
            scols = st.columns(4)
            for i, sc in enumerate(rd["scenarios"]):
                with scols[i%4]:
                    if st.button(sc, key=f"sc{i}", use_container_width=True):
                        st.session_state.current_scenario = sc
                        st.session_state.messages = []
                        st.session_state.session_id = start_session(emp["id"], sc)
                        st.session_state.session_active = True
                        st.session_state.session_start_time = time.time()
                        sp = get_system_prompt(emp["role"],emp["target_days"],emp["daily_minutes"],emp["total_sessions"]+1,sc)
                        with st.spinner("CommBot is getting ready..."):
                            opening = chat_with_groq([], sp)
                        st.session_state.messages.append({"role":"assistant","content":opening})
                        save_message(emp["id"], st.session_state.session_id, "assistant", opening)
                        if st.session_state.tts_on: speak(opening)
                        st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🎲 Surprise Me!"):
                sc = random.choice(rd["scenarios"])
                st.session_state.current_scenario = sc
                st.session_state.messages = []
                st.session_state.session_id = start_session(emp["id"], sc)
                st.session_state.session_active = True
                st.session_state.session_start_time = time.time()
                sp = get_system_prompt(emp["role"],emp["target_days"],emp["daily_minutes"],emp["total_sessions"]+1,sc)
                with st.spinner("CommBot is getting ready..."):
                    opening = chat_with_groq([], sp)
                st.session_state.messages.append({"role":"assistant","content":opening})
                save_message(emp["id"], st.session_state.session_id, "assistant", opening)
                if st.session_state.tts_on: speak(opening)
                st.rerun()
        else:
            scenario = st.session_state.current_scenario
            st.markdown(f'<div class="card card-teal" style="padding:11px 18px;margin-bottom:14px;font-size:.86rem;">🎭 <b>Scenario:</b> {scenario} &nbsp;·&nbsp; Session #{emp["total_sessions"]+1}</div>', unsafe_allow_html=True)

            for msg in st.session_state.messages:
                if msg["role"]=="user":
                    st.markdown(f'<div class="b-user"><div class="b-lbl" style="color:rgba(255,255,255,.55);">YOU</div>{msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="b-bot"><div class="b-lbl" style="color:#1A6B6B;">🤖 COMMBOT</div>{msg["content"]}</div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Native Chat Input (Guaranteed Visibility & Enter key support)
            prompt = st.chat_input("Ask CommBot anything...")
            if prompt:
                send_message(prompt, emp, scenario)




            if st.session_state.pending_text:
                t = st.session_state.pending_text; st.session_state.pending_text = ""
                send_message(t, emp, scenario, "🎙️ ")

            st.markdown("<br>", unsafe_allow_html=True)
            ec1, ec2, _ = st.columns([1,1,3])
            with ec1:
                if st.button("✅ End Session", use_container_width=True):
                    dur = max(1, int((time.time()-st.session_state.session_start_time)/60))
                    avg = sum(st.session_state.session_scores)/len(st.session_state.session_scores) if st.session_state.session_scores else 7.0
                    end_session(emp["id"],st.session_state.session_id,avg,dur,len(st.session_state.messages))
                    st.session_state.session_active=False; st.session_state.session_scores=[]; st.session_state.messages=[]
                    st.success(f"🎉 Done! Score: {avg:.1f}/10"); time.sleep(1.5); st.rerun()
            with ec2:
                if st.button("🔄 New Scenario", use_container_width=True):
                    st.session_state.session_active=False; st.session_state.messages=[]; st.session_state.session_scores=[]; st.rerun()

    with tab2:
        st.markdown("### 🗺️ Your Learning Roadmap")
        if st.button("📋 Generate My Roadmap"):
            with st.spinner("Building your plan..."):
                rm = generate_roadmap(emp["role"],emp["target_days"],emp["daily_minutes"],rd["scenarios"])
            st.markdown(f'<div class="card" style="white-space:pre-wrap;line-height:1.8;">{rm}</div>', unsafe_allow_html=True)
        pct = min(100,(emp["total_sessions"]/max(1,emp["target_days"]))*100)
        st.markdown(f"""<br>
        <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
          <span style="font-weight:600;font-size:.88rem;">Goal Progress</span>
          <span style="color:#1A6B6B;font-weight:600;">{emp["total_sessions"]}/{emp["target_days"]} sessions</span>
        </div>
        <div class="prog-bg"><div class="prog-fill" style="width:{pct}%;"></div></div>
        <br><b>🎯 Focus Areas:</b><br>{''.join(f'<span class="chip">✓ {a}</span>' for a in rd["focus_areas"])}
        """, unsafe_allow_html=True)

# ── HISTORY ───────────────────────────────────────────────────
elif st.session_state.page == "history":
    sid = st.session_state.view_session_id
    if not sid: st.session_state.page="chat"; st.rerun()
    msgs = get_session_messages(sid)
    info = {}
    if st.session_state.employee_id:
        ah = get_session_history(st.session_state.employee_id)
        info = next((h for h in ah if h["id"]==sid), {})
    st.markdown("## 💬 Chat History")
    dl = (info.get("date") or "")[:10]
    sl = f"· Score: {info.get('score')}/10" if info.get("score") else ""
    st.markdown(f'<div class="card card-teal" style="padding:11px 18px;margin-bottom:18px;font-size:.86rem;">🎭 <b>{info.get("scenario","Past Session")}</b> &nbsp;·&nbsp; {dl} {sl}</div>', unsafe_allow_html=True)
    for msg in msgs:
        if msg["role"]=="user":
            st.markdown(f'<div class="b-user"><div class="b-lbl" style="color:rgba(255,255,255,.55);">YOU</div>{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="b-bot"><div class="b-lbl" style="color:#1A6B6B;">🤖 COMMBOT</div>{msg["content"]}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Back to Practice"): st.session_state.page="chat"; st.rerun()

# ── PROGRESS ──────────────────────────────────────────────────
elif st.session_state.page == "progress":
    if not st.session_state.employee_id:
        st.warning("Please create a profile first.")
        if st.button("→ Create Profile"): st.session_state.page="setup"; st.rerun()
        st.stop()
    emp  = get_employee(st.session_state.employee_id)
    avg  = get_avg_score(st.session_state.employee_id)
    hist = get_session_history(st.session_state.employee_id)
    pct  = min(100,(emp["total_sessions"]/max(1,emp["target_days"]))*100)
    st.markdown(f"""
    <div class="hero" style="padding:26px 36px;margin-bottom:22px;">
      <div class="hero-ey">Progress Dashboard</div>
      <div class="hero-title" style="font-size:1.7rem;">Welcome back, {emp["name"]} 👋</div>
      <div class="hero-sub">{emp["role"]} · {emp["target_days"]}-day goal · {emp["daily_minutes"]} min/day</div>
    </div>""", unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    for col,val,lbl in zip([c1,c2,c3,c4],
        [str(emp["total_sessions"]),f"{avg}/10",f"🔥 {emp['streak']}",f"{int(pct)}%"],
        ["Total Sessions","Avg Score","Day Streak","Goal Progress"]):
        col.markdown(f'<div class="metric"><div class="metric-val">{val}</div><div class="metric-lbl">{lbl}</div></div>', unsafe_allow_html=True)
    st.markdown(f"""<br>
    <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
      <b>{emp["target_days"]}-Day Goal</b>
      <span style="color:#1A6B6B;font-weight:600;">{int(pct)}% complete</span>
    </div>
    <div class="prog-bg" style="height:14px;"><div class="prog-fill" style="width:{pct}%;"></div></div>""", unsafe_allow_html=True)
    sc_data=[h["score"] for h in reversed(hist) if h["score"]]
    if len(sc_data)>1:
        st.markdown("<br>### 📈 Score Trend")
        import pandas as pd
        st.line_chart(pd.DataFrame({"Score":sc_data}, index=[f"S{h['session']}" for h in reversed(hist) if h["score"]]))
    st.markdown("<br>### 📋 Session History")
    if hist:
        for h in hist:
            sc=h["score"] or 0
            c="#059669" if sc>=7 else "#D97706" if sc>=5 else "#DC2626"
            ds=(h["date"] or "")[:10]
            st.markdown(f'<div class="card" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;padding:14px 20px;"><div><div style="font-weight:700;font-size:.92rem;">Session #{h["session"]} · {h["scenario"] or "Practice"}</div><div style="font-size:.77rem;color:#A8A29E;">{ds} · {h["messages"] or 0} exchanges · {h["duration"] or 0} min</div></div><div style="font-family:\'DM Mono\',monospace;font-size:1.4rem;font-weight:500;color:{c};">{h["score"] or "—"}/10</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="card card-teal">No sessions yet — start your first practice! 🚀</div>', unsafe_allow_html=True)
