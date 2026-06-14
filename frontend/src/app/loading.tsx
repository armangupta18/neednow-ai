export default function GlobalLoading() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-6">
      {/* Animated logo pulse */}
      <div className="relative flex h-16 w-16 items-center justify-center">
        <div className="absolute inset-0 animate-ping rounded-full bg-blue-400/30" />
        <div className="relative flex h-12 w-12 items-center justify-center rounded-full bg-slate-900 text-white text-xl font-bold shadow-lg">
          N
        </div>
      </div>

      {/* Loading text */}
      <div className="text-center">
        <p className="text-lg font-medium text-slate-700">Loading NeedNow AI</p>
        <p className="mt-1 text-sm text-slate-400">Preparing your experience...</p>
      </div>

      {/* Typing dots */}
      <div className="flex gap-1.5">
        <span className="h-2 w-2 rounded-full bg-blue-500 animate-typing-dot" />
        <span className="h-2 w-2 rounded-full bg-blue-500 animate-typing-dot" />
        <span className="h-2 w-2 rounded-full bg-blue-500 animate-typing-dot" />
      </div>
    </div>
  );
}
