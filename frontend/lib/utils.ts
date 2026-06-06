import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 Combina clases de Tailwind de forma segura, resolviendo conflictos.
 Usado por todos los componentes shadcn/ui.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
