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

function parseMarkdown(text: string): React.ReactNode[] {
  if (!text) return [];

  const lines = text.split("\n");
  let inList = false;
  let inCodeBlock = false;
  const listItems: React.ReactNode[] = [];
  const codeBlockLines: string[] = [];
  const renderedElements: React.ReactNode[] = [];

  const parseInline = (inlineText: string, keyPrefix: string): React.ReactNode => {
    const parts: React.ReactNode[] = [];
    const pattern = /(`.*?`|\*\*.*?\*\*|\*.*?\*)/g;
    const tokens = inlineText.split(pattern);

    return (
      <span key={keyPrefix}>
        {tokens.map((token, tIdx) => {
          if (token.startsWith("`") && token.endsWith("`")) {
            return (
              <code key={tIdx} className="bg-slate-100 dark:bg-slate-800 text-pink-600 rounded px-1.5 py-0.5 font-mono text-[12px] border border-slate-200">
                {token.slice(1, -1)}
              </code>
            );
          } else if (token.startsWith("**") && token.endsWith("**")) {
            return (
              <strong key={tIdx} className="font-bold text-slate-900">
                {token.slice(2, -2)}
              </strong>
            );
          } else if (token.startsWith("*") && token.endsWith("*")) {
            return (
              <em key={tIdx} className="italic text-slate-800">
                {token.slice(1, -1)}
              </em>
            );
          }
          return token;
        })}
      </span>
    );
  };

  lines.forEach((line, lineIdx) => {
    const trimmed = line.trim();

    if (trimmed.startsWith("```")) {
      if (inCodeBlock) {
        renderedElements.push(
          <pre key={`code-${lineIdx}`} className="bg-slate-900 text-slate-100 p-3 rounded-lg font-mono text-xs overflow-x-auto my-2 border border-slate-800 leading-normal">
            <code>{codeBlockLines.join("\n")}</code>
          </pre>
        );
        codeBlockLines.length = 0;
        inCodeBlock = false;
      } else {
        if (inList) {
          renderedElements.push(<ul key={`list-${lineIdx}`} className="list-disc pl-5 mb-2 space-y-1">{[...listItems]}</ul>);
          listItems.length = 0;
          inList = false;
        }
        inCodeBlock = true;
      }
      return;
    }

    if (inCodeBlock) {
      codeBlockLines.push(line);
      return;
    }

    if (trimmed.startsWith("### ")) {
      if (inList) {
        renderedElements.push(<ul key={`list-${lineIdx}`} className="list-disc pl-5 mb-2 space-y-1">{[...listItems]}</ul>);
        listItems.length = 0;
        inList = false;
      }
      renderedElements.push(
        <h4 key={lineIdx} className="text-xs font-bold text-slate-800 mt-2.5 mb-1 uppercase tracking-wider">
          {parseInline(trimmed.slice(4), `h3-${lineIdx}`)}
        </h4>
      );
    } else if (trimmed.startsWith("## ")) {
      if (inList) {
        renderedElements.push(<ul key={`list-${lineIdx}`} className="list-disc pl-5 mb-2 space-y-1">{[...listItems]}</ul>);
        listItems.length = 0;
        inList = false;
      }
      renderedElements.push(
        <h3 key={lineIdx} className="text-sm font-bold text-slate-900 mt-3.5 mb-1 border-b border-slate-100 pb-0.5">
          {parseInline(trimmed.slice(3), `h2-${lineIdx}`)}
        </h3>
      );
    } else if (trimmed.startsWith("# ")) {
      if (inList) {
        renderedElements.push(<ul key={`list-${lineIdx}`} className="list-disc pl-5 mb-2 space-y-1">{[...listItems]}</ul>);
        listItems.length = 0;
        inList = false;
      }
      renderedElements.push(
        <h2 key={lineIdx} className="text-base font-extrabold text-slate-900 mt-4 mb-2 pb-1 border-b border-slate-200">
          {parseInline(trimmed.slice(2), `h1-${lineIdx}`)}
        </h2>
      );
    } else if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      inList = true;
      listItems.push(
        <li key={`li-${lineIdx}`} className="text-slate-700 list-item list-disc ml-4">
          {parseInline(trimmed.slice(2), `li-inline-${lineIdx}`)}
        </li>
      );
    } else {
      if (inList) {
        renderedElements.push(<ul key={`list-${lineIdx}`} className="list-disc pl-5 mb-2 space-y-1">{[...listItems]}</ul>);
        listItems.length = 0;
        inList = false;
      }

      if (trimmed === "") {
        renderedElements.push(<div key={`spacer-${lineIdx}`} className="h-1.5" />);
      } else {
        renderedElements.push(
          <p key={lineIdx} className="mb-1">
            {parseInline(line, `p-${lineIdx}`)}
          </p>
        );
      }
    }
  });

  if (inList && listItems.length > 0) {
    renderedElements.push(<ul key="list-final" className="list-disc pl-5 mb-2 space-y-1">{[...listItems]}</ul>);
  }

  return renderedElements;
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
    <div className="flex flex-col h-full bg-slate-50/50 border border-slate-200 rounded-lg overflow-hidden font-sans">
      {/* Messages Feed */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0 scrollbar-thin scrollbar-thumb-slate-250">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start gap-3 max-w-[85%] ${
              msg.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto"
            }`}
          >
            {/* Minimalist Avatar */}
            <div className={`w-7 h-7 rounded-lg flex items-center justify-center border shadow-3xs shrink-0 ${
              msg.role === "user" 
                ? "bg-slate-200 border-slate-300 text-slate-700" 
                : "bg-blue-100 border-blue-200 text-blue-600"
            }`}>
              {msg.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            {/* Bubble */}
            <div className={`p-3 rounded-xl text-sm leading-relaxed border shadow-3xs ${
              msg.role === "user"
                ? "bg-blue-600 border-blue-500 text-white rounded-tr-none font-medium"
                : "bg-white border-slate-200 text-slate-850 rounded-tl-none w-full"
            }`}>
              {msg.role === "user" ? (
                <p className="whitespace-pre-wrap">{msg.content}</p>
              ) : (
                <div className="space-y-1 font-normal text-slate-750">{parseMarkdown(msg.content)}</div>
              )}

              {/* Streaming Dots */}
              {msg.isStreaming && msg.content === "" && (
                <div className="flex space-x-1 items-center justify-start py-1.5">
                  <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
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
        className="p-3 bg-white border-t border-slate-200 flex gap-2 items-center"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Consultar optimización paramétrica..."
          disabled={isLoading}
          className="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-3.5 py-2.5 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 font-sans transition-all duration-200"
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="p-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-slate-100 disabled:text-slate-400 disabled:border-slate-200 text-white border border-blue-550 hover:border-blue-650 cursor-pointer flex items-center justify-center transition-all duration-200 shadow-sm shadow-blue-500/5 active:scale-95"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
