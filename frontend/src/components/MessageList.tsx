import { useEffect, useMemo, useRef } from "react";
import type { ChatMessage } from "../App";

type Props = {
  messages: ChatMessage[];
  myId: string;
  focusThread: boolean;
  agentTypingFor: string | null;
  queuedMessages: string[];
};

function dayLabel(timestamp?: number) {
  if (!timestamp) return "JUST NOW";
  const date = new Date(timestamp * 1000);
  const today = new Date();
  return date.toDateString() === today.toDateString()
    ? "TODAY"
    : date.toLocaleDateString(undefined, { month: "short", day: "numeric" }).toUpperCase();
}

export function MessageList({
  messages,
  myId,
  focusThread,
  agentTypingFor,
  queuedMessages,
}: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  const visible = useMemo(
    () =>
      focusThread
        ? messages.filter(
            (message) =>
              message.role === "system" ||
              message.user_id === myId ||
              message.reply_to_user_id === myId
          )
        : messages,
    [focusThread, messages, myId]
  );

  // Important: do not return the value of scrollIntoView (can be a Promise).
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [visible.length, agentTypingFor, queuedMessages.length]);

  let previousDay = "";

  return (
    <section className="messages" aria-live="polite" aria-label="Room messages">
      <div className="message-intro">
        <span>
          {visible.length ? `${visible.length} events in the room` : "A fresh room"}
        </span>
        <span className="intro-line" />
      </div>

      {visible.length === 0 && !queuedMessages.length ? (
        <div className="empty-state">
          <div className="empty-icon">✦</div>
          <h2>
            Start a useful
            <br />
            <em>conversation.</em>
          </h2>
          <p>Try one of these to get momentum:</p>
          <div className="prompt-list">
            <button
              onClick={() =>
                navigator.clipboard?.writeText(
                  "@agent help us frame the problem"
                )
              }
            >
              @agent help us frame the problem <span>↗</span>
            </button>
            <button
              onClick={() =>
                navigator.clipboard?.writeText(
                  "@agent what should we consider next?"
                )
              }
            >
              @agent what should we consider next? <span>↗</span>
            </button>
          </div>
        </div>
      ) : (
        visible.map((message, index) => {
          const day = dayLabel(message.created_at);
          const mine = message.user_id === myId && message.role === "user";
          const isAgent = message.role === "agent";
          const isSystem = message.role === "system";
          const showDay = day !== previousDay;
          previousDay = day;

          return (
            <div key={`${message.id ?? "local"}-${index}`}>
              {showDay && (
                <div className="day-divider">
                  <span>{day}</span>
                </div>
              )}
              <article
                className={`message ${mine ? "mine" : ""} ${
                  isAgent ? "agent" : ""
                } ${isSystem ? "system" : ""}`}
              >
                <div className="message-meta">
                  {isSystem ? (
                    <span className="system-mark">●</span>
                  ) : (
                    <>
                      <span
                        className={`message-avatar ${
                          isAgent ? "agent-avatar" : ""
                        }`}
                      >
                        {isAgent
                          ? "Z"
                          : (message.user_name || "?").slice(0, 1).toUpperCase()}
                      </span>
                      <strong>
                        {isAgent
                          ? "Ziroo agent"
                          : mine
                          ? "You"
                          : message.user_name || "Guest"}
                      </strong>
                      {isAgent && <span className="badge agent-badge">AGENT</span>}
                      {isAgent && (
                        <span className="reply-label">
                          replying to {message.reply_to_user_name || "you"}
                        </span>
                      )}
                      <time>
                        {message.created_at
                          ? new Date(message.created_at * 1000).toLocaleTimeString(
                              [],
                              { hour: "2-digit", minute: "2-digit" }
                            )
                          : "now"}
                      </time>
                    </>
                  )}
                </div>
                <div className="message-content">
                  {message.content}
                  {isAgent && (
                    <span className="degraded-badge">LIVE RESPONSE</span>
                  )}
                </div>
              </article>
            </div>
          );
        })
      )}

      <div className="queued-stack">
        {queuedMessages.map((content, index) => (
          <article className="message pending" key={`pending-${index}`}>
            <div className="message-meta">
              <span className="message-avatar">Y</span>
              <strong>You</strong>
              <span className="pending-label">QUEUED</span>
            </div>
            <div className="message-content">{content}</div>
          </article>
        ))}
      </div>

      {agentTypingFor && (
        <div className="typing-row">
          <span className="typing-avatar">Z</span>
          <span>
            <i />
            <i />
            <i />
          </span>
          <strong>Ziroo is thinking for {agentTypingFor}</strong>
        </div>
      )}
      <div ref={bottomRef} />
    </section>
  );
}
