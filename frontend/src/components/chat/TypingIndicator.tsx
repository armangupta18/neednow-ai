"use client";

export default function TypingIndicator() {
  return (
    <div className="flex justify-start animate-fade-in">
      <div className="flex items-center gap-2 rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-3 shadow-sm">
        <span className="text-xs font-medium text-slate-500">🤖 Thinking</span>
        <div className="flex gap-1">
          <span className="h-1.5 w-1.5 rounded-full bg-blue-500 animate-typing-dot" />
          <span className="h-1.5 w-1.5 rounded-full bg-blue-500 animate-typing-dot" />
          <span className="h-1.5 w-1.5 rounded-full bg-blue-500 animate-typing-dot" />
        </div>
      </div>
    </div>
  );
}
