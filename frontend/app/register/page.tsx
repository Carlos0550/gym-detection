import Link from "next/link";
import { RegisterForm } from "@/features/auth/register-form";
import { Brand } from "@/components/layout/brand";
import { Lock } from "lucide-react";

const benefits = [
  {
    title: "Recepción en vivo",
    description: "Cámara siempre activa. Verificación automática en menos de un segundo.",
  },
  {
    title: "Registro facial",
    description: "Guiado paso a paso, con feedback de luz, encuadre y calidad.",
  },
  {
    title: "Gestión de miembros",
    description: "Miembros ilimitados durante la prueba. Después, también.",
  },
  {
    title: "Membresías y planes",
    description: "Tipos de plan, fechas de inicio, vencimientos y renovaciones.",
  },
  {
    title: "Historial de ingresos",
    description: "Cada intento de acceso, filtrable y exportable.",
  },
  {
    title: "5 usuarios del equipo",
    description: "Recepción, dueño del gimnasio, hasta 3 roles más. Después podés ampliar.",
  },
];

export default function RegisterPage() {
  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 border-b border-border bg-background/70 backdrop-blur-[14px]">
        <div className="verifica-wrap flex h-16 items-center justify-between">
          <Brand href="/register" />
          <div className="flex items-center gap-2 sm:gap-3">
            <Link
              href="/login"
              className="hidden text-[13px] text-muted-foreground transition-colors hover:text-foreground sm:inline"
            >
              ¿Ya tenés cuenta?
            </Link>
            <Link
              href="/login"
              className="inline-flex items-center rounded-lg border border-border bg-surface-2 px-4 py-2.5 text-[13px] font-medium transition-colors hover:border-border-strong hover:bg-surface-3"
            >
              Ingresar
            </Link>
          </div>
        </div>
      </header>

      <section className="py-12 md:py-16">
        <div className="verifica-wrap">
          <div className="mb-10 grid items-end gap-8 lg:grid-cols-[1.4fr_1fr] lg:gap-12">
            <div>
              <nav className="breadcrumb" aria-label="Breadcrumb">
                <Link href="/register">Verifica</Link>
                <span className="sep">/</span>
                <span>Planes</span>
                <span className="sep">/</span>
                <span>Crear cuenta</span>
              </nav>
              <h1 className="page-h1">
                Creá tu cuenta de <span className="text-primary">Verifica.</span>
              </h1>
              <p className="page-sub">
                Empezás con 14 días gratis, con todos los módulos activos. Después, US$ 79 por mes
                por sede — sin contratos, sin sorpresas.
              </p>
            </div>
            <div className="flex flex-col items-start gap-2 lg:items-end">
              <span className="head-pill">
                <span className="h-1.5 w-1.5 rounded-full bg-success" />
                Activación inmediata
              </span>
              <span className="head-pill">2 / 2 pasos</span>
            </div>
          </div>

          <div className="grid items-start gap-10 lg:grid-cols-[1.55fr_1fr] lg:gap-12">
            <RegisterForm />

            <aside className="space-y-4 lg:sticky lg:top-24">
              <div className="rounded-xl border border-border bg-card p-7">
                <p className="text-[12px] font-medium uppercase tracking-[0.06em] text-muted-foreground">
                  Lo que obtenés al registrarte
                </p>
                <h3 className="mt-2 text-lg font-semibold tracking-[-0.015em]">
                  Todas las funciones incluidas, desde el primer día.
                </h3>
                <p className="mt-1.5 text-[12.5px] leading-relaxed text-muted-foreground">
                  Sin letra chica, sin cobrarte de más por módulo.
                </p>
                <ul className="mt-5 space-y-4">
                  {benefits.map((item) => (
                    <li key={item.title} className="flex items-start gap-2.5 text-[13px]">
                      <span className="mt-0.5 grid h-[18px] w-[18px] shrink-0 place-items-center rounded-[5px] bg-success/10 text-success">
                        <svg
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          className="h-[11px] w-[11px]"
                          strokeWidth={2.6}
                        >
                          <path d="M20 6L9 17l-5-5" />
                        </svg>
                      </span>
                      <span className="text-muted-foreground">
                        <strong className="text-foreground">{item.title}</strong>
                        <br />
                        {item.description}
                      </span>
                    </li>
                  ))}
                </ul>
                <div className="mt-6 space-y-2 border-t border-border pt-5 text-[12px] text-muted-foreground">
                  <p className="flex items-center gap-2">
                    <CheckIcon />
                    Activación inmediata al confirmar
                  </p>
                  <p className="flex items-center gap-2">
                    <CheckIcon />
                    Onboarding guiado paso a paso
                  </p>
                  <p className="flex items-center gap-2">
                    <CheckIcon />
                    Soporte por email en horario comercial
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3.5 rounded-xl border border-border bg-card p-5">
                <div className="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-primary/30 bg-primary/10 text-primary">
                  <Lock className="h-[18px] w-[18px]" strokeWidth={1.6} />
                </div>
                <div>
                  <h4 className="text-[13px] font-semibold">Tus datos están cifrados</h4>
                  <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                    Conexión segura · Almacenamiento cifrado. Servidores en la región que elijas al
                    confirmar.
                  </p>
                </div>
              </div>
            </aside>
          </div>
        </div>
      </section>

      <footer className="border-t border-border py-9">
        <div className="verifica-wrap flex flex-col gap-2 text-xs text-muted-2 sm:flex-row sm:items-center sm:justify-between">
          <p>© 2026 Verifica · Tus datos biométricos nunca salen de tu región.</p>
          <p className="font-mono text-[10px] uppercase tracking-[0.08em]">Pública · /register</p>
        </div>
      </footer>
    </div>
  );
}

function CheckIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2.2}
      className="shrink-0 text-success"
    >
      <path d="M20 6L9 17l-5-5" />
    </svg>
  );
}
