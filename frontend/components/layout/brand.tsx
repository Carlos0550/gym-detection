import Link from "next/link";
import { cn } from "@/lib/utils";

type BrandProps = {
  href?: string;
  className?: string;
  size?: "sm" | "md";
};

export function Brand({ href = "/members", className, size = "md" }: BrandProps) {
  const markSize = size === "sm" ? "h-6 w-6 text-xs" : "h-7 w-7 text-sm";
  const nameSize = size === "sm" ? "text-[13px]" : "text-sm";

  const content = (
    <>
      <div
        className={cn(
          "grid place-items-center rounded-[7px] bg-primary font-bold tracking-[-0.02em] text-primary-foreground",
          markSize,
        )}
      >
        V
      </div>
      <span className={cn("font-semibold tracking-[-0.01em]", nameSize)}>Verifica</span>
    </>
  );

  if (href) {
    return (
      <Link href={href} className={cn("flex items-center gap-2.5", className)}>
        {content}
      </Link>
    );
  }

  return <div className={cn("flex items-center gap-2.5", className)}>{content}</div>;
}
