"use client";

import React, { useRef, useEffect } from "react";
import { Send, Bot, User } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
}

interface AIChatPanelProps {
  messages: Message[];
  input: string;
  setInput: (val: string) => void;
  isLoading: boolean;
  handleSend: (e: React.FormEvent) => void;
}

export default function AIChatPanel({
  messages,
  input,
  setInput,
  isLoading,
  handleSend
}: AIChatPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-col h-full bg-slate-950/40 border border-slate-800 rounded-lg overflow-hidden font-mono">
      {/* Messages Feed */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0 scrollbar-thin scrollbar-thumb-slate-800">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start gap-2.5 max-w-[85%] ${
              msg.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto"
            }`}
          >
            {/* Minimalist Avatar */}
            <div className={`w-6 h-6 rounded-md flex items-center justify-center text-[10px] border ${
              msg.role === "user" 
                ? "bg-slate-800 border-slate-700 text-slate-300" 
                : "bg-blue-950/40 border-blue-900/50 text-blue-400"
            }`}>
              {msg.role === "user" ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
            </div>

            {/* Bubble */}
            <div className={`p-3 rounded-lg text-xs leading-relaxed border ${
              msg.role === "user"
                ? "bg-slate-900 border-slate-800 text-slate-100 rounded-tr-none"
                : "bg-slate-900/60 border-slate-850 text-slate-200 rounded-tl-none"
            }`}>
              <p className="whitespace-pre-wrap">{msg.content}</p>

              {/* Streaming Dots */}
              {msg.isStreaming && msg.content === "" && (
                <div className="flex space-x-1 items-center justify-start py-1">
                  <span className="w-1.5 h-1.5 bg-slate-600 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-1.5 h-1.5 bg-slate-600 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-1.5 h-1.5 bg-slate-600 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={scrollRef} />
      </div>

      {/* Input Form */}
      <form
        onSubmit={handleSend}
        className="p-3 bg-slate-950 border-t border-slate-800 flex gap-2 items-center"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Consultar optimización paramétrica..."
          disabled={isLoading}
          className="flex-1 bg-slate-900 border border-slate-800 rounded px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-slate-600 font-mono transition-colors"
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="p-2 rounded bg-slate-800 hover:bg-slate-700 disabled:bg-slate-900 disabled:text-slate-600 text-slate-300 transition-colors border border-slate-700 hover:border-slate-600 cursor-pointer flex items-center justify-center"
        >
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>
    </div>
  );
}
