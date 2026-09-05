# Ziroo Assignment — Multiplayer Room with an AI Participant

This project is a shared chat room with an AI teammate inside it.

Two people can join the same room, talk at the same time, and both can ask the same agent.
The important part is that the agent should still answer the right person with the right context.

In simple words:

- the room is shared
- the agent memory is not shared

That is the main idea of this assignment.

---

## What this app does

1. Two users join with a name and a room code
2. They can chat live in the same room
3. An AI agent sits in the room as a third participant
4. The agent only replies when someone writes `@agent ...`
5. Each user keeps a separate context for the agent
6. Messages are saved so history can come back after restart

This is a smaller version of a real team room problem:
people talk in one place, but the AI should not mix their workstreams.

---

## Stack

- **Backend:** Python, FastAPI, WebSockets, SQLite
- **Frontend:** React + TypeScript (Vite)
- **LLM:** Groq / OpenAI / Gemini
  - use whichever key you already have
  - put it in `.env`
  - do not send your key to anyone

---

## Why I chose WebSockets

I needed live communication in both directions:

- user sends a message
- other user sees it immediately
- agent typing state appears
- agent reply appears

For only two users, WebSockets were the simplest option that felt like a real chat room.

Why not the other options:

- **Polling:** works, but feels laggy for chat
- **SSE:** mostly server to client, while chat needs both directions
- **Heavy multiplayer setup:** not needed for this assignment

The brief said we do not need a scalable multiplayer server.
So I kept the transport simple on purpose.

---


## Setup

### 1. Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # Mac/Linux
```

Edit `backend/.env` and add **one** key:

```
GROQ_API_KEY=your_key_here
```

(or `OPENAI_API_KEY` / `GEMINI_API_KEY`)

Run:

```bash
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173

The frontend uses the Vite `/ws` proxy by default. Set `VITE_WS_URL` when the WebSocket server lives elsewhere; the room code is appended to that URL.

### 3. Test with two users

1. Open the app in **two browser tabs**
2. Same room code in both (example: `demo`)
3. Different names
4. Chat normally
5. In tab A: `@agent summarize what we talked about`
6. In tab B, quickly: `@agent what should I do next?`

You should see two separate agent answers. A’s context should not leak into B’s reply.

## How context isolation works

- Every human message is saved to the **shared room** (everyone can see it)
- Separately, each message is also appended to a **per-user agent memory** keyed by `(room_id, user_id)`
- When user A triggers `@agent`, the LLM prompt is built **only** from A’s memory
- User B’s messages are never included in A’s prompt
- The agent reply is broadcast to the room, tagged as “replying to A”, and stored back into A’s memory so follow-ups work

This is the main thing the assignment is testing.

## Persistence

Messages are stored in SQLite (`backend/rooms.db`). If you restart the server and rejoin the same room code, history comes back.

## Environment variables

Never commit real keys. Use `backend/.env` locally.

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Groq chat API |
| `OPENAI_API_KEY` | OpenAI chat API |
| `GEMINI_API_KEY` | Google Gemini |
| `LLM_PROVIDER` | Optional force: `groq` / `openai` / `gemini` |

If no key is set, the agent still responds with a clear mock message so the room UI stays testable.

## Project layout

```
backend/
  main.py      # WebSocket room + agent orchestration
  llm.py       # one LLM call, timeouts, error strings
  db.py        # SQLite save/load
  requirements.txt
  .env.example
frontend/
  src/App.tsx  # protocol-preserving room state
  src/components/  # join, room header, messages, composer
  src/styles.css
README.md
NOTES.md
```

## Timebox note

Built to stay inside a ~5–6 hour scope: working room, live messages, agent participant, isolation, persistence, and a usable UI. See `NOTES.md` for tradeoffs and what I would improve next.
