import { LoginForm } from "@/features/auth/login-form";
import { Brand } from "@/components/layout/brand";
import { Lock } from "lucide-react";

const benefits = [
  "Recepción en vivo con escaneo continuo",
  "Registro facial guiado paso a paso",
  "Gestión de miembros y membresías",
  "Historial de ingresos de cada acceso",
];

type Props = {
  searchParams: Promise<{ session?: string }>;
};

export default async function LoginPage({ searchParams }: Props) {
  const params = await searchParams;
  const sessionExpired = params.session === "expired";

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 border-b border-border bg-background/70 backdrop-blur-[14px]">
        <div className="verifica-wrap flex h-16 items-center justify-between">
          <Brand href="/login" />
          <p className="hidden text-[13px] text-muted-foreground sm:block">
            Acceso al panel de administración
          </p>
        </div>
      </header>

      <section className="py-12 md:py-16">
        <div className="verifica-wrap">
          <div className="mb-10">
            <nav className="breadcrumb" aria-label="Breadcrumb">
              <span>Verifica</span>
              <span className="sep">/</span>
              <span>Acceso</span>
            </nav>
            <h1 className="page-h1">
              Ingresá a tu <span className="text-primary">panel.</span>
            </h1>
            <p className="page-sub">
              Usá tu cuenta de dueño del gimnasio o encargado para gestionar miembros, recepción e
              historial de ingresos.
            </p>
          </div>

          <div className="grid items-start gap-10 lg:grid-cols-[1.55fr_1fr] lg:gap-12">
            <div className="form-card mt-0">
              <div className="mb-6 border-b border-border pb-6">
                <div className="section-tag">Acceso · Panel</div>
                <h2 className="mt-2.5 text-[19px] font-semibold tracking-[-0.015em]">
                  Credenciales
                </h2>
                <p className="mt-1.5 text-[13px] text-muted-foreground">
                  Tu email es tu usuario. La sesión se mantiene activa en este dispositivo.
                </p>
              </div>
              <LoginForm sessionExpired={sessionExpired} />
            </div>

            <aside className="space-y-4 lg:sticky lg:top-24">
              <div className="rounded-xl border border-border bg-card p-7">
                <div className="section-tag">Panel Verifica</div>
                <h3 className="mt-2.5 text-lg font-semibold tracking-[-0.015em]">
                  Todas las funciones incluidas.
                </h3>
                <p className="mt-1.5 text-[12.5px] leading-relaxed text-muted-foreground">
                  Recepción, registro facial, miembros e historial en un solo lugar.
                </p>
                <ul className="mt-5 space-y-2.5">
                  {benefits.map((item) => (
                    <li key={item} className="flex items-start gap-2.5 text-[13px]">
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
                      <span className="text-muted-foreground">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="flex items-start gap-3.5 rounded-xl border border-border bg-card p-5">
                <div className="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-primary/30 bg-primary/10 text-primary">
                  <Lock className="h-[18px] w-[18px]" strokeWidth={1.6} />
                </div>
                <div>
                  <h4 className="text-[13px] font-semibold">Tus datos están cifrados</h4>
                  <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                    Conexión segura · Almacenamiento cifrado. Datos faciales cifrados.
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
          <p className="font-mono text-[10px] uppercase tracking-[0.08em]">Privada · /login</p>
        </div>
      </footer>
    </div>
  );
}
