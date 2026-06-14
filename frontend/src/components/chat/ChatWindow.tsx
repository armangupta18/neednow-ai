"use client";

import { useRef, useEffect } from "react";
import { useChat } from "@/hooks/useChat";
import MessageBubble from "./MessageBubble";
import TypingIndicator from "./TypingIndicator";
import ReasoningPanel from "./ReasoningPanel";
import Suggestions from "./Suggestions";
import ChatInput from "./ChatInput";
import { CHAT_WELCOME_MESSAGE } from "@/constants/prompts";

export default function ChatWindow() {
  const {
    messages,
    lastResult,
    isTyping,
    sendMessage,
    cancel,
    clearChat,
  } = useChat();

  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    const el = scrollRef.current;
    if (el) {
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    }
  }, [messages, isTyping]);

  const handleSuggestion = (text: string) => {
    sendMessage(text);
  };

  const isEmpty = messages.length === 0;

  return (
    <div className="flex h-full flex-col">
      {/* Header bar */}
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-sm">
            🤖
          </span>
          <div>
            <h2 className="text-sm font-semibold text-slate-800">NeedNow AI</h2>
            <p className="text-[10px] text-slate-400">
              {isTyping ? "Thinking..." : "Online"}
            </p>
          </div>
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearChat}
            className="rounded-md px-2 py-1 text-xs text-slate-500 hover:bg-slate-100 transition"
          >
            Clear Chat
          </button>
        )}
      </div>

      {/* Messages area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-4 py-4 space-y-3"
      >
        {/* Welcome message when empty */}
        {isEmpty && (
          <div className="flex flex-col items-center justify-center h-full text-center gap-6 py-12">
            <div>
              <span className="text-4xl">🛒</span>
              <h3 className="mt-3 text-lg font-semibold text-slate-700">
                Welcome to NeedNow AI
              </h3>
              <p className="mt-1 max-w-sm text-sm text-slate-500">
                {CHAT_WELCOME_MESSAGE}
              </p>
            </div>
            <Suggestions onSelect={handleSuggestion} />
          </div>
        )}

        {/* Messages */}
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            role={msg.role}
            content={msg.content}
            timestamp={msg.timestamp}
            isError={!!msg.metadata?.error}
          />
        ))}

        {/* Typing indicator */}
        {isTyping && <TypingIndicator />}

        {/* Reasoning panel (after assistant reply) */}
        {lastResult && !isTyping && messages.length > 0 && (
          <ReasoningPanel
            reasoning={lastResult.reasoning}
            urgency={lastResult.urgency}
            confidence={lastResult.confidence}
            ecoAlternative={lastResult.ecoAlternative}
          />
        )}
      </div>

      {/* Input area */}
      <div className="border-t bg-slate-50 px-4 py-3 space-y-2">
        {/* Show suggestions when only 1-2 messages */}
        {messages.length > 0 && messages.length <= 2 && (
          <Suggestions onSelect={handleSuggestion} />
        )}
        <ChatInput
          onSend={sendMessage}
          disabled={isTyping}
          placeholder={
            isTyping
              ? "Waiting for response..."
              : "Describe your situation..."
          }
        />
      </div>
    </div>
  );
}
