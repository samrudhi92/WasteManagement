
# ♻️ EcoBot - Memory-Based Waste Management Chatbot

A **memory-enabled** AI chatbot built with **Flask**, **SQLite**, and **Ollama (llama3.2:latest)** that helps users learn about waste types, recycling details, and eco-friendly disposal recommendations. Unlike a stateless chatbot, EcoBot **remembers the conversation** using a local SQLite database, so it can hold context-aware, multi-turn conversations.

The chatbot appears as a floating chat icon in the bottom-right corner of a Bootstrap-styled landing page — click it to open the chat window.

---

## 📁 Project Structure

session3/
├── app.py # Flask backend - routes, memory (SQLite), Ollama integration
├── data.json # Knowledge base - waste categories, recycling details, tips
├── db.sqlite # SQLite database storing conversation memory
├── requirements.txt # Python dependencies
├── Procfile # Start command for Render/Heroku-style hosting
├── render.yaml # Render Blueprint deployment config (optional)
└── templates/
└── index.html # Bootstrap-only webpage with floating chatbot widget


---

## ✨ Features

- 💬 **Floating chat widget** — a circular chat icon fixed at the bottom-right of the page; clicking it opens/closes the chat window (via Bootstrap's `collapse` component)
- 🧠 **Conversation memory** — every user and bot message is stored in `db.sqlite` per browser session, and recent turns are recalled and fed back into the model for contextual replies
- 🔄 **Reset memory** — a clear/reset button in the chat header wipes the current session's conversation history
- 🌱 Answers grounded in a structured waste-management knowledge base (`data.json`) covering biodegradable, dry/recyclable, e-waste, hazardous, plastic, and medical waste
- 🎨 **100% Bootstrap styling** — no custom CSS files; only a small inline `<script>` block for AJAX calls to the Flask backend (unavoidable, since Bootstrap alone can't make network requests)
- 🤖 Powered by a **locally hosted** LLM via **Ollama** (`llama3.2:latest`) — no external AI API keys needed
- ☁️ Deployment-ready for **Render** (`requirements.txt`, `Procfile`, `render.yaml` included)

---

## 🛠️ Prerequisites

1. **Python 3.8+**
2. **Ollama** installed → [https://ollama.com](https://ollama.com)
3. The **llama3.2:latest** model pulled locally (or an externally hosted Ollama instance for production)
4. Python packages listed in `requirements.txt`

---

## 🚀 Setup & Installation (Local)

### 1. Install Ollama and pull the model
```bash
ollama pull llama3.2:latest
ollama serve
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Flask application
```bash
cd session3
python app.py
```

### 4. Open the chatbot in your browser

http://127.0.0.1:5000


Click the green chat icon in the bottom-right corner to start chatting with EcoBot.

---

## 💡 How It Works

1. **Session tracking** — When a user visits the page, Flask assigns them a unique `session_id` (stored in a secure cookie).
2. **Memory recall** — On each new message, `app.py` queries `db.sqlite` for the last few turns of that session's conversation.
3. **Prompt construction** — A system prompt (grounded in `data.json`) + the recalled conversation history + the new user message are combined into a single prompt.
4. **Model call** — The prompt is sent to the local Ollama server (`llama3.2:latest`) via its `/api/generate` endpoint.
5. **Memory update** — Both the user's message and the bot's reply are saved back into `db.sqlite`, so future turns stay context-aware.
6. **Reset** — Clicking the reset icon calls `/reset`, which deletes that session's rows from `db.sqlite`.

---

## 🗄️ Database Schema (`db.sqlite`)

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER (PK, autoincrement) | Unique message ID |
| `session_id` | TEXT | Identifies which browser session the message belongs to |
| `role` | TEXT | `'user'` or `'bot'` |
| `message` | TEXT | The message content |
| `timestamp` | DATETIME | Auto-set to the time the message was saved |

The table is auto-created on first run — no manual setup needed.

---

## 📝 Editing the Knowledge Base

All chatbot answers are grounded in `data.json`. To update or expand waste categories, tips, or FAQs, edit `data.json` and restart the app — no code changes required.

Example fields you can update:
- `waste_categories` (type, description, recyclable, recycling_details, disposal_recommendations)
- `general_tips`
- `recommendations`
- `faqs`

---

## 🎨 Styling

The frontend uses **Bootstrap 5** and **Bootstrap Icons** loaded via CDN — no custom `.css` files are used anywhere. Layout, spacing, colors, and the floating widget's positioning are all achieved using Bootstrap utility classes (`position-fixed`, `bottom-0`, `end-0`, `rounded-circle`, etc.). A minimal inline `<script>` block is included only to make the `fetch()` calls to the Flask `/chat` and `/reset` endpoints, since Bootstrap alone cannot perform network requests.

---

## 🔧 Configuration

`app.py` reads the following from environment variables (with local defaults), so the same code works locally and when deployed:

| Variable | Description | Default |
|---|---|---|
| `OLLAMA_URL` | URL of the Ollama API endpoint | `http://localhost:11434/api/generate` |
| `MODEL_NAME` | Ollama model used for generating replies | `llama3.2:latest` |
| `PORT` | Port Flask binds to (used by hosting platforms) | `5000` |

---

## ☁️ Deploying to Render

This project includes `requirements.txt`, `Procfile`, and `render.yaml` for deployment on [Render](https://render.com).

**Steps:**
1. Push the `session3/` folder to a GitHub repository.
2. On Render, create a **New Web Service** and connect your repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Set the `OLLAMA_URL` environment variable to point at your externally hosted Ollama instance.

> ⚠️ **Important:** Render's standard web service cannot run Ollama itself (no local LLM daemon support / no GPU on free tier). You must host Ollama separately (e.g. on a GPU-enabled VM) and point `OLLAMA_URL` at its public address.

---

## 🐞 Troubleshooting

**Chatbot says "Could not connect to Ollama":**
- Ensure Ollama is running: `ollama serve`
- Confirm the model is installed: `ollama list` (should show `llama3.2:latest`)
- If deployed, confirm `OLLAMA_URL` is set correctly and reachable from your hosting environment

**Chat window doesn't open when clicking the icon:**
- Ensure `bootstrap.bundle.min.js` (which includes Popper + the Collapse component) loaded successfully — check the browser console for blocked CDN requests

**Bot doesn't seem to remember earlier messages:**
- Confirm cookies are enabled in your browser (session tracking relies on the Flask session cookie)
- Check that `db.sqlite` is writable in your deployment environment

**Port already in use locally:**
- Change the port: `PORT=5001 python app.py`

---

## 📌 Future Improvements

- Add streaming responses using Ollama's streaming API for a real-time typing effect
- Add persistent user accounts instead of session-based memory
- Add a "download conversation" or "export chat" feature
- Add multilingual support for waste management guidance
- Add image-based waste classification (upload a photo of an item to identify its category)

---

## 📄 License

This project is intended for educational/academic and demonstration use. Feel free to adapt it for community awareness campaigns, municipal websites, or school/college sustainability projects.
