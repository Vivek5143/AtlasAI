import {
  Bot,
  Building2,
  Compass,
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

import { useAuth } from "@/contexts/auth-context";

type SidebarProps = {
  mobile?: boolean;
  onNavigate?: () => void;
  onClose?: () => void;
};

const allNavigation = [
  { label: "Dashboard", to: "/", icon: LayoutDashboard, end: true },
  { label: "Companies", to: "/companies", icon: Building2 },
  { label: "Discovery", to: "/discovery", icon: Compass, adminOnly: true },
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
  const { user, isAdmin, logout } = useAuth();

  const navigation = allNavigation.filter(
    (item) => !item.adminOnly || isAdmin
  );

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
          {navigation.map((item) => (
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
          {user ? (
            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-[0.2em] text-[#5d6f67] dark:text-slate-400">
                  Account
                </span>
                <span className={cn(
                  "rounded-full px-2 py-0.5 text-[0.65rem] font-bold uppercase tracking-wider",
                  isAdmin
                    ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                    : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                )}>
                  {user.role}
                </span>
              </div>
              <p className="mt-2 text-sm font-medium text-slate-900 dark:text-white truncate">
                {user.username}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
                {user.email}
              </p>
              <button
                type="button"
                onClick={() => {
                  logout();
                  if (onNavigate) onNavigate();
                }}
                className="mt-3 inline-flex w-full items-center justify-center rounded-2xl border border-rose-200 bg-rose-50 px-4 py-2 text-xs font-medium text-rose-700 transition-colors hover:bg-rose-100 dark:border-rose-900/40 dark:bg-rose-950/40 dark:text-rose-300"
              >
                Sign Out
              </button>
            </div>
          ) : (
            <div>
              <p className="text-[0.7rem] font-semibold uppercase tracking-[0.22em] text-[#5d6f67] dark:text-slate-400">
                Access
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                Sign in with an admin account to manage Company Discovery.
              </p>
              <Link
                to="/login"
                onClick={onNavigate}
                className="mt-4 inline-flex w-full items-center justify-center rounded-2xl border border-[#cfd8d1] bg-[#edf3ec] px-4 py-2.5 text-sm font-medium text-[#214938] transition-colors hover:bg-[#e4eee5] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-200 dark:hover:bg-slate-900"
              >
                Sign In / Login
              </Link>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
