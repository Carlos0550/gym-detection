"use client";

import { useMutation } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { playAccessDeniedSound, playAccessGrantedSound } from "@/lib/access-sounds";
import { formatConfidence } from "@/lib/confidence";
import { humanizeError } from "@/lib/errors";
import { verifyFace } from "@/lib/api/access";
import type { ApiError, VerifyFaceResponse } from "@/lib/types/api";
import { useWebcam } from "@/hooks/use-webcam";
import { cn } from "@/lib/utils";

type Props = {
  gymId: string;
};

type VerifyState = "idle" | "verifying" | "result";

function ConfidenceDisplay({ confidence }: { confidence: number }) {
  const { level, percent } = formatConfidence(confidence);

  return (
    <p>
      <span className="font-mono text-[10px] uppercase tracking-[0.08em] text-muted-2">
        Coincidencia
      </span>
      <br />
      <span className="text-lg font-semibold">{level}</span>
      <span className="ml-1.5 font-mono text-xs text-muted-2">({percent})</span>
    </p>
  );
}

function ResultCard({ result }: { result: VerifyFaceResponse }) {
  const isGranted = result.access === "granted" && result.result === "granted";
  const isUnknown = result.result === "unknown";
  const isLiveness =
    result.reason?.toLowerCase().includes("vivacidad") ||
    result.reason?.toLowerCase().includes("liveness") ||
    result.reason?.toLowerCase().includes("movimiento");
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
    title = "Verificación en vivo fallida";
    variant = "warning";
  } else if (isLowConfidence) {
    title = "Coincidencia insuficiente";
    variant = "warning";
  }

  const reasonText = result.reason
    ? humanizeError(result.reason, "reception")
    : null;

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
        {result.confidence != null && <ConfidenceDisplay confidence={result.confidence} />}
        {reasonText && (
          <p className="text-muted-foreground">
            <span className="font-mono text-[10px] uppercase tracking-[0.08em] text-muted-2">
              Motivo
            </span>
            <br />
            {reasonText}
          </p>
        )}
        {result.membership && (
          <Badge variant="outline">Membresía: {result.membership.status}</Badge>
        )}
      </CardContent>
    </Card>
  );
}

function ResultPanel({
  lastResult,
  onClear,
}: {
  lastResult: VerifyFaceResponse | null;
  onClear: () => void;
}) {
  return (
    <div aria-live="polite" aria-atomic="true" className="space-y-3">
      {lastResult ? (
        <>
          <ResultCard result={lastResult} />
          <Button variant="outline" onClick={onClear} className="w-full">
            Limpiar resultado
          </Button>
        </>
      ) : (
        <Card className="flex h-full min-h-[200px] items-center justify-center lg:min-h-[320px]">
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

  const mutation = useMutation({
    mutationFn: (frames: Blob[]) => verifyFace(gymId, frames),
    onSuccess: (data) => {
      setLastResult(data);
      setVerifyState("result");

      const granted = data.access === "granted" && data.result === "granted";
      if (granted) {
        playAccessGrantedSound();
      } else {
        playAccessDeniedSound();
      }
    },
    onError: (err: ApiError) => {
      toast.error(err.detail, { duration: 12000 });
      setVerifyState(lastResult ? "result" : "idle");
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
      toast.error("Se necesitan al menos 2 fotos para verificar identidad", {
        duration: 12000,
      });
      setVerifyState(lastResult ? "result" : "idle");
      verifyingRef.current = false;
      return;
    }

    mutation.mutate(frames);
  }, [captureFrames, lastResult, mutation, status]);

  useEffect(() => {
    if (!autoMode || status !== "active") return;

    const interval = setInterval(() => {
      if (verifyState !== "verifying") {
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
        subtitle="Verificá el acceso con la cámara de recepción. Se capturan 2 fotos por intento."
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
        <div className="order-1 space-y-3 lg:order-2">
          <ResultPanel lastResult={lastResult} onClear={clearResult} />
        </div>

        <Card className="order-2 lg:order-1">
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
                    Encuadrá el rostro
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
                onClick={() => setAutoMode((v) => !v)}
              >
                {autoMode ? "Pausar escaneo" : "Escaneo continuo"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
