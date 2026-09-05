# NOTES — what I built, what I tested, what I’d change

## What this assignment is really testing

From my reading, the hard part is not “call an LLM.” It’s this:

Two people share one stream. Both can talk to the same agent. The agent still has to answer the right person with the right context.

If that breaks, the rest doesn’t matter much.

## What I verified myself

I tested with two browser tabs on the same room code.

1. **Normal chat**
   - Both tabs see each other’s messages live.

2. **Agent trigger**
   - Only messages starting with `@agent` create an agent reply.
   - Normal chat does not spam the model.

3. **Context isolation (core test)**
   - Tab A: talked about a fake “PR review for payments”
   - Tab B: talked about a fake “deploy blocker on auth”
   - A asked `@agent summarize my topic`
   - B asked `@agent summarize my topic`
   - A’s answer stayed around payments/PR. B’s answer stayed around deploy/auth.
   - I did not see B’s topic show up inside A’s answer in my local runs.

4. **Concurrent typing**
   - Both tabs can send close together.
   - Server accepts both messages and broadcasts them.
   - Agent jobs are kicked off with `asyncio.create_task`, so one slow LLM call does not freeze the websocket loop for the other user.

5. **LLM failure path**
   - With no API key, agent still posts a readable mock reply.
   - Timeout / exception paths return a room message instead of crashing the process.

6. **Restart**
   - Messages written to SQLite.
   - After restart, rejoining the same room loads history.

## Design choices

### Transport: WebSockets
I wanted both directions live (chat + typing indicator). WebSockets were the straightforward choice for two users. I did not build a scalable multiplayer server on purpose.

### Isolation model
Shared visibility, private agent memory.

- Everyone sees the room transcript.
- The model only receives the asking user’s thread.

I think this matches the product idea: the room is shared, but the agent should not mix people up when both address it.

### One LLM call per @agent message
No multi-step pipeline. The brief said keep the call cheap and evaluate the system around the call, not model quality.

### Concurrency
There is a per-room async lock around the “read context → call model → write context” section so two agent runs in the same room don’t interleave memory writes in a messy way. Chat messages still flow without waiting on the model.

### Persistence
SQLite was enough. It survives restart and keeps setup light. If this were production, I’d move to Postgres and be more careful about connection handling.

## What I assumed

- Two tabs are enough to stand in for two users (as the brief says).
- No real auth needed.
- A simple `@agent` prefix is an acceptable address format.
- “Context” means recent turns for that user, not the entire company knowledge base.

## What I did not fully prove

- Heavy load / many rooms.
- Mobile polish beyond basic responsive layout.
- Perfect ordering guarantees under extreme network lag.
- Long multi-hour conversations with very large histories (I cap per-user memory).

## If I had more time

1. Add a small automated test that simulates two users and asserts prompt contents never cross.
2. Show a subtle “context used: N turns from you only” debug line on agent replies (helpful for demos).
3. Better reconnect behavior if the socket drops.
4. Room presence list (who is online).
5. Move typing state so only relevant UI surfaces update under many rooms.

## Honest scope cut

I prioritized:

1. isolation correctness
2. stable room behavior when the model is slow or fails
3. clear UI states (empty, typing, agent vs human)

I did not spend time on auth, file uploads, or fancy agent tools. Those are useful later, but they are not the core test of this assignment.
