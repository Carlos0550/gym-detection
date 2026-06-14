"use client";

import { useMutation, useQueries, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
    <Badge variant="secondary">No</Badge>
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

  const { data: members = [], isLoading, error } = useQuery({
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
    },
    onError: (err: ApiError) => toast.error(err.detail),
  });

  if (error) {
    return (
      <p className="text-sm text-destructive">
        No se pudieron cargar los miembros. El endpoint puede no estar disponible aún.
      </p>
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
        subtitle="Clientes, consentimiento biométrico y enrolamiento facial."
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
              <TableHead>Enrolado</TableHead>
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
                        {!member.biometric_consent_at && (
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={consentMutation.isPending}
                            onClick={() => consentMutation.mutate(member.id)}
                          >
                            Consentir
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setEditingMember(member)}
                        >
                          Editar
                        </Button>
                        <Button size="sm" asChild>
                          <Link href={`/enroll/${member.id}`}>Enrolar</Link>
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>

      <EditMemberDialog
        gymId={gymId}
        member={editingMember}
        open={!!editingMember}
        onOpenChange={(open) => !open && setEditingMember(null)}
      />
    </div>
  );
}
