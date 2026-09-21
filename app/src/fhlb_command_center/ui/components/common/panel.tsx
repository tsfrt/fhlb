import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function Panel({
  title,
  subtitle,
  icon,
  actions,
  className,
  persona,
  children,
}: {
  title?: ReactNode;
  subtitle?: ReactNode;
  icon?: ReactNode;
  actions?: ReactNode;
  className?: string;
  persona?: boolean;
  children: ReactNode;
}) {
  return (
    <section
      className={cn(
        "animate-fade-up rounded-xl p-4 sm:p-5",
        persona ? "glass-persona" : "glass",
        className,
      )}
    >
      {(title || actions) && (
        <header className="mb-3 flex items-start justify-between gap-3">
          <div className="flex items-start gap-2.5">
            {icon && (
              <div className="persona-bg-soft mt-0.5 grid size-8 place-items-center rounded-lg persona-text">
                {icon}
              </div>
            )}
            <div>
              {title && (
                <h3 className="text-sm font-semibold leading-tight tracking-tight">{title}</h3>
              )}
              {subtitle && (
                <p className="mt-0.5 text-xs text-muted-foreground">{subtitle}</p>
              )}
            </div>
          </div>
          {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
        </header>
      )}
      {children}
    </section>
  );
}
