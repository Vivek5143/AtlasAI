import {
  Bot,
  Building2,
  LayoutDashboard,
  Newspaper,
  Shapes,
  TriangleAlert,
  X,
} from "lucide-react";
import type { ReactElement } from "react";
import { Link } from "react-router-dom";

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
  { label: "Ask AtlasAI", to: "/ask", icon: Bot },
];

export function Sidebar({
  mobile = false,
  onNavigate,
  onClose,
}: SidebarProps): ReactElement {
  return (
    <aside
      className={cn(
        "flex h-full flex-col rounded-[2rem] border border-[#d9dfd5] bg-[#f9f6ef]/95 p-4 shadow-[0_28px_60px_-42px_rgba(15,23,42,0.45)] backdrop-blur dark:border-slate-800 dark:bg-slate-950/95",
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
            className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-[#d9dfd5] text-slate-500 transition-colors hover:bg-white hover:text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 dark:border-slate-800 dark:text-slate-400 dark:hover:bg-slate-900 dark:hover:text-white"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        ) : null}
      </div>

      <div className="mt-6 rounded-[1.75rem] border border-[#dde3d8] bg-white/80 p-4 dark:border-slate-800 dark:bg-slate-900/80">
        <p className="text-[0.7rem] font-semibold uppercase tracking-[0.24em] text-[#5d6f67] dark:text-slate-400">
          AtlasAI Workspace
        </p>
        <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
          Track companies, problems, sectors, news, and AI-led research in one calm analysis surface.
        </p>
      </div>

      <div className="mt-7">
        <p className="px-3 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500">
          Navigation
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
        <div className="rounded-[1.75rem] border border-[#d9dfd5] bg-white/85 p-4 dark:border-slate-800 dark:bg-slate-900/90">
          <p className="text-[0.7rem] font-semibold uppercase tracking-[0.22em] text-[#5d6f67] dark:text-slate-400">
            Access
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
            The current build keeps the live AtlasAI routes available while authentication is being wired.
          </p>
          <Link
            to="/login"
            onClick={onNavigate}
            className="mt-4 inline-flex w-full items-center justify-center rounded-2xl border border-[#cfd8d1] bg-[#edf3ec] px-4 py-2.5 text-sm font-medium text-[#214938] transition-colors hover:bg-[#e4eee5] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-200 dark:hover:bg-slate-900"
          >
            Open Login Page
          </Link>
        </div>
      </div>
    </aside>
  );
}
