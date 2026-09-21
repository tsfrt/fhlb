import { Suspense, type ReactNode } from "react";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import { ErrorBoundary } from "react-error-boundary";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";

export function QueryBoundary({
  children,
  fallback,
}: {
  children: ReactNode;
  fallback?: ReactNode;
}) {
  return (
    <QueryErrorResetBoundary>
      {({ reset }) => (
        <ErrorBoundary
          onReset={reset}
          fallbackRender={({ resetErrorBoundary, error }) => (
            <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-destructive/30 bg-destructive/5 p-6 text-center">
              <AlertTriangle className="size-6 text-destructive" />
              <p className="text-sm text-muted-foreground">
                Couldn't load this view.
                <br />
                <span className="text-xs opacity-70">{String((error as Error)?.message ?? "")}</span>
              </p>
              <Button variant="outline" size="sm" onClick={resetErrorBoundary}>
                <RefreshCw className="size-3.5" /> Retry
              </Button>
            </div>
          )}
        >
          <Suspense fallback={fallback ?? <Skeleton className="h-40 w-full rounded-lg" />}>
            {children}
          </Suspense>
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  );
}
