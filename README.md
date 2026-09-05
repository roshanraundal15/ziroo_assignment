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
copy .env.example .env
# Mac/Linux:
# cp .env.example .env

Open backend/.env and add one key:
BashGROQ_API_KEY=your_key_here
You can also use:
BashOPENAI_API_KEY=your_key_here
or
BashGEMINI_API_KEY=your_key_here
Then run:
Bashuvicorn main:app --reload --port 8000
2. Frontend
Bashcd frontend
npm install
npm run dev
Open:
texthttp://127.0.0.1:5173
By default, the frontend uses the Vite /ws proxy to talk to the backend.
If your WebSocket server is somewhere else, you can set:
BashVITE_WS_URL=ws://127.0.0.1:8000/ws
The room code is appended to that URL.

How to test with two users
This is the main way to check the assignment.

Open the app in two browser tabs
Use the same room code in both, for example demo
Use different names
Chat normally first
In tab A write:text@agent summarize what we talked about
In tab B write:text@agent what should I do next?

What should happen:

both users see each other’s normal chat
each @agent question gets its own reply
A’s answer should stay based on A’s context
B’s answer should stay based on B’s context
A’s details should not leak into B’s answer

That isolation test is the core of the assignment.

How context isolation works
This is the most important design choice in the project.
Shared room
Every human message is saved to the shared room.
That means both users can see the full conversation.
Private agent memory
Separately, each message is also stored in a per-user agent memory.
That memory is keyed by:
text(room_id, user_id)
When someone asks the agent
If User A writes @agent ...:

the system takes only User A’s memory
builds the prompt from that memory
calls the model once
posts the reply in the shared room
marks the reply as “replying to A”
saves that reply back into A’s memory for follow-up questions

User B’s messages are not added to User A’s prompt.
Why this design:
the room can stay open and shared,
but the agent still treats each person as a separate thread.

Persistence
Messages are stored in SQLite:
textbackend/rooms.db
Why SQLite:

simple setup
no extra service
good enough for local demo
history survives a server restart

If you restart the backend and join the same room code again, the previous messages should load back.
I did not move to Postgres for this assignment because the goal was a working local system, not production infrastructure.

Environment variables
Never commit real keys.
Use backend/.env only on your machine.

























VariablePurposeGROQ_API_KEYGroq chat APIOPENAI_API_KEYOpenAI chat APIGEMINI_API_KEYGoogle GeminiLLM_PROVIDEROptional force: groq / openai / gemini
If no key is set, the agent still replies with a clear mock message.
That way the UI and room flow can still be tested without a live model key.

Project layout
textbackend/
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

Design choices in short
1. One model call only
I call the model only when a message starts with @agent.
No call on every keystroke.
No multi-step pipeline.
Reason:
the brief said keep the AI call cheap and judge the system around the call, not the quality of the model answer.
2. Concurrent users
Both users can type at the same time.
Chat is not blocked by a slow model call.
Agent work runs in the background.
Reason:
a shared room should still feel live even when the agent is thinking.
3. Failure handling
If the model is slow, fails, or is missing:

the room does not crash
the agent posts a clear message
the other user can keep chatting

Reason:
real systems fail, so the room should degrade safely.
4. Simple persistence
SQLite for message history.
Enough for this assignment.
Reason:
easy to run, easy to understand, and restart-safe.

Timebox note
I built this to stay inside a 5 to 6 hour scope.
What I focused on:

context isolation
live shared room
safe agent calls
clear UI states
simple local setup

What I did not overbuild:

auth
multi-server scaling
complex agent tools
heavy infrastructure

Those can be useful later, but they were not the main test of this assignment.
For more detail on what I tested, what I assumed, and what I would improve next, see NOTES.md.
