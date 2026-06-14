"use client";

import { cn } from "@/lib/utils";

interface VoiceButtonProps {
  recording: boolean;
  loading: boolean;
  onPress: () => void;
  onRelease: () => void;
  disabled?: boolean;
  size?: "sm" | "md" | "lg";
}

const sizes = { sm: "h-12 w-12", md: "h-16 w-16", lg: "h-20 w-20" };
const iconSizes = { sm: "h-5 w-5", md: "h-6 w-6", lg: "h-8 w-8" };

export default function VoiceButton({
  recording,
  loading,
  onPress,
  onRelease,
  disabled,
  size = "md",
}: VoiceButtonProps) {
  return (
    <button
      onMouseDown={onPress}
      onMouseUp={onRelease}
      onTouchStart={onPress}
      onTouchEnd={onRelease}
      disabled={disabled || loading}
      className={cn(
        "relative flex items-center justify-center rounded-full shadow-lg transition",
        sizes[size],
        recording
          ? "bg-red-500 text-white animate-pulse-glow scale-110"
          : loading
          ? "bg-slate-300 text-slate-500 cursor-wait"
          : "bg-slate-900 text-white hover:bg-slate-800 hover:scale-105",
        disabled && "opacity-50 cursor-not-allowed"
      )}
      aria-label={recording ? "Recording... Release to send" : "Hold to record"}
    >
      {loading ? (
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
      ) : (
        <svg className={iconSizes[size]} viewBox="0 0 24 24" fill="currentColor">
          {recording ? (
            <rect x="6" y="6" width="12" height="12" rx="2" />
          ) : (
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3zM19 10v2a7 7 0 0 1-14 0v-2M12 19v4M8 23h8" />
          )}
        </svg>
      )}
      {/* Pulse ring when recording */}
      {recording && (
        <span className="absolute inset-0 rounded-full border-2 border-red-400 animate-ping" />
      )}
    </button>
  );
}
