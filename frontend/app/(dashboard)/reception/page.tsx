"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { ReceptionVerify } from "@/features/reception/reception-verify";
import { useGym } from "@/hooks/use-auth";

export default function ReceptionPage() {
  const { gymId } = useGym();

  if (!gymId) {
    return <Skeleton className="h-64 w-full" />;
  }

  return <ReceptionVerify gymId={gymId} />;
}
