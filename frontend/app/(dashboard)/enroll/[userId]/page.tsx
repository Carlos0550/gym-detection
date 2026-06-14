"use client";

import { use } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { EnrollCapture } from "@/features/enroll/enroll-capture";
import { useGym } from "@/hooks/use-auth";

type Props = {
  params: Promise<{ userId: string }>;
};

export default function EnrollPage({ params }: Props) {
  const { userId } = use(params);
  const { gymId } = useGym();

  if (!gymId) {
    return <Skeleton className="h-64 w-full" />;
  }

  return <EnrollCapture gymId={gymId} userId={userId} />;
}
