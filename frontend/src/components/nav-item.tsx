import type { LucideIcon } from "lucide-react";
import type { ReactElement } from "react";
import { NavLink } from "react-router-dom";

import { cn } from "@/lib/utils";

type NavItemProps = {
  icon: LucideIcon;
  label: string;
  to: string;
  end?: boolean;
  onNavigate?: () => void;
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
          "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500",
          isActive
            ? "bg-slate-950 text-white shadow-sm dark:bg-white dark:text-slate-950"
            : "text-slate-600 hover:bg-slate-100 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white",
        )
      }
    >
      <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
      <span>{label}</span>
    </NavLink>
  );
}
