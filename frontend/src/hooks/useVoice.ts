"use client";

import { useState, useRef, useCallback } from "react";
import { transcribeAudio, voiceChat, validateAudioFile } from "@/services/voice.service";
import { useUserStore } from "@/stores/user.store";
import { useChatStore } from "@/stores/chat.store";
import type { TranscribeResponse, VoiceChatResponse } from "@/services/voice.service";

/**
 * Voice hook — manages audio recording, transcription, and voice chat.
 */
export function useVoice() {
  const [recording, setRecording] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [transcription, setTranscription] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const userId = useUserStore((s) => s.userId);
  const sessionId = useChatStore((s) => s.sessionId);

  // ── Recording ──────────────────────────────────────────────

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      setRecording(true);
    } catch {
      setError("Microphone access denied. Please allow microphone permissions.");
    }
  }, []);

  const stopRecording = useCallback((): Promise<File | null> => {
    return new Promise((resolve) => {
      const recorder = mediaRecorderRef.current;
      if (!recorder || recorder.state === "inactive") {
        resolve(null);
        return;
      }

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        const file = new File([blob], "voice_recording.webm", { type: "audio/webm" });
        setRecording(false);
        // Stop all tracks
        recorder.stream.getTracks().forEach((t) => t.stop());
        resolve(file);
      };

      recorder.stop();
    });
  }, []);

  // ── Transcription ──────────────────────────────────────────

  const transcribe = useCallback(
    async (file: File): Promise<TranscribeResponse | null> => {
      const validationError = validateAudioFile(file);
      if (validationError) {
        setError(validationError);
        return null;
      }

      try {
        setLoading(true);
        setError(null);
        const result = await transcribeAudio(file, userId);
        setTranscription(result.text);
        return result;
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Transcription failed");
        return null;
      } finally {
        setLoading(false);
      }
    },
    [userId]
  );

  // ── Voice Chat (record → transcribe → pipeline) ───────────

  const sendVoiceMessage = useCallback(
    async (file: File): Promise<VoiceChatResponse | null> => {
      const validationError = validateAudioFile(file);
      if (validationError) {
        setError(validationError);
        return null;
      }

      try {
        setLoading(true);
        setError(null);
        const result = await voiceChat(file, userId, {
          sessionId: sessionId ?? undefined,
          language: "en",
        });
        setTranscription(result.transcribed_text);
        return result;
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Voice chat failed");
        return null;
      } finally {
        setLoading(false);
      }
    },
    [userId, sessionId]
  );

  // ── Convenience: record then send ─────────────────────────

  const recordAndSend = useCallback(async (): Promise<VoiceChatResponse | null> => {
    const file = await stopRecording();
    if (!file) return null;
    return sendVoiceMessage(file);
  }, [stopRecording, sendVoiceMessage]);

  return {
    // State
    recording,
    loading,
    error,
    transcription,
    // Actions
    startRecording,
    stopRecording,
    transcribe,
    sendVoiceMessage,
    recordAndSend,
  };
}
