"use client";

import { cn } from "@/lib/utils";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
  isError?: boolean;
}

export default function MessageBubble({
  role,
  content,
  timestamp,
  isError,
}: MessageBubbleProps) {
  const isUser = role === "user";

  return (
    <div
      className={cn(
        "flex w-full animate-fade-in-up",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm",
          isUser
            ? "bg-slate-900 text-white rounded-br-md"
            : isError
            ? "bg-red-50 text-red-700 border border-red-200 rounded-bl-md"
            : "bg-white text-slate-800 border border-slate-200 rounded-bl-md"
        )}
      >
        {/* Avatar indicator */}
        <div className="mb-1 flex items-center gap-1.5">
          <span className="text-xs font-medium opacity-70">
            {isUser ? "You" : "🤖 NeedNow AI"}
          </span>
        </div>

        {/* Content */}
        <p className="whitespace-pre-wrap">{content}</p>

        {/* Timestamp */}
        {timestamp && (
          <p
            className={cn(
              "mt-1.5 text-[10px] opacity-50",
              isUser ? "text-right" : "text-left"
            )}
          >
            {new Date(timestamp).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </p>
        )}
      </div>
    </div>
  );
}
