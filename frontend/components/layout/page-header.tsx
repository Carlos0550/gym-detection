import Link from "next/link";
import { cn } from "@/lib/utils";

type BreadcrumbItem = {
  label: string;
  href?: string;
};

type PageHeaderProps = {
  breadcrumbs?: BreadcrumbItem[];
  title: React.ReactNode;
  subtitle?: string;
  meta?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
};

export function PageHeader({
  breadcrumbs,
  title,
  subtitle,
  meta,
  actions,
  className,
}: PageHeaderProps) {
  return (
    <div className={cn("mb-8", className)}>
      <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div className="min-w-0 flex-1">
          {breadcrumbs && breadcrumbs.length > 0 && (
            <nav className="breadcrumb" aria-label="Breadcrumb">
              {breadcrumbs.map((item, index) => (
                <span key={item.label} className="flex items-center gap-2.5">
                  {index > 0 && <span className="sep">/</span>}
                  {item.href ? (
                    <Link href={item.href}>{item.label}</Link>
                  ) : (
                    <span>{item.label}</span>
                  )}
                </span>
              ))}
            </nav>
          )}
          <h1 className="page-h1">{title}</h1>
          {subtitle && <p className="page-sub">{subtitle}</p>}
        </div>
        {(meta || actions) && (
          <div className="flex shrink-0 flex-col items-start gap-3 lg:items-end">
            {meta}
            {actions}
          </div>
        )}
      </div>
    </div>
  );
}
