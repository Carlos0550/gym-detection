"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { AccessLogsTable } from "@/features/access-logs/access-logs-table";
import { useGym } from "@/hooks/use-auth";

export default function AccessLogsPage() {
  const { gymId } = useGym();

  if (!gymId) {
    return <Skeleton className="h-64 w-full" />;
  }

  return <AccessLogsTable gymId={gymId} />;
}
