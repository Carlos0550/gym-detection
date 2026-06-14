let audioContext: AudioContext | null = null;

function getAudioContext(): AudioContext | null {
  if (typeof window === "undefined") return null;
  if (!audioContext) {
    try {
      audioContext = new AudioContext();
    } catch {
      return null;
    }
  }
  return audioContext;
}

function playTone(
  startFreq: number,
  endFreq: number,
  durationSec: number,
  volume = 0.08,
): void {
  const ctx = getAudioContext();
  if (!ctx) return;

  void ctx.resume().then(() => {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.connect(gain);
    gain.connect(ctx.destination);

    const now = ctx.currentTime;
    osc.frequency.setValueAtTime(startFreq, now);
    osc.frequency.linearRampToValueAtTime(endFreq, now + durationSec * 0.6);
    gain.gain.setValueAtTime(volume, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + durationSec);

    osc.start(now);
    osc.stop(now + durationSec);
  });
}

/** Tono ascendente suave para acceso permitido. */
export function playAccessGrantedSound(): void {
  playTone(440, 660, 0.18);
}

/** Tono bajo para acceso denegado. */
export function playAccessDeniedSound(): void {
  playTone(330, 220, 0.22, 0.07);
}
