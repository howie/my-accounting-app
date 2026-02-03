/**
 * WebSocket client for Gemini Live API voice-to-voice interaction.
 *
 * Supports:
 * - Bidirectional audio streaming
 * - Text prompt interrupts during voice conversation
 */

const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL || 'ws://127.0.0.1:8000/api/v1';

export interface VoiceMessage {
  type: 'audio' | 'text' | 'end_turn' | 'disconnect';
  data?: string;
  text?: string;
  mime_type?: string;
}

export interface VoiceServerMessage {
  type: 'audio' | 'text' | 'interrupted' | 'error' | 'connected';
  data?: string;
  text?: string;
  message?: string;
  mime_type?: string;
}

export type VoiceEventHandler = (msg: VoiceServerMessage) => void;

export class VoiceClient {
  private ws: WebSocket | null = null;
  private onMessage: VoiceEventHandler | null = null;
  private onClose: (() => void) | null = null;
  private onError: ((error: Event) => void) | null = null;

  connect(handlers: {
    onMessage: VoiceEventHandler;
    onClose?: () => void;
    onError?: (error: Event) => void;
  }): Promise<void> {
    return new Promise((resolve, reject) => {
      this.onMessage = handlers.onMessage;
      this.onClose = handlers.onClose || null;
      this.onError = handlers.onError || null;

      const url = `${WS_BASE_URL}/voice/ws`;
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        // Wait for "connected" message from server
      };

      this.ws.onmessage = (event: MessageEvent) => {
        try {
          const msg: VoiceServerMessage = JSON.parse(event.data as string);

          if (msg.type === 'connected') {
            resolve();
          }

          if (this.onMessage) {
            this.onMessage(msg);
          }
        } catch {
          // Ignore parse errors
        }
      };

      this.ws.onclose = () => {
        if (this.onClose) {
          this.onClose();
        }
      };

      this.ws.onerror = (event: Event) => {
        if (this.onError) {
          this.onError(event);
        }
        reject(new Error('WebSocket connection failed'));
      };

      // Timeout after 10 seconds
      setTimeout(() => {
        if (this.ws?.readyState !== WebSocket.OPEN) {
          reject(new Error('Connection timeout'));
        }
      }, 10000);
    });
  }

  /**
   * Send audio data chunk to the server.
   */
  sendAudio(audioBase64: string, mimeType: string = 'audio/pcm'): void {
    this.send({
      type: 'audio',
      data: audioBase64,
      mime_type: mimeType,
    });
  }

  /**
   * Send a text message to interrupt the current voice generation.
   * This is the key feature for text-prompt interruption during v2v mode.
   */
  sendTextInterrupt(text: string): void {
    this.send({
      type: 'text',
      text,
    });
  }

  /**
   * Signal the end of speaking turn.
   */
  sendEndTurn(): void {
    this.send({ type: 'end_turn' });
  }

  /**
   * Gracefully disconnect.
   */
  disconnect(): void {
    this.send({ type: 'disconnect' });
    setTimeout(() => {
      this.ws?.close();
      this.ws = null;
    }, 100);
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  private send(msg: VoiceMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg));
    }
  }
}
