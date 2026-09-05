# NOTES.md

## What this assignment is actually testing

This is not mainly about connecting an LLM.

The real problem is:

Two people are in the same room.
Both can talk at the same time.
Both can ask the same AI agent.
The agent still has to answer the right person with the right context.

If that fails, the whole assignment fails.
So I treated context isolation as the main goal, not a side feature.

---

## What I built

A shared chat room where:

- two users can join with a name + room code
- messages appear live for both people
- an AI agent sits in the room as a third participant
- the agent only replies when someone writes `@agent ...`
- each user has a separate conversation memory for the agent
- messages are saved so the room history can survive a server restart

Stack:

- Backend: Python + FastAPI + WebSockets + SQLite
- Frontend: React + TypeScript
- LLM: one API call per `@agent` message

---

## How context isolation works

This was the most important part for me.

The room is shared.
The agent memory is not shared.

What that means:

- Everyone can see all messages in the room
- But when User A asks `@agent ...`, the model only gets User A’s recent messages
- User B’s messages are not put into User A’s prompt
- The agent reply is shown in the room, but tagged as a reply to User A
- That reply is also saved back into User A’s own memory for follow-up questions

Why I did it this way:

In real life, a shared team room is still shared.
People can see each other’s messages.
But if both people ask the agent at the same time, the agent should not mix their workstreams.

So I separated two things:

1. room transcript = shared
2. agent context = private per user

That felt closest to the product idea.

---

## What I tested myself

I tested with two browser tabs using the same room code.

### 1. Normal chat
Both tabs can send messages.
Both tabs see each other’s messages live.

### 2. Agent only when addressed
If I write a normal message, the agent stays quiet.
Only messages starting with `@agent` trigger a model call.

This was important because the brief said keep the AI call cheap.
I did not want one call on every keystroke or every chat message.

### 3. Core isolation test
This is the main test I cared about.

Tab A:
- talked about a payments PR review
- asked `@agent summarize my topic`

Tab B:
- talked about a deploy blocker on auth
- asked `@agent summarize my topic`

Result in my local runs:
- A’s answer stayed around payments / PR
- B’s answer stayed around deploy / auth
- I did not see B’s topic leak into A’s answer

That is the behavior I was aiming for.

### 4. Both users typing at the same time
Both tabs can send messages close together.
The server accepts both.
The room does not freeze.

If both users call `@agent` around the same time:
- each agent job runs in the background
- one slow model call does not block the other user’s chat

### 5. Model failure handling
I also tested the bad paths.

- If there is no API key, the agent still replies with a clear mock message
- If the model times out or fails, the agent posts an error message in the room
- The app does not crash
- The other user can still keep chatting

I wanted the room to stay usable even when the model is slow or broken.

### 6. Restart / persistence
Messages are saved in SQLite.
After restarting the backend and joining the same room again, history comes back.

---

## Why I chose WebSockets

I needed live updates in both directions:

- user sends a message
- other user sees it
- agent typing state appears
- agent reply appears

For two users, WebSockets were the simplest option that actually felt like a real chat room.

I did not try to build a scalable multiplayer system.
The brief said that was not needed.
So I kept it simple.

Polling would work, but it feels slower and less natural for chat.
SSE is mostly one-way.
WebSockets were the clean fit here.

---

## Backend decisions

### Room state
I kept room state simple:

- room code identifies the room
- connected sockets belong to that room
- each connected user has an id and name
- each user has their own agent memory list

### Concurrency
This part mattered because both users can act at the same time.

What I did:

- chat messages are accepted and broadcast as they come
- `@agent` work is started as a background task
- a room-level lock is used around:
  - reading that user’s memory
  - calling the model
  - writing the reply back into that user’s memory

Why:
I did not want two agent runs in the same room to step on each other’s memory writes.

Important point:
normal chat does not wait for the model.
Only the agent memory update is protected.

### Persistence
I used SQLite for messages.

Why:
- easy to set up
- no extra service
- enough for local demo
- survives restart

I did not overbuild this into a full production database setup.
For this assignment, restart-safe message history was enough.

---

## AI integration decisions

The brief said they are not scoring how smart the model answer is.
They are scoring what I built around the call.

So I kept the model part simple and defensive.

### One call only
- one LLM call per `@agent` message
- no multi-step pipeline
- no tool-calling chain
- no extra ranking stages

### Failures are visible in the room
If the model fails, the user should still see something useful in the room, like:

- timed out
- model error
- please try again

The room should not hang.
The room should not crash.
The other user should not get stuck because one agent call failed.

### Typing state
When the agent starts thinking, the UI shows a typing/thinking state.
When the call finishes or fails, that state is cleared.

That makes the system feel more honest and easier to understand while testing.

---

## Frontend decisions

I wanted the UI to feel like a real room, not just a list of raw messages.

So I included:

- join screen with name + room code
- live connection status
- human messages vs agent messages
- “replying to X” on agent replies
- typing / thinking state
- empty room state
- reconnect / offline messaging
- option to focus only my thread

Why this mattered:
The assignment said frontend craft is one of the comparison points.
So I spent some time on interaction states, not only the backend logic.

---

## What I assumed

These are the assumptions I made on purpose:

- two browser tabs are enough to stand in for two users
- no real login/auth is required
- `@agent` is a valid way to address the agent
- “context” means recent turns for that user, not a full company knowledge base
- for this assignment, local setup and clear behavior matter more than scale

---

## What I did not fully prove

I want to be honest about the limits.

I did not fully prove:

- many rooms at once
- many users at once
- very long chats with huge history
- perfect behavior under bad network conditions
- production-level reconnect edge cases

I capped each user’s agent memory so prompts do not grow forever.
That is a practical limit, not a perfect long-term memory system.

---

## If I had more time

If I had more time, I would improve these things first:

1. An automated test that creates two users and checks that prompts never cross
2. A small debug line on agent replies like “used N turns from your thread only”
3. Stronger reconnect handling when the socket drops
4. Cleaner online presence for who is in the room
5. Better handling for very long histories

I would not first add fancy features like file upload or multi-tool agents.
Those are useful later, but they are not the core test of this assignment.

---

## What I prioritized under the timebox

I had limited time, so I ranked work like this:

1. Context isolation
2. Stable behavior when both users are active
3. Safe handling when the model is slow or fails
4. Clear UI states so the system is easy to test
5. Simple persistence and setup

I intentionally skipped:

- authentication
- multi-server scaling
- complex agent workflows
- heavy infrastructure

Not because those are useless, but because they were not the main thing this assignment is measuring.

---

## Short summary

I built a shared room with a shared transcript and private agent memory.

The agent only answers when addressed.
Each user’s context stays separate.
Both users can talk at the same time.
If the model fails, the room still stays up.

That is the core of the submission.
