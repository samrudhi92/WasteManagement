"""
EcoBot - Memory-Based Waste Management Chatbot
-------------------------------------------------
Flask + Ollama (llama3.2:latest) powered chatbot that remembers past
conversation turns (stored in db.sqlite) and answers questions about
waste types, recycling details, and eco-friendly recommendations,
grounded in data.json.

Prerequisites:
    1. Install Ollama:        https://ollama.com
    2. Pull the model:        ollama pull llama3.2:latest
    3. Make sure Ollama is running (http://localhost:11434 by default)
    4. Install python deps:   pip install flask requests

Run:
    python app.py
    Then open http://127.0.0.1:5000 in your browser.
"""

import json
import os
import sqlite3
import uuid
import requests
from flask import Flask, render_template, request, jsonify, session

app = Flask(__name__)
app.secret_key = "ecobot-secret-key-change-in-production"

# ---------- Configuration ----------
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:latest"
BASE_DIR = os.path.dirname(__file__)
DATA_FILE = os.path.join(BASE_DIR, "data.json")
DB_FILE = os.path.join(BASE_DIR, "db.sqlite")
MEMORY_TURNS = 6  # number of past user+bot turns to recall for context


# ---------- Database setup (chat memory) ----------
def init_db():
    """Create the conversations table if it doesn't already exist."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,          -- 'user' or 'bot'
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_message(session_id, role, message):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO conversations (session_id, role, message) VALUES (?, ?, ?)",
        (session_id, role, message)
    )
    conn.commit()
    conn.close()


def get_recent_history(session_id, limit=MEMORY_TURNS * 2):
    """Fetch the most recent messages for this session, oldest first."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "SELECT role, message FROM conversations WHERE session_id = ? "
        "ORDER BY id DESC LIMIT ?",
        (session_id, limit)
    )
    rows = cur.fetchall()
    conn.close()
    rows.reverse()  # oldest first
    return rows


def clear_history(session_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()


# ---------- Load knowledge base ----------
def load_knowledge_base():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


KNOWLEDGE_BASE = load_knowledge_base()


def build_system_prompt():
    kb_text = json.dumps(KNOWLEDGE_BASE, indent=2)
    return f"""You are EcoBot, a friendly waste management assistant chatbot.
Use the WASTE MANAGEMENT DATA below as your primary source of truth to answer questions
about waste types, descriptions, recycling details, disposal recommendations, and
eco-friendly suggestions. If something isn't covered in the data, use general
sustainability best practices to still give a helpful answer.

Keep answers concise, practical, and encouraging. Use simple language.

WASTE MANAGEMENT DATA (JSON):
{kb_text}
"""


SYSTEM_PROMPT = build_system_prompt()


def build_conversation_prompt(history_rows, user_message):
    """Builds the full prompt including system context + remembered history."""
    convo_text = ""
    for role, message in history_rows:
        speaker = "User" if role == "user" else "EcoBot"
        convo_text += f"{speaker}: {message}\n"

    full_prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Conversation so far:\n{convo_text}\n"
        f"User: {user_message}\n"
        f"EcoBot:"
    )
    return full_prompt


# ---------- Routes ----------
@app.route("/")
def index():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return render_template("index.html", assistant_name=KNOWLEDGE_BASE.get("assistant_name", "EcoBot"))


@app.route("/chat", methods=["POST"])
def chat():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    session_id = session["session_id"]

    user_message = request.json.get("message", "").strip()
    if not user_message:
        return jsonify({"reply": "Please type a question about waste management or recycling."})

    # Recall memory (past turns) for this session
    history_rows = get_recent_history(session_id)

    # Save the user's message to memory
    save_message(session_id, "user", user_message)

    full_prompt = build_conversation_prompt(history_rows, user_message)

    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        bot_reply = result.get("response", "Sorry, I could not generate a response.").strip()
    except requests.exceptions.ConnectionError:
        bot_reply = ("⚠️ Could not connect to Ollama. Please make sure Ollama is running "
                     "locally (run: 'ollama serve') and that the model "
                     f"'{MODEL_NAME}' is pulled (run: 'ollama pull {MODEL_NAME}').")
    except Exception as e:
        bot_reply = f"⚠️ An error occurred while generating a response: {str(e)}"

    # Save the bot's reply to memory
    save_message(session_id, "bot", bot_reply)

    return jsonify({"reply": bot_reply})


@app.route("/reset", methods=["POST"])
def reset():
    """Clears conversation memory for the current session."""
    if "session_id" in session:
        clear_history(session["session_id"])
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
