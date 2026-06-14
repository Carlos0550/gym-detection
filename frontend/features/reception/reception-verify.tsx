"use client";

import { useMutation } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { verifyFace } from "@/lib/api/access";
import type { ApiError, VerifyFaceResponse } from "@/lib/types/api";
import { useWebcam } from "@/hooks/use-webcam";
import { cn } from "@/lib/utils";

type Props = {
  gymId: string;
};

type VerifyState = "idle" | "verifying" | "result";

function ResultCard({ result }: { result: VerifyFaceResponse }) {
  const isGranted = result.access === "granted" && result.result === "granted";
  const isUnknown = result.result === "unknown";
  const isLiveness =
    result.reason?.toLowerCase().includes("vivacidad") ||
    result.reason?.toLowerCase().includes("liveness");
  const isLowConfidence = result.result === "low_confidence";

  let title = "Acceso denegado";
  let variant: "success" | "warning" | "error" = "error";

  if (isGranted) {
    title = "Acceso permitido";
    variant = "success";
  } else if (isUnknown) {
    title = "Sin coincidencia";
    variant = "warning";
  } else if (isLiveness) {
    title = "Vivacidad fallida";
    variant = "warning";
  } else if (isLowConfidence) {
    title = "Confianza insuficiente";
    variant = "warning";
  }

  return (
    <Card
      className={cn(
        "border-2",
        variant === "success" && "border-success/40 bg-success/10",
        variant === "warning" && "border-warning/40 bg-warning/10",
        variant === "error" && "border-destructive/40 bg-destructive/10",
      )}
    >
      <CardHeader>
        <div className="flex items-center gap-3">
          <span
            className={cn(
              "h-2 w-2 rounded-full",
              variant === "success" && "bg-success",
              variant === "warning" && "bg-warning",
              variant === "error" && "bg-destructive",
            )}
          />
          <CardTitle className="text-xl">{title}</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        {result.user && (
          <p>
            <span className="font-mono text-[10px] uppercase tracking-[0.08em] text-muted-2">
              Persona
            </span>
            <br />
            <span className="font-medium">{result.user.full_name}</span>
            {result.user.document ? ` · DNI ${result.user.document}` : ""}
          </p>
        )}
        {result.confidence != null && (
          <p>
            <span className="font-mono text-[10px] uppercase tracking-[0.08em] text-muted-2">
              Confianza
            </span>
            <br />
            <span className="font-mono text-lg text-primary">
              {(result.confidence * 100).toFixed(1)}%
            </span>
          </p>
        )}
        {result.reason && (
          <p className="text-muted-foreground">
            <span className="font-mono text-[10px] uppercase tracking-[0.08em] text-muted-2">
              Motivo
            </span>
            <br />
            {result.reason}
          </p>
        )}
        {result.membership && (
          <Badge variant="outline">Membresía: {result.membership.status}</Badge>
        )}
      </CardContent>
    </Card>
  );
}

export function ReceptionVerify({ gymId }: Props) {
  const { videoRef, status, error, start, captureFrames } = useWebcam({
    facingMode: "user",
  });
  const [verifyState, setVerifyState] = useState<VerifyState>("idle");
  const [lastResult, setLastResult] = useState<VerifyFaceResponse | null>(null);
  const [autoMode, setAutoMode] = useState(false);
  const verifyingRef = useRef(false);

  const clearResult = useCallback(() => {
    setLastResult(null);
    setVerifyState("idle");
  }, []);

  useEffect(() => {
    void start();
  }, [start]);

  useEffect(() => {
    if (!lastResult) return;

    const timer = setTimeout(clearResult, 2000);
    return () => clearTimeout(timer);
  }, [clearResult, lastResult]);

  const mutation = useMutation({
    mutationFn: (frames: Blob[]) => verifyFace(gymId, frames),
    onSuccess: (data) => {
      setLastResult(data);
      setVerifyState("result");
    },
    onError: (err: ApiError) => {
      toast.error(err.detail);
      setVerifyState("idle");
    },
    onSettled: () => {
      verifyingRef.current = false;
    },
  });

  const runVerify = useCallback(async () => {
    if (verifyingRef.current || status !== "active") return;
    verifyingRef.current = true;
    setVerifyState("verifying");

    const frames = await captureFrames(3, 250);
    if (frames.length < 2) {
      toast.error("Se necesitan al menos 2 frames para verificar vivacidad");
      setVerifyState("idle");
      verifyingRef.current = false;
      return;
    }

    mutation.mutate(frames);
  }, [captureFrames, mutation, status]);

  useEffect(() => {
    if (!autoMode || status !== "active") return;

    const interval = setInterval(() => {
      if (verifyState === "idle") {
        void runVerify();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [autoMode, runVerify, status, verifyState]);

  return (
    <div className="space-y-6">
      <PageHeader
        breadcrumbs={[
          { label: "Verifica", href: "/members" },
          { label: "Panel" },
          { label: "Recepción" },
        ]}
        title={
          <>
            Recepción <span className="text-primary">en vivo.</span>
          </>
        }
        subtitle="Verificación facial con detección de vivacidad (mín. 2 frames)."
        meta={
          <span className="head-pill">
            <span
              className={cn(
                "h-1.5 w-1.5 rounded-full",
                status === "active" ? "bg-success" : "bg-muted-2",
              )}
            />
            {status === "active" ? "Cámara activa" : "Cámara inactiva"}
          </span>
        }
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <div className="section-tag">En vivo</div>
            <CardTitle className="mt-2">Cámara de recepción</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="webcam-frame">
              <video
                ref={videoRef}
                className="h-full w-full object-cover"
                playsInline
                muted
              />
              {verifyState === "verifying" && (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-background/80 backdrop-blur-sm">
                  <div className="mb-2 h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                  <p className="font-mono text-[11px] uppercase tracking-[0.08em] text-primary">
                    Verificando...
                  </p>
                </div>
              )}
              {status === "active" && verifyState !== "verifying" && (
                <div className="pointer-events-none absolute inset-x-0 top-3 flex justify-center">
                  <span className="rounded-full border border-primary/30 bg-background/80 px-3 py-1 font-mono text-[10px] uppercase tracking-[0.08em] text-primary backdrop-blur-sm">
                    Encuadre el rostro
                  </span>
                </div>
              )}
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <div className="flex flex-wrap gap-2">
              <Button
                onClick={() => void runVerify()}
                disabled={verifyState === "verifying" || status !== "active"}
              >
                Verificar ahora
              </Button>
              <Button
                variant={autoMode ? "default" : "outline"}
                onClick={() => {
                  setAutoMode((v) => !v);
                  clearResult();
                }}
              >
                {autoMode ? "Modo automático ON" : "Modo automático OFF"}
              </Button>
            </div>
          </CardContent>
        </Card>

        <div>
          {lastResult ? (
            <ResultCard result={lastResult} />
          ) : (
            <Card className="flex h-full min-h-[320px] items-center justify-center">
              <CardContent className="py-12 text-center">
                <div className="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-xl border border-border bg-surface-2 text-muted-2">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    className="h-6 w-6"
                    strokeWidth={1.5}
                  >
                    <path d="M9 12l2 2l4 -4" />
                    <circle cx="12" cy="12" r="9" />
                  </svg>
                </div>
                <p className="text-sm text-muted-foreground">
                  El resultado de la verificación aparecerá aquí
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
