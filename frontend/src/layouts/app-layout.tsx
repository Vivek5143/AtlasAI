import { Menu } from "lucide-react";
import type { PropsWithChildren, ReactElement } from "react";
import { Link, NavLink } from "react-router-dom";

const navigationItems = [
  { label: "Dashboard", to: "/" },
  { label: "Companies", to: "/companies" },
  { label: "Problems", to: "/problems" },
  { label: "Sectors", to: "/sectors" },
  { label: "News", to: "/news" },
];

export function AppLayout({ children }: PropsWithChildren): ReactElement {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <Link className="text-lg font-semibold text-slate-900" to="/">
            AtlasAI
          </Link>
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <Menu className="h-4 w-4" />
            <span>Frontend Setup</span>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[220px_minmax(0,1fr)] lg:px-8">
        <aside className="rounded-lg border border-slate-200 bg-white p-4">
          <p className="mb-3 text-sm font-medium text-slate-900">Navigation</p>
          <nav className="flex flex-col gap-2">
            {navigationItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  [
                    "rounded-md px-3 py-2 text-sm transition-colors",
                    isActive
                      ? "bg-slate-900 text-white"
                      : "text-slate-700 hover:bg-slate-100",
                  ].join(" ")
                }
                end={item.to === "/"}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </aside>

        <main className="rounded-lg border border-slate-200 bg-white p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
