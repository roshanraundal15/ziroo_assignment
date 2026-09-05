# Build Assignment — Multiplayer Room with an Automated Participant

Role: Full Stack Engineering Intern  
Timebox: 5–6 hours (don’t exceed this; it’s better to cut scope than rush features)

Goal (plain): Build a simple chat room where two people can talk at the same time and there is an automated participant in the room that answers when addressed. The important rule: when the automated participant replies, it must keep each user’s conversation separate and not mix them up.

What to build
- A shared chat room. Two people join with a name and a room code and see each other’s messages live.
- An automated participant that only replies when a message begins with something like `@agent ...`.
- Per-user context. The automated participant must keep each user’s context separate so one user’s history never affects the other’s replies.
- Basic persistence so messages and room state survive a server restart (or document clearly why you didn’t persist).
- A simple, usable UI: message list, identity for each user, clear visual difference for automated messages, a “typing” or loading indicator while the automated participant is preparing a reply, and a reasonable empty state for new rooms.

Minimum technical stack
- Backend: Python + FastAPI + WebSockets
- Frontend: React + TypeScript (Vite)
- Data store: SQLite (simple, local persistence)

How it should behave (example)
1. Open two browser tabs, join the same room code with different names.
2. Both users type messages and see each other’s messages immediately.
3. If Tab A sends `@agent summarize what we talked about`, the automated participant replies using only Tab A’s conversation history.
4. If Tab B also asks `@agent ...`, the reply for B uses only B’s history. No details from A should appear in B’s reply.

Design notes (what you should defend in the README / NOTES.md)
- Why you picked your transport (WebSockets, SSE, or polling). For two users, pick the simplest that works and explain why.
- How you stored room and per-user memory (what’s persisted, keys used, data model).
- How you avoid cross-talk between users (how you build the input for the automated participant so each user stays isolated).
- How you handle concurrency, message ordering, and race conditions (briefly describe any locking, queuing, or timestamp rules).
- How you handle service failures, timeouts, and bad responses — the room must keep working even if a call fails.

Constraints and expectations
- One call to the external service per addressed message (not on every keystroke).
- Keep the design simple and reliable for two concurrent users — you don’t need production-scale multiplayer.
- The app should degrade gracefully if the automated participant is slow or fails (show an error message in the room, keep chat working).
- Two browser tabs are enough to demonstrate correctness — no real authentication needed.

What reviewers will evaluate (in order)
1. Does the automated participant keep two users’ context separate? This is the main test.
2. Backend design: how you modeled rooms/sessions, concurrency choices, and persistence.
3. Integration safety: do you handle slow, malformed, or failed replies defensively?
4. Frontend: interaction states and overall UX (typing state, clear identities, visual separation).
5. Honesty in NOTES.md: what you tested, what you assumed, and what you’d improve with more time.

Practical notes
- Use whichever external service/key you already have access to and document how to set the key in `.env`.
- Keep calls small during development — a handful of test messages is enough.
- Include a NOTES.md with tradeoffs, tests performed, and next steps.
- The app should run locally with documented setup steps for backend and frontend.

Submission
- A working repository (or zip) with frontend + backend and setup instructions.
- README with how to run locally and a NOTES.md describing what you tested and what you’d improve.
