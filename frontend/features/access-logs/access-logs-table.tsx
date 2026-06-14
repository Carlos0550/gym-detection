"use client";

import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatConfidence } from "@/lib/confidence";
import { humanizeError } from "@/lib/errors";
import { listAccessLogs } from "@/lib/api/access";

type Props = {
  gymId: string;
};

const resultLabels: Record<string, string> = {
  granted: "Permitido",
  denied: "Denegado",
  unknown: "Sin coincidencia",
  low_confidence: "Coincidencia baja",
};

function ResultBadge({ result }: { result: string }) {
  const label = resultLabels[result] ?? result;
  if (result === "granted") {
    return <Badge variant="success">{label}</Badge>;
  }
  if (result === "unknown" || result === "low_confidence") {
    return <Badge variant="warning">{label}</Badge>;
  }
  return <Badge variant="destructive">{label}</Badge>;
}

function ConfidenceCell({ confidence }: { confidence: number }) {
  const { level, percent } = formatConfidence(confidence);

  return (
    <span>
      <span className="font-medium">{level}</span>
      <span className="ml-1 font-mono text-xs text-muted-2">({percent})</span>
    </span>
  );
}

function formatDate(iso: string) {
  return new Intl.DateTimeFormat("es-AR", {
    dateStyle: "short",
    timeStyle: "medium",
  }).format(new Date(iso));
}

function UserCell({
  fullName,
  document,
}: {
  fullName: string | null;
  document: string | null;
}) {
  if (!fullName) {
    return <span className="text-muted-2">—</span>;
  }

  return (
    <div>
      <p className="font-medium">{fullName}</p>
      {document && (
        <p className="font-mono text-[10px] uppercase tracking-[0.06em] text-muted-2">
          {document}
        </p>
      )}
    </div>
  );
}

function formatDetail(detail: string | null, membershipStatus: string | null): string {
  if (detail) {
    return humanizeError(detail, "reception");
  }
  if (membershipStatus) {
    return membershipStatus;
  }
  return "—";
}

export function AccessLogsTable({ gymId }: Props) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["access-logs", gymId],
    queryFn: () => listAccessLogs(gymId, { limit: 100 }),
    enabled: !!gymId,
    refetchInterval: 30_000,
  });

  if (error) {
    return (
      <p className="text-sm text-destructive">
        No se pudieron cargar los registros. El endpoint puede no estar disponible aún.
      </p>
    );
  }

  const logs = data?.items ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        breadcrumbs={[
          { label: "Verifica", href: "/members" },
          { label: "Panel" },
          { label: "Registros" },
        ]}
        title={
          <>
            Historial de <span className="text-primary">ingresos.</span>
          </>
        }
        subtitle="Registro de verificaciones faciales en recepción."
        meta={
          <span className="head-pill">
            <span className="h-1.5 w-1.5 rounded-full bg-success" />
            {logs.length} eventos
          </span>
        }
      />

      <div className="data-table-wrap">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Fecha y hora</TableHead>
              <TableHead>Usuario</TableHead>
              <TableHead>Resultado</TableHead>
              <TableHead>Coincidencia</TableHead>
              <TableHead>Detalle</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 5 }).map((__, j) => (
                    <TableCell key={j}>
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : logs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="py-12 text-center text-muted-foreground">
                  Sin registros de acceso.
                </TableCell>
              </TableRow>
            ) : (
              logs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {formatDate(log.created_at)}
                  </TableCell>
                  <TableCell>
                    <UserCell
                      fullName={log.user_full_name}
                      document={log.user_document}
                    />
                  </TableCell>
                  <TableCell>
                    <ResultBadge result={log.result} />
                  </TableCell>
                  <TableCell>
                    {log.confidence != null ? (
                      <ConfidenceCell confidence={log.confidence} />
                    ) : (
                      "—"
                    )}
                  </TableCell>
                  <TableCell className="max-w-xs truncate text-muted-foreground">
                    {formatDetail(log.detail, log.membership_status)}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
