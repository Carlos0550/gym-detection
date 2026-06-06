import Link from "next/link";

export default function HomePage() {
  return (
    <main className="container flex min-h-screen flex-col items-center justify-center gap-6 py-12">
      <h1 className="text-4xl font-bold tracking-tight">Gym Detection</h1>
      <p className="max-w-md text-center text-muted-foreground">
        Sistema de reconocimiento facial para gimnasios. Etapa 0 — setup base.
      </p>
      <div className="flex gap-3">
        <Link
          href="http://localhost:8000/docs"
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
          target="_blank"
        >
          API Docs
        </Link>
        <Link
          href="http://localhost:8000/health"
          className="rounded-md border border-input bg-background px-4 py-2 text-sm font-medium hover:bg-accent"
          target="_blank"
        >
          Healthcheck
        </Link>
      </div>
    </main>
  );
}
