"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useChatStore } from "@/stores/chat.store";
import { ROUTES } from "@/constants/routes";
import { formatRelativeTime } from "@/lib/utils";

interface HistoryEntry {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export default function HistoryPage() {
  const messages = useChatStore((s) => s.messages);
  const sessionId = useChatStore((s) => s.sessionId);
  const clearChat = useChatStore((s) => s.clearChat);
  const [mounted, setMounted] = useState(false);

  // Avoid hydration mismatch (Zustand persist loads from localStorage)
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="mx-auto max-w-4xl px-6 py-8">
        <h1 className="text-2xl font-bold text-slate-900 mb-6">Chat History</h1>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 rounded-xl bg-slate-100 animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  // Group messages into conversation pairs (user + assistant)
  const conversations: Array<{ user: HistoryEntry; assistant: HistoryEntry | null }> = [];
  for (let i = 0; i < messages.length; i++) {
    const msg = messages[i];
    if (msg && msg.role === "user") {
      const next = messages[i + 1];
      conversations.push({
        user: msg,
        assistant: next && next.role === "assistant" ? next : null,
      });
    }
  }

  const isEmpty = conversations.length === 0;

  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Chat History</h1>
          <p className="text-sm text-slate-500 mt-1">
            {isEmpty
              ? "Your conversations will appear here"
              : `${conversations.length} conversation${conversations.length > 1 ? "s" : ""}`}
            {sessionId && (
              <span className="ml-2 text-slate-400">
                Session: {sessionId.slice(0, 8)}...
              </span>
            )}
          </p>
        </div>
        {!isEmpty && (
          <button
            onClick={clearChat}
            className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-medium text-red-600 transition hover:bg-red-50"
          >
            Clear History
          </button>
        )}
      </div>

      {/* Empty State */}
      {isEmpty && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <span className="text-5xl mb-4">📋</span>
          <h3 className="text-lg font-semibold text-slate-700">No history available</h3>
          <p className="mt-2 max-w-sm text-sm text-slate-500">
            Start a conversation with NeedNow AI and your chat history will appear here.
          </p>
          <Link
            href={ROUTES.CHAT}
            className="mt-6 rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white shadow transition hover:bg-slate-800"
          >
            Start a New Chat
          </Link>
        </div>
      )}

      {/* History Cards */}
      {!isEmpty && (
        <div className="space-y-3">
          {conversations.map((conv, idx) => (
            <HistoryCard
              key={conv.user.id || idx}
              userMessage={conv.user.content}
              assistantMessage={conv.assistant?.content}
              timestamp={conv.user.timestamp}
              isError={!!conv.assistant?.metadata?.error}
            />
          ))}
        </div>
      )}

      {/* CTA at bottom */}
      {!isEmpty && (
        <div className="mt-8 text-center">
          <Link
            href={ROUTES.CHAT}
            className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
          >
            ← Back to Chat
          </Link>
        </div>
      )}
    </div>
  );
}

// ─── History Card Component ──────────────────────────────────

function HistoryCard({
  userMessage,
  assistantMessage,
  timestamp,
  isError,
}: {
  userMessage: string;
  assistantMessage?: string | null;
  timestamp: string;
  isError?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const truncatedUser = userMessage.length > 80 ? userMessage.slice(0, 80) + "..." : userMessage;
  const truncatedAssistant =
    assistantMessage && assistantMessage.length > 120
      ? assistantMessage.slice(0, 120) + "..."
      : assistantMessage;

  return (
    <div
      className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:border-slate-300 cursor-pointer"
      onClick={() => setExpanded(!expanded)}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-800">
            {expanded ? userMessage : truncatedUser}
          </p>
        </div>
        <span className="shrink-0 text-[10px] text-slate-400">
          {formatRelativeTime(timestamp)}
        </span>
      </div>

      {/* Assistant reply */}
      {assistantMessage && (
        <div className={`mt-2 rounded-lg p-2.5 text-xs leading-relaxed ${isError ? "bg-red-50 text-red-700" : "bg-slate-50 text-slate-600"}`}>
          <span className="font-medium text-slate-500">🤖 AI: </span>
          {expanded ? assistantMessage : truncatedAssistant}
        </div>
      )}

      {/* Expand hint */}
      {(userMessage.length > 80 || (assistantMessage && assistantMessage.length > 120)) && (
        <p className="mt-2 text-[10px] text-slate-400 text-right">
          {expanded ? "▲ Click to collapse" : "▼ Click to expand"}
        </p>
      )}
    </div>
  );
}
