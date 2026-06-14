"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Skeleton } from "@/components/ui/skeleton";
import { getToken } from "@/lib/api-client";
import { useAuth } from "@/hooks/use-auth";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, isLoading, isAuthenticated } = useAuth();

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  if (!getToken() || isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center p-8">
        <div className="w-full max-w-md space-y-4">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </div>
      </div>
    );
  }

  if (!user) return null;

  const canManage = user.memberships.some((m) =>
    ["owner", "manager"].includes(m.role),
  );

  if (!canManage && !user.is_superadmin) {
    return (
      <div className="flex min-h-screen items-center justify-center p-8">
        <p className="text-center text-muted-foreground">
          Tu cuenta no tiene permisos de gestión en ningún gimnasio.
        </p>
      </div>
    );
  }

  return <>{children}</>;
}
