"use client";

import { useState, useRef, useCallback, KeyboardEvent } from "react";
import { useSpeechRecognition } from "@/hooks/useSpeechRecognition";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  autoSubmitVoice?: boolean;
}

export default function ChatInput({
  onSend,
  disabled = false,
  placeholder = "Describe your situation...",
  autoSubmitVoice = true,
}: ChatInputProps) {
  const [value, setValue] = useState("");
  const [isSending, setIsSending] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Speech recognition
  const {
    isListening,
    transcript,
    interimTranscript,
    isSupported: voiceSupported,
    error: voiceError,
    startListening,
    stopListening,
  } = useSpeechRecognition({
    language: "en-US",
    continuous: false,
    interimResults: true,
    onResult: (text, isFinal) => {
      if (isFinal) {
        const newValue = value + text;
        setValue(newValue);
        // Auto-submit after final result if enabled
        if (autoSubmitVoice && newValue.trim()) {
          setTimeout(() => {
            handleSendMessage(newValue.trim());
          }, 500);
        }
      }
    },
    onEnd: () => {
      // Voice input ended
    },
  });

  const handleSendMessage = useCallback(
    (message?: string) => {
      const text = message || value.trim();
      if (!text || disabled || isSending) return;
      setIsSending(true);
      onSend(text);
      setValue("");
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
      setTimeout(() => setIsSending(false), 100);
    },
    [value, disabled, isSending, onSend]
  );

  const handleSend = useCallback(() => {
    handleSendMessage();
  }, [handleSendMessage]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = Math.min(el.scrollHeight, 150) + "px";
    }
  };

  const handleVoiceToggle = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  const displayValue = isListening ? value + interimTranscript : value;
  const isButtonDisabled = displayValue.trim().length === 0 || disabled || isSending;

  return (
    <div className="space-y-1">
      {/* Voice status / error */}
      {isListening && (
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-50 border border-red-200">
          <span className="relative flex h-3 w-3">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75" />
            <span className="relative inline-flex h-3 w-3 rounded-full bg-red-500" />
          </span>
          <span className="text-xs font-medium text-red-700">Listening...</span>
          {interimTranscript && (
            <span className="text-xs text-red-600 italic truncate flex-1">
              &quot;{interimTranscript}&quot;
            </span>
          )}
        </div>
      )}

      {voiceError && (
        <p className="text-xs text-red-600 px-3">{voiceError}</p>
      )}

      {/* Input area */}
      <div className="flex items-end gap-2 rounded-xl border border-slate-200 bg-white p-2 shadow-sm">
        {/* Microphone button */}
        {voiceSupported && (
          <button
            type="button"
            onClick={handleVoiceToggle}
            disabled={disabled}
            className={cn(
              "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition",
              isListening
                ? "bg-red-500 text-white animate-pulse hover:bg-red-600"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-900"
            )}
            aria-label={isListening ? "Stop listening" : "Start voice input"}
            title={isListening ? "Stop listening" : "Voice input"}
          >
            {isListening ? (
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="6" width="12" height="12" rx="2" />
              </svg>
            ) : (
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 19v4M8 23h8" />
              </svg>
            )}
          </button>
        )}

        <textarea
          ref={textareaRef}
          value={displayValue}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder={isListening ? "Listening..." : placeholder}
          disabled={disabled || isListening}
          rows={1}
          className="flex-1 resize-none bg-transparent px-2 py-1.5 text-sm outline-none placeholder:text-slate-400 disabled:opacity-50"
        />

        {/* Send button */}
        <button
          type="button"
          onClick={handleSend}
          disabled={isButtonDisabled}
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-900 text-white transition hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed"
          aria-label="Send message"
        >
          <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
          </svg>
        </button>
      </div>
    </div>
  );
}
