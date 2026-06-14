"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export type WebcamStatus = "idle" | "requesting" | "active" | "error";

export type UseWebcamOptions = {
  width?: number;
  height?: number;
  facingMode?: "user" | "environment";
  /** Espeja horizontalmente la captura (como la vista previa selfie). */
  mirror?: boolean;
};

function isPlayInterrupted(err: unknown): boolean {
  if (!(err instanceof Error)) return false;
  return (
    err.name === "AbortError" ||
    err.message.includes("interrupted") ||
    err.message.includes("aborted")
  );
}

export function useWebcam(options: UseWebcamOptions = {}) {
  const { width = 640, height = 480, facingMode = "user", mirror = false } = options;
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const startSessionRef = useRef(0);
  const [status, setStatus] = useState<WebcamStatus>("idle");
  const [error, setError] = useState<string | null>(null);

  const stop = useCallback(() => {
    startSessionRef.current += 1;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setStatus("idle");
  }, []);

  const start = useCallback(async () => {
    stop();
    const session = startSessionRef.current;
    setError(null);
    setStatus("requesting");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width, height, facingMode },
        audio: false,
      });
      if (session !== startSessionRef.current) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }
      streamRef.current = stream;
      const video = videoRef.current;
      if (!video) {
        stream.getTracks().forEach((track) => track.stop());
        setStatus("idle");
        return;
      }
      video.srcObject = stream;
      try {
        await video.play();
      } catch (playErr) {
        if (session !== startSessionRef.current || isPlayInterrupted(playErr)) {
          return;
        }
        throw playErr;
      }
      if (session !== startSessionRef.current) return;
      setStatus("active");
    } catch (err) {
      if (session !== startSessionRef.current) return;
      const message =
        err instanceof Error
          ? err.message
          : "No se pudo acceder a la cámara. Verificá los permisos.";
      setError(message);
      setStatus("error");
    }
  }, [width, height, facingMode, stop]);

  const captureFrame = useCallback(async (): Promise<Blob | null> => {
    const video = videoRef.current;
    if (!video || video.readyState < 2) return null;

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || width;
    canvas.height = video.videoHeight || height;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    if (mirror) {
      const mirrored = document.createElement("canvas");
      mirrored.width = canvas.width;
      mirrored.height = canvas.height;
      const mctx = mirrored.getContext("2d");
      if (!mctx) return null;
      mctx.translate(canvas.width, 0);
      mctx.scale(-1, 1);
      mctx.drawImage(canvas, 0, 0);
      return new Promise((resolve) => {
        mirrored.toBlob((blob) => resolve(blob), "image/jpeg", 0.92);
      });
    }

    return new Promise((resolve) => {
      canvas.toBlob((blob) => resolve(blob), "image/jpeg", 0.92);
    });
  }, [width, height, mirror]);

  const captureFrames = useCallback(
    async (count: number, delayMs = 300): Promise<Blob[]> => {
      const frames: Blob[] = [];
      for (let i = 0; i < count; i++) {
        const frame = await captureFrame();
        if (frame) frames.push(frame);
        if (i < count - 1) {
          await new Promise((r) => setTimeout(r, delayMs));
        }
      }
      return frames;
    },
    [captureFrame],
  );

  useEffect(() => {
    return () => stop();
  }, [stop]);

  return {
    videoRef,
    status,
    error,
    start,
    stop,
    captureFrame,
    captureFrames,
  };
}
