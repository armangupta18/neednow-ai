/**
 * WebSocket client for NeedNow AI real-time features.
 *
 * Supports:
 * - Auto-reconnect with exponential backoff
 * - Typed message handlers
 * - Connection state tracking
 * - Heartbeat / ping-pong
 * - Graceful close
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ConnectionState = "connecting" | "connected" | "disconnected" | "reconnecting";

export interface WSMessage<T = unknown> {
  event: string;
  data: T;
  timestamp?: string;
}

export interface WSClientOptions {
  /** WebSocket URL */
  url: string;
  /** Auto-reconnect on disconnect (default: true) */
  autoReconnect?: boolean;
  /** Max reconnect attempts (default: 5) */
  maxRetries?: number;
  /** Initial reconnect delay in ms (default: 1000) */
  reconnectDelay?: number;
  /** Heartbeat interval in ms (default: 30000, 0 to disable) */
  heartbeatInterval?: number;
  /** Callback when connection state changes */
  onStateChange?: (state: ConnectionState) => void;
  /** Callback for incoming messages */
  onMessage?: (message: WSMessage) => void;
  /** Callback on error */
  onError?: (error: Event) => void;
}

// ---------------------------------------------------------------------------
// WebSocket Client
// ---------------------------------------------------------------------------

export class WSClient {
  private ws: WebSocket | null = null;
  private options: Required<WSClientOptions>;
  private retryCount = 0;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private _state: ConnectionState = "disconnected";

  constructor(options: WSClientOptions) {
    this.options = {
      autoReconnect: true,
      maxRetries: 5,
      reconnectDelay: 1000,
      heartbeatInterval: 30000,
      onStateChange: () => {},
      onMessage: () => {},
      onError: () => {},
      ...options,
    };
  }

  /** Current connection state */
  get state(): ConnectionState {
    return this._state;
  }

  /** Connect to the WebSocket server */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    this.setState("connecting");

    try {
      this.ws = new WebSocket(this.options.url);

      this.ws.onopen = () => {
        this.setState("connected");
        this.retryCount = 0;
        this.startHeartbeat();
      };

      this.ws.onmessage = (event: MessageEvent) => {
        try {
          const message: WSMessage = JSON.parse(event.data);
          this.options.onMessage(message);
        } catch {
          // Non-JSON message (e.g., pong)
        }
      };

      this.ws.onerror = (event) => {
        this.options.onError(event);
      };

      this.ws.onclose = () => {
        this.stopHeartbeat();
        this.setState("disconnected");

        if (this.options.autoReconnect && this.retryCount < this.options.maxRetries) {
          this.scheduleReconnect();
        }
      };
    } catch {
      this.setState("disconnected");
    }
  }

  /** Send a typed message */
  send<T>(event: string, data: T): void {
    if (this.ws?.readyState !== WebSocket.OPEN) {
      console.warn("WebSocket not connected. Message not sent.");
      return;
    }

    const message: WSMessage<T> = {
      event,
      data,
      timestamp: new Date().toISOString(),
    };

    this.ws.send(JSON.stringify(message));
  }

  /** Gracefully close the connection */
  disconnect(): void {
    this.options.autoReconnect = false;
    this.stopHeartbeat();
    this.clearReconnect();
    this.ws?.close(1000, "Client disconnect");
    this.ws = null;
    this.setState("disconnected");
  }

  // ─── Private ─────────────────────────────────────────────────

  private setState(state: ConnectionState): void {
    this._state = state;
    this.options.onStateChange(state);
  }

  private startHeartbeat(): void {
    if (this.options.heartbeatInterval <= 0) return;
    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send("ping");
      }
    }, this.options.heartbeatInterval);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private scheduleReconnect(): void {
    this.setState("reconnecting");
    const delay = this.options.reconnectDelay * Math.pow(2, this.retryCount);
    this.retryCount++;

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, Math.min(delay, 30000));
  }

  private clearReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
}

// ---------------------------------------------------------------------------
// Factory
// ---------------------------------------------------------------------------

const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";

/** Create a WebSocket client for the chat stream */
export function createChatWS(
  sessionId: string,
  handlers: Pick<WSClientOptions, "onMessage" | "onStateChange" | "onError">
): WSClient {
  return new WSClient({
    url: `${WS_BASE_URL}/chat/${sessionId}`,
    ...handlers,
  });
}
