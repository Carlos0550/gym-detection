"use client";

import { AuthGuard } from "@/components/layout/auth-guard";
import { DashboardSidebar, MobileNav } from "@/components/layout/dashboard-sidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <div className="flex min-h-screen bg-background">
        <div className="hidden md:block">
          <DashboardSidebar />
        </div>
        <div className="flex min-h-screen flex-1 flex-col">
          <MobileNav />
          <main className="flex-1 overflow-auto py-6 md:py-10">
            <div className="verifica-wrap">{children}</div>
          </main>
        </div>
      </div>
    </AuthGuard>
  );
}
