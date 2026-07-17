import {
  Building2,
  LayoutDashboard,
  Newspaper,
  Settings,
  Shapes,
  TriangleAlert,
  X,
} from "lucide-react";
import type { ReactElement } from "react";

import { Logo } from "@/components/logo";
import { NavItem } from "@/components/nav-item";
import { cn } from "@/lib/utils";

type SidebarProps = {
  mobile?: boolean;
  onNavigate?: () => void;
  onClose?: () => void;
};

const primaryNavigation = [
  { label: "Dashboard", to: "/", icon: LayoutDashboard, end: true },
  { label: "Companies", to: "/companies", icon: Building2 },
  { label: "Problems", to: "/problems", icon: TriangleAlert },
  { label: "Sectors", to: "/sectors", icon: Shapes },
  { label: "News", to: "/news", icon: Newspaper },
];

export function Sidebar({
  mobile = false,
  onNavigate,
  onClose,
}: SidebarProps): ReactElement {
  return (
    <aside
      className={cn(
        "flex h-full flex-col rounded-3xl border border-slate-200 bg-white/95 p-4 shadow-sm dark:border-slate-800 dark:bg-slate-950/95",
        mobile ? "w-full max-w-xs" : "w-72",
      )}
      aria-label="Primary navigation"
    >
      <div className="flex items-center justify-between gap-3">
        <Logo />
        {mobile ? (
          <button
            type="button"
            onClick={onClose}
            aria-label="Close navigation menu"
            className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:border-slate-800 dark:text-slate-400 dark:hover:bg-slate-900 dark:hover:text-white"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        ) : null}
      </div>

      <div className="mt-8">
        <p className="px-3 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400 dark:text-slate-500">
          Workspace
        </p>
        <nav className="mt-3 flex flex-col gap-2">
          {primaryNavigation.map((item) => (
            <NavItem
              key={item.to}
              end={item.end}
              icon={item.icon}
              label={item.label}
              onNavigate={onNavigate}
              to={item.to}
            />
          ))}
        </nav>
      </div>

      <div className="mt-auto pt-6">
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-900">
          <button
            type="button"
            onClick={onNavigate}
            aria-label="Settings placeholder"
            className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
          >
            <Settings className="h-4 w-4 shrink-0" aria-hidden="true" />
            <span>Settings</span>
          </button>
        </div>
      </div>
    </aside>
  );
}
