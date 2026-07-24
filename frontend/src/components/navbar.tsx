import { Menu } from "lucide-react";
import type { ReactElement } from "react";
import { Link, matchPath, useLocation } from "react-router-dom";

import { GlobalSearch } from "@/components/global-search";
import { ThemeToggle } from "@/components/theme-toggle";
import { useAuth } from "@/contexts/auth-context";
import type { Theme } from "@/hooks/use-theme";

type RouteMeta = {
  description: string;
  path: string;
  title: string;
};

const routeMeta: RouteMeta[] = [
  {
    path: "/",
    title: "Dashboard",
    description: "AtlasAI intelligence overview",
  },
  {
    path: "/companies",
    title: "Companies",
    description: "Browse the current company intelligence dataset",
  },
  {
    path: "/companies/:companyId",
    title: "Company Profile",
    description: "Detailed company intelligence and linked records",
  },
  {
    path: "/problems",
    title: "Problems",
    description: "Investigate market problems and mapped categories",
  },
  {
    path: "/discovery",
    title: "Company Discovery",
    description: "Admin discovery portal for evaluating tavily organization candidates",
  },
  {
    path: "/news",
    title: "News",
    description: "Track the latest linked market developments",
  },
  {
    path: "/ask",
    title: "Ask AtlasAI",
    description: "Explore the knowledge base with AI-assisted research",
  },
];

function resolveRouteMeta(pathname: string): RouteMeta {
  const match = routeMeta.find((entry) =>
    matchPath({ path: entry.path, end: entry.path !== "/companies/:companyId" }, pathname),
  );

  return (
    match ?? {
      path: pathname,
      title: "AtlasAI",
      description: "Market intelligence workspace",
    }
  );
}

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
  const location = useLocation();
  const currentRoute = resolveRouteMeta(location.pathname);
  const { user } = useAuth();

  const initials = user
    ? user.username.slice(0, 2).toUpperCase()
    : "AA";

  return (
    <header className="sticky top-0 z-20 border-b border-[#dddccf] bg-[#f3efe6]/88 px-4 py-4 backdrop-blur sm:px-6 dark:border-slate-800 dark:bg-slate-950/80">
      <div className="flex items-center justify-between gap-4">
        <div className="flex min-w-0 items-center gap-3">
          <button
            type="button"
            aria-label="Open navigation menu"
            onClick={onOpenSidebar}
            className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-[#d7ddd1] bg-white/80 text-slate-600 transition-colors hover:bg-white hover:text-slate-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 lg:hidden dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
          >
            <Menu className="h-4 w-4" aria-hidden="true" />
          </button>

          <div className="min-w-0">
            <p className="text-[0.72rem] font-semibold uppercase tracking-[0.24em] text-[#5e7068] dark:text-slate-400">
              AtlasAI
            </p>
            <h1 className="truncate font-editorial text-2xl leading-none tracking-[-0.04em] text-slate-950 dark:text-white">
              {currentRoute.title}
            </h1>
            <p className="mt-1 truncate text-sm text-slate-500 dark:text-slate-400">
              {currentRoute.description}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          <GlobalSearch />

          <ThemeToggle onToggle={onToggleTheme} theme={theme} />

          <Link
            to={user ? "#" : "/login"}
            title={user ? `Signed in as ${user.username} (${user.role})` : "Sign In"}
            aria-label="User account profile"
            className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-[#d7ddd1] bg-[#214938] text-sm font-semibold text-[#f6f2e8] shadow-[0_20px_40px_-28px_rgba(28,71,54,0.7)] transition-transform hover:scale-[1.02] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 dark:border-emerald-300/20 dark:bg-emerald-200 dark:text-emerald-950"
          >
            {initials}
          </Link>
        </div>
      </div>
    </header>
  );
}
