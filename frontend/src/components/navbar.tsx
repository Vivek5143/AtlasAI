import { Bell, Menu, Search } from "lucide-react";
import type { ReactElement } from "react";

import type { Theme } from "@/hooks/use-theme";
import { ThemeToggle } from "@/components/theme-toggle";

type NavbarProps = {
  theme: Theme;
  onOpenSidebar: () => void;
  onToggleTheme: () => void;
};

export function Navbar({
  theme,
  onOpenSidebar,
  onToggleTheme,
}: NavbarProps): ReactElement {
  return (
    <header className="sticky top-0 z-20 flex items-center justify-between gap-4 border-b border-slate-200 bg-white/85 px-4 py-4 backdrop-blur sm:px-6 dark:border-slate-800 dark:bg-slate-950/80">
      <div className="flex min-w-0 items-center gap-3">
        <button
          type="button"
          aria-label="Open navigation menu"
          onClick={onOpenSidebar}
          className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 lg:hidden dark:border-slate-800 dark:text-slate-300 dark:hover:bg-slate-900 dark:hover:text-white"
        >
          <Menu className="h-4 w-4" aria-hidden="true" />
        </button>

        <div className="min-w-0">
          <p className="text-sm font-semibold text-slate-950 dark:text-white">
            AtlasAI
          </p>
          <p className="truncate text-sm text-slate-500 dark:text-slate-400">
            Workspace / Placeholder shell
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        <label className="relative hidden md:block">
          <span className="sr-only">Search the application shell</span>
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            placeholder="Search"
            className="h-10 w-56 rounded-xl border border-slate-200 bg-white pl-9 pr-3 text-sm text-slate-700 shadow-sm outline-none transition-colors placeholder:text-slate-400 focus:border-blue-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:placeholder:text-slate-500"
          />
        </label>

        <ThemeToggle onToggle={onToggleTheme} theme={theme} />

        <button
          type="button"
          aria-label="Notifications"
          className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-600 shadow-sm transition-colors hover:bg-slate-100 hover:text-slate-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
        >
          <Bell className="h-4 w-4" aria-hidden="true" />
        </button>

        <button
          type="button"
          aria-label="Profile menu"
          className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-slate-950 text-sm font-semibold text-white shadow-sm transition-transform hover:scale-[1.02] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:bg-white dark:text-slate-950"
        >
          AI
        </button>
      </div>
    </header>
  );
}
