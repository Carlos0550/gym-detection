"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertCircle, CheckCircle2 } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { humanizeError } from "@/lib/errors";
import { enrollFace, validateEnrollPose } from "@/lib/api/face";
import { listGymClients } from "@/lib/api/users";
import type { ApiError } from "@/lib/types/api";
import { useWebcam } from "@/hooks/use-webcam";
import { cn } from "@/lib/utils";

type Props = {
  gymId: string;
  userId: string;
};

const GUIDED_STEPS = [
  {
    key: "center",
    label: "Centrar",
    title: "Centrá tu rostro",
    hint: "Mirá a la cámara y ubicá tu cara dentro del marco amarillo.",
  },
  {
    key: "left",
    label: "Izquierda",
    title: "Girá a la izquierda",
    hint: "Girá la cabeza lentamente hacia tu hombro izquierdo y mantené la pose.",
  },
  {
    key: "right",
    label: "Derecha",
    title: "Girá a la derecha",
    hint: "Girá la cabeza lentamente hacia tu hombro derecho y mantené la pose.",
  },
] as const;

type EnrollPoseStep = (typeof GUIDED_STEPS)[number]["key"];

const TIMING = {
  PREPARING_MS: 1200,
  COUNTDOWN_SECONDS: 3,
  HOLD_MS: 1000,
  FLASH_MS: 400,
  STEP_TRANSITION_MS: 350,
} as const;

type EnrollPhase =
  | "idle"
  | "preparing"
  | "countdown"
  | "hold"
  | "capturing"
  | "submitting"
  | "done";

type PanelErrorKind = "pose" | "capture" | "submit";

type PanelError = {
  message: string;
  kind: PanelErrorKind;
};

const CAPTURE_FLOW_PHASES: EnrollPhase[] = [
  "preparing",
  "countdown",
  "hold",
  "capturing",
];

export function EnrollCapture({ gymId, userId }: Props) {
  const queryClient = useQueryClient();
  const { videoRef, status, error, start, captureFrame } = useWebcam({ mirror: true });
  const [stepIndex, setStepIndex] = useState(0);
  const [capturedFrames, setCapturedFrames] = useState<Blob[]>([]);
  const [previewUrls, setPreviewUrls] = useState<string[]>([]);
  const [phase, setPhase] = useState<EnrollPhase>("idle");
  const [countdown, setCountdown] = useState<number>(TIMING.COUNTDOWN_SECONDS);
  const [flashActive, setFlashActive] = useState(false);
  const [panelError, setPanelError] = useState<PanelError | null>(null);
  const captureLockRef = useRef(false);
  const captureRunRef = useRef(false);

  const { data: members = [], isLoading } = useQuery({
    queryKey: ["members", gymId],
    queryFn: () => listGymClients(gymId),
    enabled: !!gymId,
  });

  const member = members.find((m) => m.id === userId);
  const hasConsent = !!member?.biometric_consent_at;

  useEffect(() => {
    void start();
  }, [start]);

  const mutation = useMutation({
    mutationFn: (frames: Blob[]) => enrollFace(gymId, userId, frames),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["members", gymId] });
      void queryClient.invalidateQueries({ queryKey: ["face", gymId, userId] });
      toast.success("Rostro registrado correctamente", { duration: 8000 });
      setPhase("done");
    },
    onError: (err: ApiError) => {
      setPanelError({
        message: humanizeError(
          err.detail ?? "Error al registrar el rostro",
          "enroll",
        ),
        kind: "submit",
      });
      setPhase("idle");
      captureLockRef.current = false;
      captureRunRef.current = false;
      setFlashActive(false);
    },
  });

  const submitFrames = useCallback(
    (frames: Blob[]) => {
      setPhase("submitting");
      mutation.mutate(frames);
    },
    [mutation],
  );

  const resetCaptureFlow = useCallback(() => {
    captureLockRef.current = false;
    captureRunRef.current = false;
    setFlashActive(false);
    setPhase("idle");
    setCountdown(TIMING.COUNTDOWN_SECONDS);
  }, []);

  const runCaptureSequence = useCallback(async () => {
    setPanelError(null);
    setFlashActive(true);

    await new Promise((resolve) => setTimeout(resolve, TIMING.FLASH_MS * 0.45));

    const blob = await captureFrame();

    await new Promise((resolve) => setTimeout(resolve, TIMING.FLASH_MS * 0.55));
    setFlashActive(false);

    if (!blob) {
      setPanelError({
        message: humanizeError(
          "No se pudo capturar la imagen. Revisá la cámara e intentá de nuevo.",
          "enroll",
        ),
        kind: "capture",
      });
      resetCaptureFlow();
      return;
    }

    const step = GUIDED_STEPS[stepIndex]?.key as EnrollPoseStep | undefined;
    if (!step) {
      resetCaptureFlow();
      return;
    }

    try {
      await validateEnrollPose(gymId, userId, step, blob);
    } catch (err) {
      const apiErr = err as ApiError;
      const message = humanizeError(
        apiErr.detail ?? "Pose incorrecta para este paso",
        "enroll",
      );
      setPanelError({ message, kind: "pose" });
      resetCaptureFlow();
      return;
    }

    const nextFrames = [...capturedFrames, blob];
    const nextPreviews = [...previewUrls, URL.createObjectURL(blob)];
    setCapturedFrames(nextFrames);
    setPreviewUrls(nextPreviews);

    if (nextFrames.length >= GUIDED_STEPS.length) {
      submitFrames(nextFrames);
      return;
    }

    await new Promise((resolve) => setTimeout(resolve, TIMING.STEP_TRANSITION_MS));

    setStepIndex(nextFrames.length);
    resetCaptureFlow();
  }, [
    captureFrame,
    capturedFrames,
    gymId,
    previewUrls,
    resetCaptureFlow,
    stepIndex,
    submitFrames,
    userId,
  ]);

  const startManualCapture = useCallback(() => {
    if (captureLockRef.current || status !== "active") return;
    captureLockRef.current = true;
    captureRunRef.current = false;
    setFlashActive(false);
    setPhase("capturing");
  }, [status]);

  useEffect(() => {
    if (
      phase !== "idle" ||
      !hasConsent ||
      status !== "active" ||
      stepIndex >= GUIDED_STEPS.length ||
      capturedFrames.length !== stepIndex ||
      captureLockRef.current
    ) {
      return;
    }

    setPhase("preparing");
    setCountdown(TIMING.COUNTDOWN_SECONDS);
  }, [capturedFrames.length, hasConsent, phase, status, stepIndex]);

  useEffect(() => {
    if (phase !== "preparing") return;

    const timer = setTimeout(() => {
      setPhase("countdown");
      setCountdown(TIMING.COUNTDOWN_SECONDS);
    }, TIMING.PREPARING_MS);

    return () => clearTimeout(timer);
  }, [phase]);

  useEffect(() => {
    if (phase !== "countdown") return;

    if (countdown === 0) {
      setPhase("hold");
      return;
    }

    const timer = setTimeout(() => setCountdown((value) => value - 1), 1000);
    return () => clearTimeout(timer);
  }, [countdown, phase]);

  useEffect(() => {
    if (phase !== "hold") return;

    const timer = setTimeout(() => {
      captureLockRef.current = true;
      captureRunRef.current = false;
      setPhase("capturing");
    }, TIMING.HOLD_MS);

    return () => clearTimeout(timer);
  }, [phase]);

  useEffect(() => {
    if (phase !== "capturing") {
      captureRunRef.current = false;
      return;
    }
    if (captureRunRef.current) return;

    captureRunRef.current = true;
    void runCaptureSequence();
  }, [phase, runCaptureSequence]);

  const resetFlow = () => {
    previewUrls.forEach((url) => URL.revokeObjectURL(url));
    setPreviewUrls([]);
    setCapturedFrames([]);
    setStepIndex(0);
    setPhase("idle");
    setCountdown(TIMING.COUNTDOWN_SECONDS);
    setPanelError(null);
    captureLockRef.current = false;
    captureRunRef.current = false;
    setFlashActive(false);
    void start();
  };

  const retryFromPanelError = () => {
    if (panelError?.kind === "submit") {
      resetFlow();
      return;
    }
    setPanelError(null);
    resetCaptureFlow();
  };

  if (isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  if (!member) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-muted-foreground">
          Miembro no encontrado.
          <div className="mt-4">
            <Button asChild variant="outline">
              <Link href="/members">Volvé a miembros</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (phase === "done") {
    return (
      <div className="space-y-6">
        <PageHeader
          breadcrumbs={[
            { label: "Verifica", href: "/members" },
            { label: "Miembros", href: "/members" },
            { label: "Registro facial" },
          ]}
          title={
            <>
              Registro facial <span className="text-primary">completado.</span>
            </>
          }
          subtitle={member.full_name}
        />

        <Card className="border-success/40 bg-success/5">
          <CardContent className="flex flex-col items-center py-16 text-center">
            <div className="mb-6 grid h-20 w-20 place-items-center rounded-full border-2 border-success/40 bg-success/10">
              <CheckCircle2 className="h-10 w-10 text-success" strokeWidth={1.5} />
            </div>
            <h2 className="text-2xl font-semibold tracking-tight">
              Rostro registrado correctamente
            </h2>
            <p className="mt-2 text-muted-foreground">
              {member.full_name}
              {member.document ? ` · DNI ${member.document}` : ""}
            </p>
            <p className="mt-1 max-w-md text-sm text-muted-2">
              Ya podés verificar el acceso de este miembro en recepción.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <Button asChild size="lg">
                <Link href="/members">Volvé a miembros</Link>
              </Button>
              <Button variant="outline" size="lg" onClick={resetFlow}>
                Registrar otro
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const currentStep = GUIDED_STEPS[stepIndex];
  const isBusy = phase === "submitting" || mutation.isPending;
  const isInCaptureFlow = CAPTURE_FLOW_PHASES.includes(phase);
  const framePulse = phase === "hold" || phase === "capturing";
  const overlayLabel =
    phase === "preparing"
      ? "Preparate…"
      : phase === "hold"
        ? "¡Mantené la pose!"
        : phase === "capturing"
          ? "Capturando…"
          : null;

  return (
    <div className="space-y-6">
      <PageHeader
        breadcrumbs={[
          { label: "Verifica", href: "/members" },
          { label: "Miembros", href: "/members" },
          { label: "Registro facial" },
        ]}
        title={
          <>
            Registro facial <span className="text-primary">guiado.</span>
          </>
        }
        subtitle={`${member.full_name} · DNI ${member.document ?? "—"}`}
        meta={
          <span className="head-pill">
            <span
              className={cn(
                "h-1.5 w-1.5 rounded-full",
                hasConsent ? "bg-success" : "bg-warning",
              )}
            />
            {hasConsent ? "Consentimiento OK" : "Sin consentimiento"}
          </span>
        }
        actions={
          <Button asChild variant="outline">
            <Link href="/members">Volvé</Link>
          </Button>
        }
      />

      {!hasConsent && (
        <Card className="border-destructive/40 bg-destructive/10">
          <CardContent className="py-4 text-sm text-destructive">
            Este miembro no tiene consentimiento biométrico. Marcá el consentimiento en la lista de
            miembros antes de registrar el rostro.
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <div className="section-tag">Captura guiada</div>
            <CardTitle className="mt-2">Registro facial paso a paso</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              {GUIDED_STEPS.map((step, index) => {
                const done = index < capturedFrames.length;
                const active = index === stepIndex && !isBusy;
                return (
                  <div
                    key={step.label}
                    className={cn(
                      "flex flex-1 flex-col items-center gap-1 rounded-lg border px-2 py-2 text-center",
                      done && "border-success/40 bg-success/10",
                      active && "border-primary/40 bg-primary/10",
                      !done && !active && "border-border bg-surface-2",
                    )}
                  >
                    <span className="font-mono text-[10px] uppercase tracking-[0.08em] text-muted-2">
                      Paso {index + 1}
                    </span>
                    <span className="text-xs font-medium">{step.label}</span>
                  </div>
                );
              })}
            </div>

            <div className="webcam-frame overflow-hidden">
              <video
                ref={videoRef}
                className={cn(
                  "h-full w-full scale-x-[-1] object-cover transition-opacity duration-300",
                  phase === "capturing" && flashActive && "opacity-90",
                )}
                playsInline
                muted
              />
              <div
                aria-hidden
                className={cn(
                  "pointer-events-none absolute inset-0 bg-white transition-opacity duration-150 ease-out",
                  flashActive ? "opacity-75" : "opacity-0",
                )}
              />
              {status !== "active" && (
                <div className="absolute inset-0 flex items-center justify-center bg-background/80 text-sm text-muted-foreground backdrop-blur-sm">
                  {status === "requesting" ? "Solicitando cámara..." : "Cámara inactiva"}
                </div>
              )}
              {status === "active" && hasConsent && !isBusy && (
                <>
                  <div
                    className={cn(
                      "pointer-events-none absolute inset-4 rounded-lg border-2 transition-all duration-300",
                      framePulse
                        ? "animate-pulse border-warning shadow-[0_0_24px_rgba(234,179,8,0.35)]"
                        : "border-primary/30",
                    )}
                  />
                  <div className="pointer-events-none absolute inset-x-0 top-3 flex justify-center px-4">
                    <div
                      className={cn(
                        "max-w-sm rounded-xl border border-primary/30 bg-background/90 px-4 py-3 text-center backdrop-blur-sm transition-opacity duration-300",
                        overlayLabel && "opacity-80",
                      )}
                    >
                      <p className="font-mono text-[10px] uppercase tracking-[0.08em] text-primary">
                        {currentStep?.title ?? "Completado"}
                      </p>
                      <p className="mt-1 text-sm text-foreground">
                        {currentStep?.hint ?? "Procesando..."}
                      </p>
                    </div>
                  </div>
                  {phase === "countdown" && countdown > 0 && (
                    <div className="absolute inset-0 flex items-center justify-center bg-background/50 backdrop-blur-[1px] transition-opacity duration-300">
                      <span className="grid h-20 w-20 place-items-center rounded-full border-2 border-primary bg-background/90 font-mono text-3xl text-primary transition-transform duration-300 animate-in zoom-in-95">
                        {countdown}
                      </span>
                    </div>
                  )}
                  {overlayLabel && (
                    <div
                      aria-live="polite"
                      className="absolute inset-0 flex items-center justify-center bg-background/35 backdrop-blur-[1px] transition-opacity duration-300 animate-in fade-in"
                    >
                      <span
                        className={cn(
                          "rounded-2xl border px-6 py-4 text-center shadow-lg backdrop-blur-sm transition-transform duration-300",
                          phase === "hold"
                            ? "border-warning/50 bg-warning/10 text-2xl font-semibold text-warning animate-pulse"
                            : phase === "capturing"
                              ? "border-primary/40 bg-background/90 font-mono text-sm uppercase tracking-[0.12em] text-primary"
                              : "border-border/60 bg-background/85 text-lg font-medium text-muted-foreground",
                        )}
                      >
                        {overlayLabel}
                      </span>
                    </div>
                  )}
                </>
              )}
              {isBusy && (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-background/80 backdrop-blur-sm">
                  <div className="mb-2 h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                  <p className="font-mono text-[11px] uppercase tracking-[0.08em] text-primary">
                    Verificando identidad…
                  </p>
                </div>
              )}
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <div className="flex flex-wrap gap-2">
              <Button onClick={resetFlow} variant="outline" type="button" disabled={isBusy}>
                Reiniciar proceso
              </Button>
              <Button
                onClick={startManualCapture}
                disabled={
                  !hasConsent ||
                  isBusy ||
                  status !== "active" ||
                  phase === "capturing"
                }
                type="button"
              >
                {isInCaptureFlow ? "Capturar ahora" : "Capturar paso"}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="section-tag">Vista previa</div>
            <CardTitle className="mt-2">Fotos capturadas</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {previewUrls.length > 0 ? (
              <div className="grid grid-cols-3 gap-2">
                {previewUrls.map((url, index) => (
                  <div key={url} className="space-y-1">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={url}
                      alt={`Paso ${index + 1}`}
                      className="aspect-[3/4] w-full rounded-lg border border-border object-cover animate-in fade-in duration-300"
                    />
                    <p className="text-center font-mono text-[10px] uppercase tracking-[0.08em] text-muted-2">
                      {GUIDED_STEPS[index]?.label}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex aspect-[4/3] flex-col items-center justify-center rounded-lg border border-dashed border-border bg-surface-2 text-sm text-muted-foreground">
                <p>Seguí las instrucciones en la cámara</p>
                <p className="mt-1 text-xs text-muted-2">
                  Centro → izquierda → derecha
                </p>
              </div>
            )}

            {panelError && (
              <div
                aria-live="polite"
                aria-atomic="true"
                className="rounded-lg border border-destructive/40 bg-destructive/10 p-4"
                role="alert"
              >
                <div className="flex gap-3">
                  <AlertCircle
                    className="mt-0.5 h-5 w-5 shrink-0 text-destructive"
                    aria-hidden
                  />
                  <div className="min-w-0 space-y-3">
                    <div>
                      <p className="font-mono text-[10px] uppercase tracking-[0.08em] text-destructive/80">
                        {panelError.kind === "submit"
                          ? "Registro fallido"
                          : panelError.kind === "pose"
                            ? "Pose incorrecta"
                            : "Captura fallida"}
                      </p>
                      <p className="mt-1 text-sm text-destructive">{panelError.message}</p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      type="button"
                      onClick={retryFromPanelError}
                      disabled={isBusy}
                      className="border-destructive/30 hover:bg-destructive/10"
                    >
                      {panelError.kind === "submit"
                        ? "Reiniciar captura"
                        : "Volver a intentar"}
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
