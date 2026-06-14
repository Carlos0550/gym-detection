"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ClipboardList,
  LogOut,
  ScanFace,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/use-auth";
import { Brand } from "./brand";
import { GymSelector } from "./gym-selector";

const navItems = [
  { href: "/members", label: "Miembros", icon: Users, tag: "Panel" },
  { href: "/reception", label: "Recepción", icon: ScanFace, tag: "En vivo" },
  { href: "/access-logs", label: "Registros", icon: ClipboardList, tag: "Auditoría" },
];

export function DashboardSidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="flex h-screen w-64 shrink-0 flex-col border-r border-border bg-card">
      <div className="px-5 py-5">
        <Brand href="/members" />
      </div>

      <div className="px-5 pb-4">
        <p className="mb-2 font-mono text-[10px] uppercase tracking-[0.1em] text-muted-2">
          Sede activa
        </p>
        <GymSelector />
      </div>

      <Separator className="bg-border" />

      <nav className="flex-1 space-y-1 p-3">
        <p className="px-3 pb-2 font-mono text-[10px] uppercase tracking-[0.1em] text-muted-2">
          Módulos
        </p>
        {navItems.map(({ href, label, icon: Icon, tag }) => {
          const active = pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] font-medium transition-colors",
                active
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-surface-2 hover:text-foreground",
              )}
            >
              <Icon className={cn("h-4 w-4", active && "text-primary")} />
              <span className="flex-1">{label}</span>
              {active && (
                <span className="font-mono text-[9px] uppercase tracking-[0.08em] text-primary/80">
                  {tag}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-border p-4">
        <div className="mb-3 rounded-lg border border-border bg-surface-2 px-3 py-2.5">
          <p className="truncate text-sm font-medium">{user?.full_name}</p>
          <p className="truncate font-mono text-[10px] uppercase tracking-[0.06em] text-muted-2">
            {user?.email}
          </p>
        </div>
        <Button variant="outline" className="w-full justify-start gap-2" onClick={logout}>
          <LogOut className="h-4 w-4" />
          Cerrar sesión
        </Button>
      </div>
    </aside>
  );
}

export function MobileNav() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur-xl md:hidden">
      <div className="flex items-center justify-between px-4 py-3">
        <Brand href="/members" size="sm" />
      </div>
      <nav className="flex gap-1 overflow-x-auto px-2 pb-2">
        {navItems.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex shrink-0 items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium",
                active
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground",
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          );
        })}
      </nav>
    </header>
  );
}
