import { Bot } from "lucide-react";
import type { ReactElement } from "react";

function TypingDot({ delayClassName }: { delayClassName?: string }): ReactElement {
  return (
    <span
      className={`h-2.5 w-2.5 rounded-full bg-cyan-300/90 animate-pulse ${delayClassName ?? ""}`}
      aria-hidden="true"
    />
  );
}

export function TypingIndicator(): ReactElement {
  return (
    <div className="flex items-start gap-3">
      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-cyan-500/15 text-cyan-200 ring-1 ring-cyan-500/20">
        <Bot className="h-5 w-5" aria-hidden="true" />
      </div>

      <div className="max-w-2xl rounded-[1.75rem] rounded-tl-md border border-slate-800 bg-slate-900/85 px-5 py-4 shadow-[0_20px_50px_-35px_rgba(8,145,178,0.5)]">
        <p className="text-sm text-slate-300">AtlasAI is thinking...</p>
        <div className="mt-3 flex items-center gap-2">
          <TypingDot />
          <TypingDot />
          <TypingDot />
        </div>
      </div>
    </div>
  );
}
