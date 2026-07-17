import type { PropsWithChildren, ReactElement } from "react";
import { useEffect, useState } from "react";

import { Navbar } from "@/components/navbar";
import { Sidebar } from "@/components/sidebar";
import { useTheme } from "@/hooks/use-theme";

export function AppShell({ children }: PropsWithChildren): ReactElement {
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();

  useEffect(() => {
    if (!isMobileSidebarOpen) {
      return undefined;
    }

    const handleEscape = (event: KeyboardEvent): void => {
      if (event.key === "Escape") {
        setIsMobileSidebarOpen(false);
      }
    };

    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [isMobileSidebarOpen]);

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <div className="flex min-h-screen">
        <div className="hidden p-4 lg:block">
          <Sidebar />
        </div>

        <div className="flex min-h-screen min-w-0 flex-1 flex-col">
          <Navbar
            onOpenSidebar={() => setIsMobileSidebarOpen(true)}
            onToggleTheme={toggleTheme}
            theme={theme}
          />

          <main className="min-h-0 flex-1 overflow-y-auto">{children}</main>
        </div>
      </div>

      {isMobileSidebarOpen ? (
        <div
          className="fixed inset-0 z-50 bg-slate-950/50 px-4 py-4 backdrop-blur-sm lg:hidden"
          role="dialog"
          aria-modal="true"
          aria-label="Mobile navigation"
        >
          <div className="max-w-xs">
            <Sidebar
              mobile
              onClose={() => setIsMobileSidebarOpen(false)}
              onNavigate={() => setIsMobileSidebarOpen(false)}
            />
          </div>
        </div>
      ) : null}
    </div>
  );
}
