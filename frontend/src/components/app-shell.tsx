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
    <div className="relative min-h-screen overflow-hidden bg-[#f3efe6] text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-72 bg-[radial-gradient(circle_at_top_left,_rgba(60,110,88,0.18),_transparent_44%),radial-gradient(circle_at_top_right,_rgba(166,179,173,0.2),_transparent_38%)] dark:bg-[radial-gradient(circle_at_top_left,_rgba(52,211,153,0.12),_transparent_44%),radial-gradient(circle_at_top_right,_rgba(15,23,42,0.55),_transparent_38%)]" />
      <div className="pointer-events-none absolute right-[-5rem] top-[6rem] h-56 w-56 rounded-full bg-emerald-950/8 blur-3xl dark:bg-emerald-400/10" />

      <div className="relative flex min-h-screen">
        <div className="hidden p-5 lg:block">
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
          className="fixed inset-0 z-50 bg-slate-950/45 px-4 py-4 backdrop-blur-sm lg:hidden"
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
