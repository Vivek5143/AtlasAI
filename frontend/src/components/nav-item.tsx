import type { LucideIcon } from "lucide-react";
import type { ReactElement } from "react";
import { NavLink } from "react-router-dom";

import { cn } from "@/lib/utils";

type NavItemProps = {
  end?: boolean;
  icon: LucideIcon;
  label: string;
  onNavigate?: () => void;
  to: string;
};

export function NavItem({
  icon: Icon,
  label,
  to,
  end = false,
  onNavigate,
}: NavItemProps): ReactElement {
  return (
    <NavLink
      to={to}
      end={end}
      onClick={onNavigate}
      className={({ isActive }) =>
        cn(
          "group relative flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600",
          isActive
            ? "bg-[#e5efe6] text-[#214938] shadow-[0_18px_40px_-28px_rgba(28,71,54,0.55)] dark:bg-emerald-500/15 dark:text-emerald-100"
            : "text-slate-600 hover:bg-white/90 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-900 dark:hover:text-white",
        )
      }
    >
      {({ isActive }) => (
        <>
          <span
            className={cn(
              "absolute left-1 top-1/2 h-8 w-0.5 -translate-y-1/2 rounded-full transition-colors",
              isActive ? "bg-[#2f6b51] dark:bg-emerald-300" : "bg-transparent",
            )}
            aria-hidden="true"
          />
          <span
            className={cn(
              "flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border transition-colors",
              isActive
                ? "border-emerald-900/10 bg-white/80 text-[#214938] dark:border-emerald-400/15 dark:bg-emerald-400/10 dark:text-emerald-100"
                : "border-transparent bg-transparent text-slate-500 group-hover:border-slate-200 group-hover:bg-slate-50 group-hover:text-slate-900 dark:text-slate-400 dark:group-hover:border-slate-800 dark:group-hover:bg-slate-950 dark:group-hover:text-white",
            )}
          >
            <Icon className="h-4 w-4" aria-hidden="true" />
          </span>
          <span>{label}</span>
        </>
      )}
    </NavLink>
  );
}
