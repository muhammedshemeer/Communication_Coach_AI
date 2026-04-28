# 🎙️ SpeakSync AI - Communication Coach

SpeakSync AI is a professional AI-driven communication trainer designed to help employees improve their verbal skills, tone, and professional mindset through real-time roleplay scenarios.

![CommBot Preview](https://img.shields.io/badge/Status-Beta-brightgreen)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red)

## 🚀 Key Features

- **AI Roleplay Scenarios**: Practice handling angry clients, technical support, and internal briefings.
- **Real-time Feedback**: AI-powered coaching on verbal communication, tone, body language, and mindset.
- **Premium UI/UX**: Modern ChatGPT-style interface with a clean white theme.
- **Progress Tracking**: Track your daily streaks, session scores, and learning roadmaps.
- **Voice Synthesis**: Hear AI responses for a more immersive training experience.

## 🛠️ Technology Stack

- **Frontend**: Streamlit (Python)
- **AI Engine**: Groq (Llama 3.3 70B Model)
- **Database**: SQLite
- **Voice**: gTTS (Google Text-to-Speech)

## 📋 Prerequisites

- Python 3.9 or higher
- A Groq API Key (Get it at [console.groq.com](https://console.groq.com/))

## ⚙️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/[YOUR_USERNAME]/vdart_chatbot.git
   cd vdart_chatbot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Environment Variables**:
   Create a system environment variable or a `.env` file with your Groq API key:
   ```bash
   export GROQ_API_KEY="your_api_key_here"
   ```

## 🚀 Running the App

```bash
streamlit run app.py
```

## 📂 Project Structure

- `app.py`: Main Streamlit application and UI logic.
- `chatbot/`:
  - `groq_client.py`: Groq API integration and AI logic.
  - `role_prompts.py`: AI coaching and roleplay system prompts.
- `database/`:
  - `db.py`: SQLite persistence layer for profiles and history.
- `assets/`: UI assets and styling.

## 🤝 Contributing

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---
Developed for **VDart Intern Project**.
