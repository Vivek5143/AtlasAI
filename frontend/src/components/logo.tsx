import { Orbit } from "lucide-react";
import type { ReactElement } from "react";
import { Link } from "react-router-dom";

export function Logo(): ReactElement {
  return (
    <Link
      to="/"
      className="group flex items-center gap-3 rounded-2xl px-1 py-1 text-slate-950 transition-colors hover:text-emerald-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 dark:text-white dark:hover:text-emerald-200"
    >
      <span className="relative flex h-11 w-11 items-center justify-center rounded-2xl border border-emerald-950/10 bg-[#1d4d3b] text-[#f5f1e8] shadow-[0_16px_36px_-24px_rgba(22,61,47,0.75)] transition-transform duration-300 group-hover:scale-[1.02] dark:border-emerald-400/20 dark:bg-emerald-200 dark:text-emerald-950">
        <Orbit className="h-5 w-5" aria-hidden="true" />
        <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-emerald-200 dark:bg-emerald-700" />
      </span>
      <span className="flex flex-col">
        <span className="font-editorial text-lg leading-none tracking-[-0.04em]">
          AtlasAI
        </span>
        <span className="mt-1 text-[0.68rem] uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">
          Market Intelligence
        </span>
      </span>
    </Link>
  );
}
