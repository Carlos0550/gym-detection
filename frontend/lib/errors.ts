type ErrorContext = "enroll" | "reception" | "general";

function stripTechnicalPrefixes(detail: string): string {
  return detail
    .replace(/^Vivacidad no verificada:\s*/i, "")
    .replace(/^ConflictError:\s*/i, "")
    .replace(/^LivenessFailedError:\s*/i, "")
    .trim();
}

export function humanizeError(
  detail: string,
  context: ErrorContext = "general",
): string {
  const raw = detail.trim();
  if (!raw) {
    return "Ocurrió un error inesperado. Intentá de nuevo.";
  }

  const lower = raw.toLowerCase();

  if (
    /frame\s+\d+:\s*no corresponde/i.test(raw) ||
    /frame\s+\d+:\s*no parece ser la misma persona/i.test(raw) ||
    /sim\s*mín\s*=\s*[\d.]+/i.test(raw) ||
    /no parecen ser de la misma persona/i.test(raw) ||
    (/sim\s*=\s*[\d.]+/i.test(raw) && lower.includes("misma persona"))
  ) {
    return "Las fotos no parecen ser de la misma persona. Repetí la captura sin cambiar de persona.";
  }

  if (
    lower.includes("variación de orientación") ||
    lower.includes("movimiento insuficiente") ||
    lower.includes("foto estática") ||
    lower.includes("no se detectó movimiento")
  ) {
    return "No detectamos movimiento suficiente entre las poses. Girá más la cabeza en cada paso e intentá de nuevo.";
  }

  if (lower.includes("vivacidad no verificada")) {
    return stripTechnicalPrefixes(raw);
  }

  if (lower.includes("no se detectaron landmarks faciales")) {
    return "No pudimos detectar bien tu rostro. Mejorá la luz y encuadrá la cara dentro del marco.";
  }

  if (
    lower.includes("se requieren al menos 3 frames") ||
    lower.includes("3 frames guiados") ||
    lower.includes("centro, izquierda, derecha")
  ) {
    return "Necesitamos 3 fotos (centro, izquierda y derecha). Completá los tres pasos.";
  }

  if (lower.includes("se requieren al menos 2 frames")) {
    return "Necesitamos al menos 2 fotos para verificar identidad. Volvé a intentar.";
  }

  if (lower.includes("sin embeddings en el gimnasio")) {
    return "Todavía no hay rostros registrados en este gimnasio. Registrá rostros antes de verificar acceso.";
  }

  if (
    lower.includes("det_score") ||
    lower.includes("calidad insuficiente") ||
    lower.includes("cara demasiado chica")
  ) {
    return "La imagen no tiene calidad suficiente. Acercate a la cámara, mejorá la luz y volvé a intentar.";
  }

  if (lower.includes("rostro no reconocido")) {
    return "No reconocemos este rostro. Verificá que la persona tenga el rostro registrado o intentá de nuevo.";
  }

  if (
    lower.includes("membresía no vigente") ||
    (lower.includes("membership") && lower.includes("inactive")) ||
    lower.includes("membresía inactiva")
  ) {
    return "La membresía no está vigente. Revisá el estado del miembro antes de permitir el acceso.";
  }

  if (
    lower.includes("pose incorrecta") ||
    lower.includes("centrá tu rostro") ||
    lower.includes("girá la cabeza") ||
    lower.includes("paso izquierda") ||
    lower.includes("paso derecha") ||
    lower.includes("orientación del rostro")
  ) {
    if (context === "enroll") {
      return stripTechnicalPrefixes(raw);
    }
    return "La pose no coincide con lo pedido. Seguí las instrucciones en pantalla.";
  }

  if (lower.includes("no se detectó rostro")) {
    return "No detectamos un rostro. Encuadrá la cara dentro del marco e intentá de nuevo.";
  }

  if (lower.includes("múltiples rostros") || lower.includes("multiples rostros")) {
    return "Hay más de un rostro en la imagen. Solo debe aparecer una persona.";
  }

  if (lower.includes("consentimiento biométrico")) {
    return "Falta el consentimiento biométrico. Registralo en la lista de miembros antes de continuar.";
  }

  if (
    lower.includes("email ya está registrado en este gimnasio") ||
    lower.includes("documento ya está registrado en este gimnasio")
  ) {
    return stripTechnicalPrefixes(raw);
  }

  if (lower.includes("sesión expirada")) {
    return "Tu sesión expiró. Volvé a iniciar sesión.";
  }

  return stripTechnicalPrefixes(raw);
}
