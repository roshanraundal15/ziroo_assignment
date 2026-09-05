import { useCallback, useEffect, useRef, useState } from "react";
import { Composer } from "./components/Composer";
import { JoinScreen } from "./components/JoinScreen";
import { MessageList } from "./components/MessageList";
import { RoomHeader } from "./components/RoomHeader";

export type ChatMessage = {
  id?: number | string;
  user_id?: string;
  user_name?: string;
  role?: "user" | "agent" | "system";
  content: string;
  reply_to_user_id?: string;
  reply_to_user_name?: string;
  created_at?: number;
};

type Member = { id: string; name: string };
type ConnectionStatus = "idle" | "connecting" | "open" | "reconnecting" | "closed";

function wsUrl(roomId: string) {
  const override = import.meta.env.VITE_WS_URL as string | undefined;
  if (override) {
    return `${override.replace(/\/$/, "")}/${encodeURIComponent(roomId)}`;
  }
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  // Vite dev server proxies /ws -> backend
  return `${protocol}://${window.location.host}/ws/${encodeURIComponent(roomId)}`;
}

export default function App() {
  const [name, setName] = useState("");
  const [roomCode, setRoomCode] = useState("demo");
  const [joined, setJoined] = useState(false);
  const [myId, setMyId] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [agentTypingFor, setAgentTypingFor] = useState<string | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>("idle");
  const [focusThread, setFocusThread] = useState(false);
  const [queuedMessages, setQueuedMessages] = useState<string[]>([]);
  const [copied, setCopied] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<number | undefined>(undefined);
  const shouldReconnect = useRef(false);
  const queuedRef = useRef<string[]>([]);

  const room = roomCode.trim().toLowerCase();
  const canJoin = name.trim().length > 0 && room.length > 0;

  const connect = useCallback(() => {
    if (!canJoin) return;
    window.clearTimeout(reconnectTimer.current);
    setStatus("connecting");

    const ws = new WebSocket(wsUrl(room));
    wsRef.current = ws;

    ws.onopen = () => {
      setJoined(true);
      setStatus("open");
      ws.send(JSON.stringify({ type: "join", name: name.trim() }));
      const queued = queuedRef.current;
      queuedRef.current = [];
      setQueuedMessages([]);
      queued.forEach((content) =>
        ws.send(JSON.stringify({ type: "chat", content }))
      );
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "welcome") {
        setMyId(data.user_id);
        setMessages(data.messages || []);
        if (Array.isArray(data.members)) {
          setMembers(data.members);
        }
        return;
      }

      if (data.type === "members") {
        setMembers(Array.isArray(data.members) ? data.members : []);
        return;
      }

      if (data.type === "agent_typing") {
        setAgentTypingFor(data.active ? data.user_name || "someone" : null);
        return;
      }

      if (data.type === "system") {
        setMessages((current) => [
          ...current,
          {
            role: "system",
            content: data.content,
            created_at: data.created_at,
          },
        ]);
        return;
      }

      if (data.type === "chat") {
        setMessages((current) => [...current, data]);
      }
    };

    ws.onclose = () => {
      if (shouldReconnect.current) {
        setStatus("reconnecting");
        reconnectTimer.current = window.setTimeout(connect, 1800);
      } else {
        setStatus("closed");
      }
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [canJoin, name, room]);

  useEffect(
    () => () => {
      shouldReconnect.current = false;
      window.clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    },
    []
  );

  function startRoom() {
    if (canJoin) {
      shouldReconnect.current = true;
      connect();
    }
  }

  function leaveRoom() {
    shouldReconnect.current = false;
    window.clearTimeout(reconnectTimer.current);
    wsRef.current?.close();
    setJoined(false);
    setStatus("idle");
    setMessages([]);
    setMembers([]);
    setAgentTypingFor(null);
  }

  function sendChat(content: string) {
    if (!content.trim()) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({ type: "chat", content: content.trim() })
      );
    } else {
      queuedRef.current = [...queuedRef.current, content.trim()];
      setQueuedMessages([...queuedRef.current]);
    }
  }

  function copyRoom() {
    void navigator.clipboard?.writeText(room).then(() => {
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1400);
    });
  }

  if (!joined) {
    return (
      <JoinScreen
        name={name}
        roomCode={roomCode}
        status={status}
        canJoin={canJoin}
        onNameChange={setName}
        onRoomChange={setRoomCode}
        onJoin={startRoom}
        onRandomRoom={() =>
          setRoomCode(Math.random().toString(36).slice(2, 8))
        }
      />
    );
  }

  return (
    <div className="app-shell room-screen">
      <RoomHeader
        room={room}
        name={name}
        status={status}
        members={members}
        focusThread={focusThread}
        copied={copied}
        onCopy={copyRoom}
        onFocusChange={setFocusThread}
        onLeave={leaveRoom}
        onRetry={connect}
      />
      {(status === "reconnecting" || status === "closed") && (
        <div className="connection-banner" role="status">
          <span className="signal-icon">!</span>
          <span>
            {status === "reconnecting"
              ? "Connection interrupted. Reconnecting..."
              : "You are offline. Messages will queue until you reconnect."}
          </span>
          <button onClick={connect}>Retry connection</button>
        </div>
      )}
      <main className="room-layout">
        <MessageList
          messages={messages}
          myId={myId}
          focusThread={focusThread}
          agentTypingFor={agentTypingFor}
          queuedMessages={queuedMessages}
        />
        <Composer
          onSend={sendChat}
          queuedCount={queuedMessages.length}
          disabled={status === "closed"}
        />
      </main>
    </div>
  );
}
