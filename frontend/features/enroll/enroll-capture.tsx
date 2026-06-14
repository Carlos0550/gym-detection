"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
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

const COUNTDOWN_SECONDS = 3;

type EnrollPhase = "idle" | "countdown" | "submitting" | "done";

export function EnrollCapture({ gymId, userId }: Props) {
  const { videoRef, status, error, start, captureFrame } = useWebcam({ mirror: true });
  const [stepIndex, setStepIndex] = useState(0);
  const [capturedFrames, setCapturedFrames] = useState<Blob[]>([]);
  const [previewUrls, setPreviewUrls] = useState<string[]>([]);
  const [phase, setPhase] = useState<EnrollPhase>("idle");
  const [countdown, setCountdown] = useState(COUNTDOWN_SECONDS);
  const [stepError, setStepError] = useState<string | null>(null);
  const captureLockRef = useRef(false);

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
      toast.success("Rostro enrolado correctamente");
      setPhase("done");
    },
    onError: (err: ApiError) => {
      toast.error(err.detail);
      setPhase("idle");
      captureLockRef.current = false;
    },
  });

  const submitFrames = useCallback(
    (frames: Blob[]) => {
      setPhase("submitting");
      mutation.mutate(frames);
    },
    [mutation],
  );

  const captureCurrentStep = useCallback(async () => {
    if (captureLockRef.current || status !== "active") return;
    captureLockRef.current = true;
    setStepError(null);

    const blob = await captureFrame();
    if (!blob) {
      toast.error("No se pudo capturar la imagen");
      captureLockRef.current = false;
      setPhase("idle");
      setCountdown(COUNTDOWN_SECONDS);
      return;
    }

    const step = GUIDED_STEPS[stepIndex]?.key as EnrollPoseStep | undefined;
    if (!step) {
      captureLockRef.current = false;
      return;
    }

    try {
      await validateEnrollPose(gymId, userId, step, blob);
    } catch (err) {
      const apiErr = err as ApiError;
      const message = apiErr.detail ?? "Pose incorrecta para este paso";
      setStepError(message);
      toast.error(message);
      captureLockRef.current = false;
      setPhase("idle");
      setCountdown(COUNTDOWN_SECONDS);
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

    setStepIndex(nextFrames.length);
    setPhase("idle");
    setCountdown(COUNTDOWN_SECONDS);
    captureLockRef.current = false;
  }, [
    captureFrame,
    capturedFrames,
    gymId,
    previewUrls,
    status,
    stepIndex,
    submitFrames,
    userId,
  ]);

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

    setPhase("countdown");
    setCountdown(COUNTDOWN_SECONDS);
  }, [capturedFrames.length, hasConsent, phase, status, stepIndex]);

  useEffect(() => {
    if (phase !== "countdown") return;

    if (countdown <= 0) {
      void captureCurrentStep();
      return;
    }

    const timer = setTimeout(() => setCountdown((value) => value - 1), 1000);
    return () => clearTimeout(timer);
  }, [captureCurrentStep, countdown, phase]);

  const resetFlow = () => {
    previewUrls.forEach((url) => URL.revokeObjectURL(url));
    setPreviewUrls([]);
    setCapturedFrames([]);
    setStepIndex(0);
    setPhase("idle");
    setCountdown(COUNTDOWN_SECONDS);
    setStepError(null);
    captureLockRef.current = false;
    void start();
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
              <Link href="/members">Volver a miembros</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  const currentStep = GUIDED_STEPS[stepIndex];
  const isBusy = phase === "submitting" || mutation.isPending;

  return (
    <div className="space-y-6">
      <PageHeader
        breadcrumbs={[
          { label: "Verifica", href: "/members" },
          { label: "Miembros", href: "/members" },
          { label: "Enrolamiento" },
        ]}
        title={
          <>
            Enrolamiento <span className="text-primary">facial.</span>
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
            <Link href="/members">Volver</Link>
          </Button>
        }
      />

      {!hasConsent && (
        <Card className="border-destructive/40 bg-destructive/10">
          <CardContent className="py-4 text-sm text-destructive">
            Este miembro no tiene consentimiento biométrico. Marcá el consentimiento en la
            lista de miembros antes de enrolar.
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <div className="section-tag">Captura guiada</div>
            <CardTitle className="mt-2">Enrolamiento paso a paso</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              {GUIDED_STEPS.map((step, index) => {
                const done = index < capturedFrames.length;
                const active = index === stepIndex && !isBusy && phase !== "done";
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

            <div className="webcam-frame">
              <video
                ref={videoRef}
                className="h-full w-full scale-x-[-1] object-cover"
                playsInline
                muted
              />
              {status !== "active" && (
                <div className="absolute inset-0 flex items-center justify-center bg-background/80 text-sm text-muted-foreground backdrop-blur-sm">
                  {status === "requesting" ? "Solicitando cámara..." : "Cámara inactiva"}
                </div>
              )}
              {status === "active" && hasConsent && phase !== "done" && !isBusy && (
                <>
                  <div className="pointer-events-none absolute inset-4 rounded-lg border border-primary/30" />
                  <div className="pointer-events-none absolute inset-x-0 top-3 flex justify-center px-4">
                    <div className="max-w-sm rounded-xl border border-primary/30 bg-background/90 px-4 py-3 text-center backdrop-blur-sm">
                      <p className="font-mono text-[10px] uppercase tracking-[0.08em] text-primary">
                        {currentStep?.title ?? "Completado"}
                      </p>
                      <p className="mt-1 text-sm text-foreground">
                        {currentStep?.hint ?? "Procesando..."}
                      </p>
                    </div>
                  </div>
                  {phase === "countdown" && (
                    <div className="absolute inset-0 flex items-center justify-center bg-background/50 backdrop-blur-[1px]">
                      <span className="grid h-20 w-20 place-items-center rounded-full border-2 border-primary bg-background/90 font-mono text-3xl text-primary">
                        {countdown || "·"}
                      </span>
                    </div>
                  )}
                </>
              )}
              {isBusy && (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-background/80 backdrop-blur-sm">
                  <div className="mb-2 h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                  <p className="font-mono text-[11px] uppercase tracking-[0.08em] text-primary">
                    Validando vivacidad...
                  </p>
                </div>
              )}
              {phase === "done" && (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-success/20 backdrop-blur-sm">
                  <p className="font-mono text-sm uppercase tracking-[0.08em] text-success">
                    Enrolamiento completado
                  </p>
                </div>
              )}
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}
            {stepError && <p className="text-sm text-destructive">{stepError}</p>}

            <div className="flex flex-wrap gap-2">
              <Button onClick={resetFlow} variant="outline" type="button" disabled={isBusy}>
                Reiniciar proceso
              </Button>
              <Button
                onClick={() => void captureCurrentStep()}
                disabled={
                  !hasConsent ||
                  isBusy ||
                  phase === "done" ||
                  status !== "active" ||
                  captureLockRef.current
                }
                type="button"
              >
                {phase === "countdown" ? "Capturar ahora" : "Capturar paso"}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="section-tag">Vista previa</div>
            <CardTitle className="mt-2">Frames capturados</CardTitle>
          </CardHeader>
          <CardContent>
            {previewUrls.length > 0 ? (
              <div className="grid grid-cols-3 gap-2">
                {previewUrls.map((url, index) => (
                  <div key={url} className="space-y-1">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={url}
                      alt={`Paso ${index + 1}`}
                      className="aspect-[3/4] w-full rounded-lg border border-border object-cover"
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
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
