import { ThemeProvider } from "@/components/apx/theme-provider";
import { QueryClient } from "@tanstack/react-query";
import { createRootRouteWithContext, Outlet } from "@tanstack/react-router";
import { Toaster } from "sonner";
import { AppShell } from "@/components/shell/app-shell";

export const Route = createRootRouteWithContext<{
  queryClient: QueryClient;
}>()({
  component: () => (
    <ThemeProvider defaultTheme="dark" storageKey="apx-ui-theme">
      <AppShell>
        <Outlet />
      </AppShell>
      <Toaster richColors theme="dark" />
    </ThemeProvider>
  ),
});
