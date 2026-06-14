/**
 * Amazon Bedrock integration helpers for NeedNow AI.
 *
 * Client-side utilities for streaming responses from Bedrock-powered
 * endpoints. The actual Bedrock invocation happens server-side —
 * this module handles the frontend streaming consumption.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface StreamEvent {
  type: "text" | "thinking" | "product" | "cart_update" | "eco_alert" | "done" | "error";
  content: string;
  metadata?: Record<string, unknown>;
}

export interface StreamOptions {
  /** Callback for each streamed chunk */
  onChunk: (event: StreamEvent) => void;
  /** Callback when stream completes */
  onComplete?: () => void;
  /** Callback on stream error */
  onError?: (error: Error) => void;
  /** AbortSignal for cancellation */
  signal?: AbortSignal;
}

// ---------------------------------------------------------------------------
// SSE Stream Consumer
// ---------------------------------------------------------------------------

/**
 * Consume a Server-Sent Events stream from a Bedrock-powered endpoint.
 *
 * The backend streams partial responses via SSE as the LLM generates text.
 * This function parses the event stream and invokes typed callbacks.
 */
export async function consumeBedrockStream(
  url: string,
  body: Record<string, unknown>,
  options: StreamOptions
): Promise<void> {
  const { onChunk, onComplete, onError, signal } = options;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: JSON.stringify(body),
      signal,
    });

    if (!response.ok) {
      throw new Error(`Stream request failed: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error("No readable stream");

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Parse SSE events (data: {...}\n\n)
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const block of lines) {
        const dataLine = block
          .split("\n")
          .find((line) => line.startsWith("data: "));

        if (!dataLine) continue;

        const jsonStr = dataLine.slice(6); // Remove "data: "
        if (jsonStr === "[DONE]") {
          onComplete?.();
          return;
        }

        try {
          const event: StreamEvent = JSON.parse(jsonStr);
          onChunk(event);
        } catch {
          // Non-JSON SSE data, skip
        }
      }
    }

    onComplete?.();
  } catch (err) {
    if (err instanceof Error && err.name === "AbortError") return;
    const error = err instanceof Error ? err : new Error("Stream failed");
    onError?.(error);
  }
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** Bedrock model identifiers (for display/metadata) */
export const BEDROCK_MODELS = {
  CLAUDE_SONNET: "anthropic.claude-3-5-sonnet-20241022-v2:0",
  TITAN_EMBED: "amazon.titan-embed-text-v2:0",
} as const;

/** Max tokens configured on backend */
export const BEDROCK_MAX_TOKENS = 4096;
