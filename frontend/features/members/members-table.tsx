"use client";

import { useMutation, useQueries, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { listFaceEmbeddings } from "@/lib/api/face";
import { listGymClients, updateGymUser } from "@/lib/api/users";
import type { ActiveMembershipSummary, ApiError, GymClient } from "@/lib/types/api";
import { humanizeError } from "@/lib/errors";
import { CreateMemberDialog } from "./create-member-dialog";
import { EditMemberDialog } from "./edit-member-dialog";

type Props = {
  gymId: string;
};

function ConsentBadge({ consentAt }: { consentAt: string | null }) {
  if (consentAt) {
    return <Badge variant="success">Otorgado</Badge>;
  }
  return <Badge variant="warning">Pendiente</Badge>;
}

function EnrolledBadge({ enrolled }: { enrolled: boolean | undefined }) {
  if (enrolled === undefined) return <Skeleton className="h-5 w-16" />;
  return enrolled ? (
    <Badge variant="success">Sí</Badge>
  ) : (
    <Badge variant="secondary">Pendiente</Badge>
  );
}

const membershipStatusLabels: Record<string, string> = {
  active: "Activa",
  expired: "Vencida",
  cancelled: "Cancelada",
  suspended: "Suspendida",
};

function formatMembershipDate(iso: string) {
  return new Intl.DateTimeFormat("es-AR", { dateStyle: "short" }).format(new Date(iso));
}

function MembershipCell({ membership }: { membership: ActiveMembershipSummary | null }) {
  if (!membership) {
    return <Badge variant="outline">Sin membresía</Badge>;
  }

  const label = membershipStatusLabels[membership.status] ?? membership.status;
  const variant =
    membership.status === "active"
      ? "success"
      : membership.status === "suspended"
        ? "destructive"
        : "secondary";

  const dateRange = membership.end_date
    ? `${formatMembershipDate(membership.start_date)} – ${formatMembershipDate(membership.end_date)}`
    : `Desde ${formatMembershipDate(membership.start_date)}`;

  return (
    <div className="space-y-1">
      <Badge variant={variant}>{label}</Badge>
      <p className="font-mono text-[10px] uppercase tracking-[0.06em] text-muted-2">
        {dateRange}
      </p>
    </div>
  );
}

export function MembersTable({ gymId }: Props) {
  const queryClient = useQueryClient();
  const [editingMember, setEditingMember] = useState<GymClient | null>(null);
  const [consentTarget, setConsentTarget] = useState<GymClient | null>(null);

  const { data: members = [], isLoading, error, refetch, isRefetching } = useQuery({
    queryKey: ["members", gymId],
    queryFn: () => listGymClients(gymId),
    enabled: !!gymId,
  });

  const enrollmentQueries = useQueries({
    queries: members.map((member) => ({
      queryKey: ["face", gymId, member.id],
      queryFn: () => listFaceEmbeddings(gymId, member.id),
      enabled: !!gymId,
      staleTime: 60_000,
    })),
  });

  const consentMutation = useMutation({
    mutationFn: (userId: string) =>
      updateGymUser(gymId, userId, { grant_biometric_consent: true }),
    onSuccess: () => {
      toast.success("Consentimiento biométrico registrado");
      queryClient.invalidateQueries({ queryKey: ["members", gymId] });
      setConsentTarget(null);
    },
    onError: (err: ApiError) => toast.error(err.detail),
  });

  if (error) {
    const rawDetail =
      typeof error === "object" &&
      error !== null &&
      "detail" in error &&
      typeof (error as { detail: unknown }).detail === "string"
        ? (error as { detail: string }).detail
        : error instanceof Error
          ? error.message
          : "No pudimos cargar los miembros. Revisá tu conexión e intentá de nuevo.";
    const detail = humanizeError(rawDetail);
    return (
      <div className="space-y-4 rounded-lg border border-destructive/30 bg-destructive/5 p-6">
        <p className="text-sm text-destructive">{detail}</p>
        <Button
          variant="outline"
          size="sm"
          onClick={() => void refetch()}
          disabled={isRefetching}
        >
          {isRefetching ? "Reintentando..." : "Reintentar"}
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        breadcrumbs={[
          { label: "Verifica", href: "/members" },
          { label: "Panel" },
          { label: "Miembros" },
        ]}
        title={
          <>
            Gestión de <span className="text-primary">miembros.</span>
          </>
        }
        subtitle="Clientes, consentimiento biométrico y registro facial."
        meta={
          <span className="head-pill">
            <span className="h-1.5 w-1.5 rounded-full bg-success" />
            {members.length} registrados
          </span>
        }
        actions={<CreateMemberDialog gymId={gymId} />}
      />

      <div className="data-table-wrap">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nombre</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>DNI</TableHead>
              <TableHead>Membresía</TableHead>
              <TableHead>Consentimiento</TableHead>
              <TableHead>Rostro registrado</TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 4 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 7 }).map((__, j) => (
                    <TableCell key={j}>
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : members.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="py-12 text-center text-muted-foreground">
                  No hay miembros registrados.
                </TableCell>
              </TableRow>
            ) : (
              members.map((member, index) => {
                const enrolled = enrollmentQueries[index]?.data
                  ? enrollmentQueries[index].data!.length > 0
                  : undefined;
                const hasConsent = !!member.biometric_consent_at;

                return (
                  <TableRow key={member.id}>
                    <TableCell className="font-medium">{member.full_name}</TableCell>
                    <TableCell className="text-muted-foreground">{member.email}</TableCell>
                    <TableCell className="font-mono text-xs text-muted-2">
                      {member.document ?? "—"}
                    </TableCell>
                    <TableCell>
                      <MembershipCell membership={member.active_membership} />
                    </TableCell>
                    <TableCell>
                      <ConsentBadge consentAt={member.biometric_consent_at} />
                    </TableCell>
                    <TableCell>
                      <EnrolledBadge enrolled={enrolled} />
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        {!hasConsent && (
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={consentMutation.isPending}
                            onClick={() => setConsentTarget(member)}
                          >
                            Marcar consentimiento
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setEditingMember(member)}
                        >
                          Editar
                        </Button>
                        {hasConsent ? (
                          <Button size="sm" asChild>
                            <Link href={`/enroll/${member.id}`}>Registrar rostro</Link>
                          </Button>
                        ) : (
                          <Button
                            size="sm"
                            disabled
                            title="Primero necesitás el consentimiento del miembro"
                          >
                            Registrar rostro
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>

      <Dialog
        open={!!consentTarget}
        onOpenChange={(open) => !open && setConsentTarget(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirmar consentimiento</DialogTitle>
            <DialogDescription>
              ¿Confirmás la autorización de{" "}
              <strong className="text-foreground">{consentTarget?.full_name}</strong> para
              reconocimiento facial?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConsentTarget(null)}>
              Cancelar
            </Button>
            <Button
              disabled={consentMutation.isPending}
              onClick={() => consentTarget && consentMutation.mutate(consentTarget.id)}
            >
              {consentMutation.isPending ? "Confirmando..." : "Confirmar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <EditMemberDialog
        gymId={gymId}
        member={editingMember}
        open={!!editingMember}
        onOpenChange={(open) => !open && setEditingMember(null)}
      />
    </div>
  );
}
