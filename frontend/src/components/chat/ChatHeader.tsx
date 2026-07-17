import { Sparkles, Trash2 } from "lucide-react";
import type { ReactElement } from "react";

type ChatHeaderProps = {
  canClear: boolean;
  messageCount: number;
  onClear: () => void;
};

export function ChatHeader({
  canClear,
  messageCount,
  onClear,
}: ChatHeaderProps): ReactElement {
  return (
    <header className="border-b border-slate-800/80 bg-slate-950/70 px-4 py-5 backdrop-blur sm:px-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0">
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/20 bg-cyan-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-cyan-200">
            <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
            Ask AtlasAI
          </div>
          <h1 className="mt-3 text-2xl font-semibold tracking-tight text-white sm:text-3xl">
            Research companies with your private AI workspace
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400 sm:text-base">
            AtlasAI searches your indexed backend knowledge base and responds with
            cited answers you can trace back to company records.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 px-4 py-3 text-sm text-slate-300 shadow-[0_20px_60px_-35px_rgba(14,165,233,0.4)]">
            <span className="font-medium text-white">{messageCount}</span>{" "}
            {messageCount === 1 ? "message" : "messages"}
          </div>

          <button
            type="button"
            onClick={onClear}
            disabled={!canClear}
            className="inline-flex items-center gap-2 rounded-2xl border border-slate-800 bg-slate-900 px-4 py-3 text-sm font-medium text-slate-300 transition-all duration-200 hover:border-slate-700 hover:bg-slate-800 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Trash2 className="h-4 w-4" aria-hidden="true" />
            Clear chat
          </button>
        </div>
      </div>
    </header>
  );
}
