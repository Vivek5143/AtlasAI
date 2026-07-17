import { Sparkles } from "lucide-react";
import type { ReactElement } from "react";
import { Link } from "react-router-dom";

export function Logo(): ReactElement {
  return (
    <Link
      to="/"
      className="flex items-center gap-3 rounded-lg px-1 py-1 text-slate-950 transition-colors hover:text-blue-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:text-white dark:hover:text-blue-400"
    >
      <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-950 text-white shadow-sm dark:bg-white dark:text-slate-950">
        <Sparkles className="h-5 w-5" />
      </span>
      <span className="flex flex-col">
        <span className="text-sm font-semibold tracking-tight">AtlasAI</span>
        <span className="text-xs text-slate-500 dark:text-slate-400">
          InsightForge AI
        </span>
      </span>
    </Link>
  );
}
