ROLES = {
    "Junior Developer / Fresher": {
        "icon": "💻",
        "color": "#00D4FF",
        "description": "Build confidence in technical communication",
        "scenarios": [
            "Daily standup meeting",
            "Explaining a bug to your senior",
            "Asking for help from a teammate",
            "Writing a professional email to your manager",
            "Introducing yourself in a team meeting",
            "Discussing project progress",
            "Code review conversation",
            "Client requirement clarification",
        ],
        "focus_areas": ["Technical vocabulary", "Standup communication", "Email writing", "Asking questions politely"],
    },
    "HR / Recruiter": {
        "icon": "🤝",
        "color": "#FF6B9D",
        "description": "Professional HR communication and interviewing",
        "scenarios": [
            "Conducting a job interview",
            "Explaining company policies",
            "Giving offer letter call",
            "Handling employee grievances",
            "Onboarding a new employee",
            "Rejection call with candidates",
            "Salary negotiation conversation",
            "Reference check call",
        ],
        "focus_areas": ["Interview language", "Empathetic communication", "Policy explanation", "Professional calls"],
    },
    "Sales / Business Development": {
        "icon": "📈",
        "color": "#FFB347",
        "description": "Persuasive client communication and pitching",
        "scenarios": [
            "Client pitch presentation",
            "Cold call introduction",
            "Handling client objections",
            "Follow-up email after meeting",
            "Contract negotiation",
            "Client relationship building",
            "Explaining service offerings",
            "Closing a deal conversation",
        ],
        "focus_areas": ["Persuasive language", "Client handling", "Negotiation phrases", "Professional pitching"],
    },
    "Manager / Team Lead": {
        "icon": "🎯",
        "color": "#7C83FD",
        "description": "Leadership and team communication excellence",
        "scenarios": [
            "Giving feedback to a team member",
            "Running a project status meeting",
            "Escalation call with senior management",
            "Motivating the team during pressure",
            "Handling a conflict between team members",
            "Presenting project roadmap",
            "Performance review conversation",
            "Delegating tasks clearly",
        ],
        "focus_areas": ["Leadership vocabulary", "Constructive feedback", "Presentation skills", "Conflict resolution"],
    },
    "Support / Operations": {
        "icon": "🛠️",
        "color": "#56CFE1",
        "description": "Clear, calm, and helpful customer communication",
        "scenarios": [
            "Handling an angry client call",
            "Explaining technical issues simply",
            "Escalating an unresolved issue",
            "Writing a support ticket response",
            "Following up on a complaint",
            "Communicating downtime to stakeholders",
            "Training a new support member",
            "SLA breach explanation call",
        ],
        "focus_areas": ["Calm communication", "Technical simplification", "Complaint handling", "Professional emails"],
    },
    "Custom / Other Role": {
        "icon": "⚙️",
        "color": "#A8EDEA",
        "description": "General professional English communication",
        "scenarios": [
            "Professional self-introduction",
            "Meeting participation",
            "Writing business emails",
            "Phone call etiquette",
            "Presentation skills",
            "Workplace small talk",
            "Asking for clarification",
            "Giving updates to seniors",
        ],
        "focus_areas": ["General business English", "Professional vocabulary", "Email writing", "Spoken confidence"],
    },
}

def get_system_prompt(role: str, target_days: int, daily_minutes: int, session_number: int, scenario: str) -> str:
    role_data = ROLES.get(role, ROLES["Custom / Other Role"])
    difficulty = "beginner" if session_number <= 3 else "intermediate" if session_number <= 8 else "advanced"

    return f"""You are CommBot, an expert English communication coach at VDart — a leading IT staffing and workforce solutions company. You are a supportive mentor and coach.

EMPLOYEE PROFILE:
- Role: {role}
- Learning Goal: Complete in {target_days} days, {daily_minutes} minutes/day  
- Current Session: #{session_number}
- Difficulty Level: {difficulty}
- Today's Practice Scenario: {scenario}

YOUR MISSION:
Transform the user into a confident communicator by providing practical, role-based coaching. For EVERY response, you MUST include the following structured feedback:

1. 🗣️ VERBAL COMMUNICATION (What to say):
   - Provide a clear, professional example sentence or conversation snippet.
   - Adjust the tone based on the role (e.g., Junior = polite/learning, Manager = confident/clear, HR = empathetic/formal).

2. 🎭 TONE & DELIVERY (How to say it):
   - Explain the ideal tone (friendly, respectful, assertive, etc.).
   - Highlight clarity and the required confidence level.

3. 🕴️ BODY LANGUAGE GUIDANCE:
   - Specific advice on posture, eye contact, facial expressions, and gestures relevant to the scenario.

4. 🧠 MINDSET COACHING:
   - Explain how the person should think (e.g., "be open to feedback", "stay confident but respectful").

5. ✏️ GRAMMAR & CORRECTION (If applicable):
   - If the user made a mistake:
     ✏️ "You said: ..."
     ✅ "Better way: ..."
     💡 "Why: ..."

TAMIL SUPPORT:
- If the employee writes in Tamil (தமிழ்), understand it fully. 
- Respond with a brief acknowledgement in Tamil (1 line).
- Provide the English equivalent they should use.

CONVERSATION RULES:
- Keep the overall response simple, practical, and mentor-like.
- Stay in character for the scenario: "{scenario}".
- For {role}, focus on: {', '.join(role_data['focus_areas'])}.
- Keep the practice flow natural. Do not overwhelm — focus on one or two key improvements per exchange.

Begin by warmly greeting the employee, confirming their scenario for today, and starting the role-play naturally."""

