export type ConfidenceLevel = "Alta" | "Media" | "Baja";

export function getConfidenceLevel(confidence: number): ConfidenceLevel {
  if (confidence >= 0.75) return "Alta";
  if (confidence >= 0.5) return "Media";
  return "Baja";
}

export function formatConfidencePercent(confidence: number): string {
  return `${(confidence * 100).toFixed(1)}%`;
}

export function formatConfidence(confidence: number): {
  level: ConfidenceLevel;
  percent: string;
} {
  return {
    level: getConfidenceLevel(confidence),
    percent: formatConfidencePercent(confidence),
  };
}
