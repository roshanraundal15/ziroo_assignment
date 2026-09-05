# Build Assignment — Multiplayer Room with an Automated Participant

Role: Full Stack Engineering Intern  
Timebox: 5–6 hours (don't exceed this; it's better to cut scope than rush features)

Goal (plain): Build a simple chat room where two people can talk at the same time and there is an automated participant in the room that answers when addressed. The important rule: when the automated participant replies, it only sees the conversation history of the user who addressed it—not the other user's messages.

## What to build
- A shared chat room. Two people join with a name and a room code and see each other's messages live.
- An automated participant that only replies when a message begins with something like `@agent ...`.
- Per-user context. The automated participant must keep each user's context separate so one user's history never affects the other's replies.
- Basic persistence so messages and room state survive a server restart (or document clearly why you didn't persist).
- A simple, usable UI: message list, identity for each user, clear visual difference for automated messages, a "typing" or loading indicator while the automated participant is preparing a reply.

## Minimum technical stack
- Backend: Python + FastAPI + WebSockets
- Frontend: React + TypeScript (Vite)
- Data store: SQLite (simple, local persistence)

## How it should behave (example)
1. Open two browser tabs, join the same room code with different names.
2. Both users type messages and see each other's messages immediately.
3. If Tab A sends `@agent summarize what we talked about`, the automated participant replies using only Tab A's conversation history.
4. If Tab B also asks `@agent ...`, the reply for B uses only B's history. No details from A should appear in B's reply.

## Design notes (what you should defend in the README / NOTES.md)
- Why you picked your transport (WebSockets, SSE, or polling). For two users, pick the simplest that works and explain why.
- How you stored room and per-user memory (what's persisted, keys used, data model).
- How you avoid cross-talk between users (how you build the input for the automated participant so each user stays isolated).
- How you handle concurrency, message ordering, and race conditions (briefly describe any locking, queuing, or timestamp rules).
- How you handle service failures, timeouts, and bad responses — the room must keep working even if a call fails.

## Constraints and expectations
- One call to the external service per addressed message (not on every keystroke).
- Keep the design simple and reliable for two concurrent users — you don't need production-scale multiplayer.
- The app should degrade gracefully if the automated participant is slow or fails (show an error message in the room, keep chat working).
- Two browser tabs are enough to demonstrate correctness — no real authentication needed.

## What reviewers will evaluate (in order)
1. Does the automated participant keep two users' context separate? This is the main test.
2. Backend design: how you modeled rooms/sessions, concurrency choices, and persistence.
3. Integration safety: do you handle slow, malformed, or failed replies defensively?
4. Frontend: interaction states and overall UX (typing state, clear identities, visual separation).
5. Honesty in NOTES.md: what you tested, what you assumed, and what you'd improve with more time.

## Practical notes
- Use whichever external service/key you already have access to and document how to set the key in `.env`.
- Keep calls small during development — a handful of test messages is enough.
- Include a NOTES.md with tradeoffs, tests performed, and next steps.
- The app should run locally with documented setup steps for backend and frontend.

## Submission
- A working repository (or zip) with frontend + backend and setup instructions.
- README with how to run locally and a NOTES.md describing what you tested and what you'd improve.

---

# Installation & Setup Guide

## Prerequisites
- **Python** 3.9 or higher
- **Node.js** 16.x or higher and **npm** (or yarn)
- **SQLite3** (usually pre-installed on macOS/Linux)
- **Git**

## Backend Setup

### 1. Clone the repository
```bash
git clone https://github.com/roshanraundal15/ziroo_assignment.git
cd ziroo_assignment
```

### 2. Create a virtual environment (Python)
```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file in the backend root directory:
```bash
# .env
OPENAI_API_KEY=your_api_key_here
DATABASE_URL=sqlite:///./chat_rooms.db
HOST=127.0.0.1
PORT=8000
```

Replace `your_api_key_here` with your actual API key (e.g., OpenAI, Anthropic, or similar).

### 5. Initialize the database
```bash
python -m backend.db.init
# Or if using Alembic for migrations:
# alembic upgrade head
```

### 6. Start the backend server
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend will be running at `http://127.0.0.1:8000`. WebSocket endpoint: `ws://127.0.0.1:8000/ws`.

## Frontend Setup

### 1. Navigate to the frontend directory
```bash
cd frontend
```

### 2. Install dependencies
```bash
npm install
# or
yarn install
```

### 3. Configure environment variables (if needed)
Create a `.env` file in the `frontend/` directory:
```bash
# .env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### 4. Start the development server
```bash
npm run dev
# or
yarn dev
```

The frontend will typically run at `http://localhost:5173` (Vite default).

## Running Locally

1. **Start the backend** (in one terminal):
   ```bash
   source venv/bin/activate  # or activate on Windows
   uvicorn backend.main:app --reload
   ```

2. **Start the frontend** (in another terminal):
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open two browser tabs**:
   - Tab 1: `http://localhost:5173`
   - Tab 2: `http://localhost:5173` (same URL)

4. **Test the flow**:
   - Enter the same room code in both tabs with different names
   - Send messages and verify they appear in both tabs instantly
   - Send `@agent <your question>` in one tab and check the response uses only that user's context

## Database

The SQLite database is created automatically at `./chat_rooms.db` (or the path specified in `DATABASE_URL`). It persists:
- Rooms and room metadata
- Messages with timestamps and user identifiers
- Per-user conversation history

To reset the database:
```bash
rm chat_rooms.db  # Delete the database file
python -m backend.db.init  # Reinitialize
```

## Troubleshooting

### Port already in use
If port 8000 is already in use:
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload
# Update VITE_WS_URL in frontend/.env to ws://localhost:8001
```

### WebSocket connection fails
- Ensure the backend is running and accessible at the configured URL
- Check that CORS and WebSocket settings are properly configured in `backend/main.py`
- Verify the frontend `.env` has the correct `VITE_WS_URL`

### Missing dependencies
```bash
# Backend
pip install --upgrade pip
pip install -r requirements.txt

# Frontend
npm ci  # Clean install
npm install
```

### Database issues
```bash
# Check database file exists
ls -la chat_rooms.db  # macOS/Linux
dir chat_rooms.db     # Windows

# Reinitialize if corrupted
rm chat_rooms.db
python -m backend.db.init
```

## Development Tips

- **Backend logs**: Check terminal output for WebSocket connection details and agent calls
- **Frontend DevTools**: Use React DevTools and browser Network tab to debug WebSocket messages
- **API Documentation**: Visit `http://localhost:8000/docs` for interactive Swagger documentation
- **Database viewer**: Use `sqlite3 chat_rooms.db` or a GUI tool like DB Browser for SQLite

## Production Deployment

For production deployment, refer to `NOTES.md` for security considerations and recommended changes before deploying to a live environment.

---

For detailed architecture, design decisions, and testing information, see **NOTES.md**.
