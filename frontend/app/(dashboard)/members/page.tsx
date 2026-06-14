"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { MembersTable } from "@/features/members/members-table";
import { useGym } from "@/hooks/use-auth";

export default function MembersPage() {
  const { gymId } = useGym();

  if (!gymId) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  return <MembersTable gymId={gymId} />;
}
