# Ziroo Assignment — Multiplayer Room with an AI Participant

This project is a shared chat room with an AI teammate inside it.

Two people can join the same room, talk at the same time, and both can ask the same agent. The important part is that the agent should still answer the right person with the right context.

**In simple words:**
- The room is shared (everyone sees all messages)
- The agent memory is not shared (each person has their own context)

That is the main idea of this assignment.

---

## What This App Does

1. Two users join with a name and a room code
2. They can chat live in the same room
3. An AI agent sits in the room as a third participant
4. The agent only replies when someone writes `@agent ...`
5. Each user keeps a separate context for the agent
6. Messages are saved so history comes back after restart

This is a smaller version of a real team room problem: people talk in one place, but the AI should not mix their workstreams.

---

## Stack

- **Backend:** Python, FastAPI, WebSockets, SQLite
- **Frontend:** React + TypeScript (Vite)
- **LLM:** Groq / OpenAI / Gemini
  - Use whichever key you already have
  - Put it in `.env`
  - Do not send your key to anyone

---

## Why WebSockets

I needed live communication in both directions:

- User sends a message → other user sees it immediately
- Agent typing state appears in real-time
- Agent reply appears instantly

For only two users, WebSockets were the simplest option that felt like a real chat room.

**Why not the other options:**
- **Polling:** Works, but feels laggy for chat
- **SSE:** Mostly server → client; chat needs both directions
- **Heavy multiplayer setup:** Not needed for this assignment

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
copy .env.example .env
# Mac/Linux:
# cp .env.example .env
```

Open `backend/.env` and add one key:

```
GROQ_API_KEY=your_key_here
```

Or use:

```
OPENAI_API_KEY=your_key_here
```

Or:

```
GEMINI_API_KEY=your_key_here
```

Then run:

```bash
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open your browser:

```
http://127.0.0.1:5173
```

By default, the frontend uses the Vite `/ws` proxy to talk to the backend.

If your WebSocket server is somewhere else, set:

```
VITE_WS_URL=ws://127.0.0.1:8000/ws
```

The room code is appended to that URL.

---

## How to Test with Two Users

This is the main way to check the assignment.

1. Open the app in **two browser tabs**
2. Use the **same room code** in both (example: `demo`)
3. Use **different names**
4. Chat normally first
5. In **tab A** write:
   ```
   @agent summarize what we talked about
   ```
6. In **tab B** write:
   ```
   @agent what should I do next?
   ```

**What should happen:**
- Both users see each other's normal chat
- Each `@agent` question gets its own reply
- A's answer stays based on A's context
- B's answer stays based on B's context
- A's details do **not** leak into B's answer

That isolation test is the core of the assignment.

---

## How Context Isolation Works

This is the most important design choice in the project.

### Shared Room

Every human message is saved to the shared room. That means both users can see the full conversation.

### Private Agent Memory

Separately, each message is also stored in a per-user agent memory. That memory is keyed by `(room_id, user_id)`.

### When Someone Asks the Agent

If User A writes `@agent ...`:

1. The system takes **only User A's memory**
2. Builds the prompt from that memory
3. Calls the model once
4. Posts the reply in the shared room
5. Marks the reply as "replying to A"
6. Saves that reply back into A's memory for follow-up questions

**User B's messages are not added to User A's prompt.**

### Why This Design

- The room can stay open and shared
- The agent still treats each person as a separate thread
- No cross-talk between users

---

## Persistence

Messages are stored in SQLite:

```
backend/rooms.db
```

**Why SQLite:**
- Simple setup
- No extra service
- Good enough for local demo
- History survives a server restart

If you restart the backend and join the same room code again, the previous messages should load back.

I did not move to Postgres for this assignment because the goal was a working local system, not production infrastructure.

---

## Environment Variables

Never commit real keys. Use `backend/.env` only on your machine.

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Groq chat API |
| `OPENAI_API_KEY` | OpenAI chat API |
| `GEMINI_API_KEY` | Google Gemini |
| `LLM_PROVIDER` | Optional force: `groq` / `openai` / `gemini` |

If no key is set, the agent still replies with a clear mock message. That way the UI and room flow can still be tested without a live model key.

---

## Project Layout

```
backend/
  main.py            # room + websocket + agent flow
  llm.py             # one model call, timeout and error handling
  db.py              # sqlite save/load
  requirements.txt
  .env.example

frontend/
  src/App.tsx
  src/components/    # join screen, header, messages, composer
  src/styles.css

README.md
NOTES.md
```

---

## Design Choices in Short

### 1. One Model Call Only

I call the model only when a message starts with `@agent`. No call on every keystroke. No multi-step pipeline.

**Reason:** The brief said keep the AI call cheap and judge the system around the call, not the quality of the model answer.

### 2. Concurrent Users

Both users can type at the same time. Chat is not blocked by a slow model call. Agent work runs in the background.

**Reason:** A shared room should still feel live even when the agent is thinking.

### 3. Failure Handling

If the model is slow, fails, or is missing:
- The room does not crash
- The agent posts a clear message
- The other user can keep chatting

**Reason:** Real systems fail, so the room should degrade safely.

### 4. Simple Persistence

SQLite for message history. Enough for this assignment.

**Reason:** Easy to run, easy to understand, and restart-safe.

---

## Timebox Note

I built this to stay inside a 5–6 hour scope.

**What I focused on:**
- Context isolation
- Live shared room
- Safe agent calls
- Clear UI states
- Simple local setup

**What I did not overbuild:**
- Auth
- Multi-server scaling
- Complex agent tools
- Heavy infrastructure

Those can be useful later, but they were not the main test of this assignment.

For more detail on what I tested, what I assumed, and what I would improve next, see **NOTES.md**.
