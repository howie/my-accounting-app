'use client';

import { useCallback, useRef, useState } from 'react';

import { VoiceClient, VoiceServerMessage } from '@/lib/api/voice';

export type VoiceStatus = 'idle' | 'connecting' | 'connected' | 'recording' | 'error';

interface AudioWorkletNodeLike {
  port: MessagePort;
  disconnect: () => void;
}

export function useVoiceChat() {
  const [status, setStatus] = useState<VoiceStatus>('idle');
  const [transcript, setTranscript] = useState('');
  const [isAiSpeaking, setIsAiSpeaking] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const clientRef = useRef<VoiceClient | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const processorRef = useRef<AudioWorkletNodeLike | null>(null);
  const playbackQueueRef = useRef<string[]>([]);
  const isPlayingRef = useRef(false);

  /**
   * Play audio data received from Gemini.
   */
  const playAudio = useCallback(async (audioBase64: string, mimeType: string) => {
    if (!audioContextRef.current) {
      audioContextRef.current = new AudioContext({ sampleRate: 24000 });
    }

    const ctx = audioContextRef.current;
    const binaryStr = atob(audioBase64);
    const bytes = new Uint8Array(binaryStr.length);
    for (let i = 0; i < binaryStr.length; i++) {
      bytes[i] = binaryStr.charCodeAt(i);
    }

    // Gemini Live returns PCM 16-bit at 24kHz
    const isPcm = mimeType.includes('pcm') || mimeType.includes('raw');
    if (isPcm) {
      const int16 = new Int16Array(bytes.buffer);
      const float32 = new Float32Array(int16.length);
      for (let i = 0; i < int16.length; i++) {
        float32[i] = int16[i] / 32768;
      }

      const audioBuffer = ctx.createBuffer(1, float32.length, 24000);
      audioBuffer.copyToChannel(float32, 0);

      const source = ctx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(ctx.destination);

      setIsAiSpeaking(true);
      source.onended = () => {
        setIsAiSpeaking(false);
        // Play next queued audio if any
        processPlaybackQueue();
      };
      source.start();
    }
  }, []);

  const processPlaybackQueue = useCallback(() => {
    if (isPlayingRef.current || playbackQueueRef.current.length === 0) {
      return;
    }
    const next = playbackQueueRef.current.shift();
    if (next) {
      isPlayingRef.current = true;
      playAudio(next, 'audio/pcm;rate=24000').finally(() => {
        isPlayingRef.current = false;
      });
    }
  }, [playAudio]);

  /**
   * Handle messages from the Gemini Live server.
   */
  const handleServerMessage = useCallback(
    (msg: VoiceServerMessage) => {
      switch (msg.type) {
        case 'audio':
          if (msg.data) {
            playbackQueueRef.current.push(msg.data);
            processPlaybackQueue();
          }
          break;

        case 'text':
          if (msg.text) {
            setTranscript((prev) => prev + msg.text);
          }
          break;

        case 'interrupted':
          setIsAiSpeaking(false);
          playbackQueueRef.current = [];
          break;

        case 'error':
          setErrorMessage(msg.message || '語音連線錯誤');
          setStatus('error');
          break;

        case 'connected':
          setStatus('connected');
          break;
      }
    },
    [processPlaybackQueue]
  );

  /**
   * Start capturing microphone and streaming to Gemini.
   */
  const startMicrophoneCapture = useCallback(async () => {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        sampleRate: 16000,
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
      },
    });
    streamRef.current = stream;

    const ctx = new AudioContext({ sampleRate: 16000 });
    audioContextRef.current = ctx;

    const source = ctx.createMediaStreamSource(stream);

    // Use ScriptProcessorNode for PCM capture (AudioWorklet needs more setup)
    const processor = ctx.createScriptProcessor(4096, 1, 1);
    processor.onaudioprocess = (e: AudioProcessingEvent) => {
      if (!clientRef.current?.isConnected) return;

      const float32Data = e.inputBuffer.getChannelData(0);
      // Convert float32 to int16 PCM
      const int16 = new Int16Array(float32Data.length);
      for (let i = 0; i < float32Data.length; i++) {
        const s = Math.max(-1, Math.min(1, float32Data[i]));
        int16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
      }

      // Convert to base64
      const bytes = new Uint8Array(int16.buffer);
      let binary = '';
      for (let i = 0; i < bytes.length; i++) {
        binary += String.fromCharCode(bytes[i]);
      }
      const base64 = btoa(binary);

      clientRef.current.sendAudio(base64, 'audio/pcm');
    };

    source.connect(processor);
    processor.connect(ctx.destination);
    processorRef.current = processor as unknown as AudioWorkletNodeLike;

    setStatus('recording');
  }, []);

  /**
   * Connect to the voice chat server and start recording.
   */
  const startVoiceChat = useCallback(async () => {
    setStatus('connecting');
    setTranscript('');
    setErrorMessage('');
    playbackQueueRef.current = [];

    const client = new VoiceClient();
    clientRef.current = client;

    try {
      await client.connect({
        onMessage: handleServerMessage,
        onClose: () => {
          setStatus('idle');
          setIsAiSpeaking(false);
        },
        onError: () => {
          setStatus('error');
          setErrorMessage('語音連線失敗');
        },
      });

      await startMicrophoneCapture();
    } catch {
      setStatus('error');
      setErrorMessage('無法建立語音連線');
    }
  }, [handleServerMessage, startMicrophoneCapture]);

  /**
   * Stop voice chat and clean up resources.
   */
  const stopVoiceChat = useCallback(() => {
    // Stop microphone
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    // Disconnect processor
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }

    // Close audio context
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    // Disconnect from server
    if (clientRef.current) {
      clientRef.current.disconnect();
      clientRef.current = null;
    }

    playbackQueueRef.current = [];
    isPlayingRef.current = false;
    setStatus('idle');
    setIsAiSpeaking(false);
  }, []);

  /**
   * Send a text prompt to interrupt the current voice conversation.
   * This sends text through the WebSocket to interrupt Gemini's audio output.
   */
  const sendTextInterrupt = useCallback((text: string) => {
    if (clientRef.current?.isConnected && text.trim()) {
      clientRef.current.sendTextInterrupt(text);
      setTranscript((prev) => prev + `\n[文字中斷] ${text}\n`);
      // Clear playback queue since we're interrupting
      playbackQueueRef.current = [];
      setIsAiSpeaking(false);
    }
  }, []);

  return {
    status,
    transcript,
    isAiSpeaking,
    errorMessage,
    startVoiceChat,
    stopVoiceChat,
    sendTextInterrupt,
  };
}
