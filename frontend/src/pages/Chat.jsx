/**
 * pages/Chat.jsx
 * Phase 1 — RAG chat with source citations.
 */

import { useState, useRef, useEffect } from "react";
import { useApp } from "../context/AppContext";
import { sendChat, saveChat } from "../services/api";
import ReactMarkdown from "react-markdown";
import { Send, Bot, User, FileText } from "lucide-react";
import toast from "react-hot-toast";

function SourcePill({ source, page, similarity }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      background: "var(--bg3)", border: "1px solid var(--border)",
      borderRadius: 999, padding: "2px 10px", fontSize: 11,
      color: "var(--text2)", margin: "2px 3px",
    }}>
      <FileText size={10} />
      {source} · p.{page} · {(similarity * 100).toFixed(0)}%
    </span>
  );
}

function Message({ role, content, sources }) {
  const isUser = role === "user";
  return (
    <div style={{
      display: "flex", gap: 12, marginBottom: 24,
      flexDirection: isUser ? "row-reverse" : "row",
    }}>
      {/* Avatar */}
      <div style={{
        width: 52, height: 52, borderRadius: "50%", flexShrink: 0,
        background: isUser ? "linear-gradient(135deg,var(--accent),#9333ea)" : "var(--bg3)",
        border: "1px solid var(--border)",
        display: "flex", alignItems: "center", justifyContent: "center",
      }}>
        {isUser ? <User size={14} color="white" /> : <Bot size={14} color="var(--accent)" />}
      </div>

      {/* Bubble */}
      <div style={{ maxWidth: "75%", minWidth: 0 }}>
        <div style={{
          background: isUser ? "rgba(108,99,255,0.15)" : "var(--bg2)",
          border: `1px solid ${isUser ? "rgba(108,99,255,0.3)" : "var(--border)"}`,
          borderRadius: isUser ? "14px 4px 14px 14px" : "4px 14px 14px 14px",
          padding: "12px 16px",
        }}>
          <div className="markdown" style={{ fontSize: 14 }}>
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        </div>
        {sources?.length > 0 && (
          <div style={{ marginTop: 6 }}>
            {sources.map((s, i) => <SourcePill key={i} {...s} />)}
          </div>
        )}
      </div>
    </div>
  );
}

export default function Chat() {
  const { username, courseCode } = useApp();
  const [messages, setMessages] = useState([]);
  const [input, setInput]       = useState("");
  const [loading, setLoading]   = useState(false);
  const bottomRef               = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const send = async () => {
    if (!input.trim()) return;
    if (!courseCode) return toast.error("Set your course code first");

    const question = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: question }]);
    setLoading(true);

    try {
      const res = await sendChat(question, courseCode);
      const { answer, sources } = res.data;
      setMessages(prev => [...prev, { role: "assistant", content: answer, sources }]);

      // Phase 5: save chat to profile
      if (username) saveChat(username, courseCode, question, answer).catch(() => {});
    } catch (e) {
      toast.error(e.response?.data?.detail || "Chat failed");
      setMessages(prev => [...prev, { role: "assistant", content: "❌ Error getting answer. Make sure you've uploaded lecture notes first." }]);
    } finally { setLoading(false); }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>

      {/* Header */}
      <div style={{ padding: "20px 28px 16px", borderBottom: "1px solid var(--border)", flexShrink: 0 }}>
        <h1 style={{ fontSize: 32, fontWeight: 700 }}>💬 Chat</h1>
        <div style={{ fontSize: 17, color: "var(--text3)", marginTop: 2 }}>
          Ask anything about your uploaded lecture notes — answers include page citations
        </div>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: "auto", padding: "24px 28px" }}>
        {messages.length === 0 && (
          <div className="chat-empty" style={{ textAlign: "center", marginTop: "20vh" }}>
            <Bot size={40} color="var(--text3)" style={{ margin: "0 auto 12px" }} />
            <div className="empty-title" style={{ fontSize: 26, fontWeight: 500, color: "var(--text2)" }}>Ask a question about your notes</div>
            <div className="empty-subtitle" style={{ fontSize: 13, color: "var(--text3)", marginTop: 6 }}>
              Upload lecture PDFs first, then ask anything
            </div>
            <div style={{ display: "flex", gap: 8, justifyContent: "center", marginTop: 20, flexWrap: "wrap" }}>
              {["What is Fick's First Law?", "Explain Reynolds number", "What is heat transfer?"].map(q => (
                <button key={q} className="btn btn-secondary suggestion-btn" onClick={() => setInput(q)}>{q}</button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => <Message key={i} {...m} />)}

        {loading && (
          <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
            <div style={{ width: 32, height: 32, borderRadius: "50%", background: "var(--bg3)", border: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Bot size={14} color="var(--accent)" />
            </div>
            <div style={{ background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: "4px 14px 14px 14px", padding: "14px 18px" }}>
              <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                {[0, 1, 2].map(i => (
                  <div key={i} style={{
                    width: 6, height: 6, borderRadius: "50%", background: "var(--accent)",
                    animation: `bounce .8s ${i * .15}s infinite alternate`,
                  }} />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{ padding: "16px 28px", borderTop: "1px solid var(--border)", flexShrink: 0 }}>
        <div style={{ display: "flex", gap: 10 }}>
          <input
            className="input"
            placeholder="Ask about your lecture notes..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && !e.shiftKey && send()}
            disabled={loading}
          />
          <button className="btn btn-primary" onClick={send} disabled={loading || !input.trim()}>
            <Send size={15} />
          </button>
        </div>
        <div style={{ fontSize: 15, color: "var(--text3)", marginTop: 6 }}>
          Press Enter to send · Answers cite source file and page number
        </div>
      </div>

      <style>{`@keyframes bounce { from { transform: translateY(0) } to { transform: translateY(-6px) } }`}</style>
    </div>
  );
}