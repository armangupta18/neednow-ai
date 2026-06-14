"use client";

import { useVoice } from "@/hooks/useVoice";
import { useChat } from "@/hooks/useChat";
import VoiceButton from "./VoiceButton";
import { VOICE_START_PROMPT, VOICE_RECORDING_PROMPT, VOICE_PROCESSING_PROMPT } from "@/constants/prompts";

interface VoicePanelProps {
  onTranscriptionComplete?: (text: string) => void;
}

export default function VoicePanel({ onTranscriptionComplete }: VoicePanelProps) {
  const {
    recording,
    loading,
    error,
    transcription,
    startRecording,
    stopRecording,
    sendVoiceMessage,
  } = useVoice();
  const { sendMessage } = useChat();

  const handleRelease = async () => {
    const file = await stopRecording();
    if (!file) return;

    const result = await sendVoiceMessage(file);
    if (result) {
      onTranscriptionComplete?.(result.transcribed_text);
      // The voice chat response already went through the pipeline
    }
  };

  const statusText = recording
    ? VOICE_RECORDING_PROMPT
    : loading
    ? VOICE_PROCESSING_PROMPT
    : VOICE_START_PROMPT;

  return (
    <div className="flex flex-col items-center gap-4 py-6">
      <VoiceButton
        recording={recording}
        loading={loading}
        onPress={startRecording}
        onRelease={handleRelease}
      />

      <p className="text-sm text-slate-500 text-center max-w-xs">{statusText}</p>

      {error && (
        <p className="text-xs text-red-500 text-center">{error}</p>
      )}

      {transcription && !recording && !loading && (
        <div className="w-full max-w-md rounded-lg bg-slate-50 border border-slate-200 p-3">
          <p className="text-xs text-slate-400 mb-1">Transcribed:</p>
          <p className="text-sm text-slate-700 italic">&ldquo;{transcription}&rdquo;</p>
        </div>
      )}
    </div>
  );
}
