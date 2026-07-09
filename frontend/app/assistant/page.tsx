"use client";

import { useState, useRef, useEffect } from "react";
import { Sparkles, Send, User } from "lucide-react";
import Topbar from "@/components/Topbar";
import { api } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  text: string;
  data?: string[];
}

const SUGGESTIONS = [
  "How many available seats on Floor 3?",
  "What's the utilization of Floor 2?",
  "How many pending new joiners?",
  "How many employees have no seat?",
];

export default function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", text: "Ask me about seat availability, utilization, headcounts, or who's sitting where." },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (text: string) => {
    if (!text.trim() || busy) return;
    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");
    setBusy(true);
    try {
      const { data } = await api.post("/api/assistant/query", { query: text });
      setMessages((m) => [...m, { role: "assistant", text: data.answer, data: data.data }]);
    } catch {
      setMessages((m) => [...m, { role: "assistant", text: "Something went wrong reaching the assistant service." }]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <Topbar title="Ask Ethara" />
      <div className="p-6 max-w-2xl mx-auto flex flex-col h-[calc(100vh-73px)]">
        <div className="flex-1 overflow-auto space-y-4 pb-4">
          {messages.map((m, i) => (
            <div key={i} className={`flex gap-3 ${m.role === "user" ? "flex-row-reverse" : ""}`}>
              <div className={`w-7 h-7 rounded-lg grid place-items-center shrink-0 ${
                m.role === "assistant" ? "bg-brand-light text-brand" : "bg-brand text-white"
              }`}>
                {m.role === "assistant" ? <Sparkles size={14} /> : <User size={14} />}
              </div>
              <div className={`card px-4 py-2.5 max-w-[80%] text-sm ${m.role === "user" ? "bg-brand text-white border-brand" : ""}`}>
                <p>{m.text}</p>
                {m.data && m.data.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {m.data.map((d, j) => (
                      <span key={j} className="font-mono text-[11px] px-1.5 py-0.5 bg-white/[0.06] rounded border border-white/10">{d}</span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        {messages.length <= 1 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {SUGGESTIONS.map((s) => (
              <button key={s} onClick={() => send(s)}
                className="text-xs px-3 py-1.5 rounded-full border border-white/10 text-ink-muted hover:border-brand hover:text-brand transition-colors">
                {s}
              </button>
            ))}
          </div>
        )}

        <form onSubmit={(e) => { e.preventDefault(); send(input); }} className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about seats, utilization, or headcount…"
            className="flex-1 px-4 py-2.5 text-sm bg-white/5 border border-white/10 rounded-lg focus-visible:outline-none focus:border-brand placeholder:text-ink-muted"
          />
          <button type="submit" disabled={busy}
            className="w-10 h-10 shrink-0 grid place-items-center rounded-lg brand-gradient text-white glow-hover disabled:opacity-50">
            <Send size={16} />
          </button>
        </form>
      </div>
    </>
  );
}
