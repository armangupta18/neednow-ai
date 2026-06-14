"use client";

import { cn } from "@/lib/utils";

interface MessageAction {
  label: string;
  icon?: string;
  onClick: () => void;
  variant?: "primary" | "secondary" | "outline";
}

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
  isError?: boolean;
  actions?: MessageAction[];
}

export default function MessageBubble({
  role,
  content,
  timestamp,
  isError,
  actions,
}: MessageBubbleProps) {
  const isUser = role === "user";

  return (
    <div
      className={cn(
        "flex w-full animate-fade-in",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div className={cn("max-w-[85%]", isUser ? "items-end" : "items-start")}>
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm",
            isUser
              ? "bg-slate-900 text-white rounded-br-md"
              : isError
              ? "bg-red-50 text-red-700 border border-red-200 rounded-bl-md"
              : "bg-white text-slate-800 border border-slate-200 rounded-bl-md"
          )}
        >
          {/* Avatar indicator */}
          {!isUser && (
            <div className="mb-1 flex items-center gap-1.5">
              <span className="text-xs font-medium opacity-70">
                🤖 NeedNow AI
              </span>
            </div>
          )}

          {/* Content — render bold text with ** markers */}
          <p className="whitespace-pre-wrap">
            {renderContent(content)}
          </p>

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

        {/* Action buttons */}
        {actions && actions.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {actions.map((action, idx) => (
              <button
                key={idx}
                onClick={action.onClick}
                className={cn(
                  "rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors",
                  action.variant === "primary"
                    ? "bg-blue-600 text-white hover:bg-blue-700"
                    : action.variant === "outline"
                    ? "border border-slate-300 text-slate-700 hover:bg-slate-50"
                    : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                )}
              >
                {action.icon && <span className="mr-1">{action.icon}</span>}
                {action.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/** Render content with basic bold (**text**) support */
function renderContent(content: string) {
  const parts = content.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return part;
  });
}
