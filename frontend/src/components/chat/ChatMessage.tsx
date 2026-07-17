import { Bot, Copy, User } from "lucide-react";
import ReactMarkdown from "react-markdown";
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactElement,
} from "react";

import { cn } from "@/lib/utils";
import type { ChatMessage as ChatMessageType } from "@/types/chat";

import { MetadataAccordion } from "./MetadataAccordion";
import { SourceList } from "./SourceList";

type ChatMessageProps = {
  message: ChatMessageType;
};

function MarkdownAnswer({ content }: { content: string }): ReactElement {
  return (
    <ReactMarkdown
      components={{
        a: ({ children, href }) => (
          <a
            href={href}
            target="_blank"
            rel="noreferrer"
            className="text-cyan-300 underline decoration-cyan-500/50 underline-offset-4 transition-colors hover:text-cyan-200"
          >
            {children}
          </a>
        ),
        code: ({ children }) => (
          <code className="rounded-md bg-slate-950/80 px-1.5 py-0.5 text-[0.95em] text-cyan-200">
            {children}
          </code>
        ),
        h1: ({ children }) => (
          <h1 className="mt-1 text-xl font-semibold text-white first:mt-0">{children}</h1>
        ),
        h2: ({ children }) => (
          <h2 className="mt-5 text-lg font-semibold text-white first:mt-0">{children}</h2>
        ),
        h3: ({ children }) => (
          <h3 className="mt-4 text-base font-semibold text-white first:mt-0">{children}</h3>
        ),
        li: ({ children }) => <li className="ml-5 list-disc text-slate-200">{children}</li>,
        ol: ({ children }) => <ol className="space-y-2">{children}</ol>,
        p: ({ children }) => <p className="leading-7 text-slate-200">{children}</p>,
        pre: ({ children }) => (
          <pre className="overflow-x-auto rounded-2xl bg-slate-950/90 p-4 text-sm text-slate-100">
            {children}
          </pre>
        ),
        strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
        ul: ({ children }) => <ul className="space-y-2">{children}</ul>,
      }}
    >
      {content}
    </ReactMarkdown>
  );
}

function formatTimestamp(createdAt: string): string {
  return new Intl.DateTimeFormat(undefined, {
    hour: "numeric",
    minute: "2-digit",
    month: "short",
    day: "numeric",
  }).format(new Date(createdAt));
}

export function ChatMessage({ message }: ChatMessageProps): ReactElement {
  const [isVisible, setIsVisible] = useState(false);
  const [hasCopied, setHasCopied] = useState(false);

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => setIsVisible(true));
    return () => window.cancelAnimationFrame(frame);
  }, []);

  useEffect(() => {
    if (!hasCopied) {
      return undefined;
    }

    const timeoutId = window.setTimeout(() => setHasCopied(false), 1800);
    return () => window.clearTimeout(timeoutId);
  }, [hasCopied]);

  const isAssistant = message.role === "assistant";
  const Icon = isAssistant ? Bot : User;

  const alignmentClassName = isAssistant ? "justify-start" : "justify-end";
  const bubbleClassName = isAssistant
    ? "rounded-[1.75rem] rounded-tl-md border border-slate-800 bg-slate-900/90 text-slate-100 shadow-[0_20px_50px_-35px_rgba(8,145,178,0.55)]"
    : "rounded-[1.75rem] rounded-tr-md bg-gradient-to-br from-cyan-500 to-sky-500 text-slate-950 shadow-[0_20px_50px_-35px_rgba(6,182,212,0.7)]";
  const iconClassName = isAssistant
    ? "bg-cyan-500/15 text-cyan-200 ring-1 ring-cyan-500/20"
    : "bg-cyan-400 text-slate-950";

  const timestamp = useMemo(() => formatTimestamp(message.createdAt), [message.createdAt]);

  const handleCopy = useCallback(async (): Promise<void> => {
    try {
      await navigator.clipboard.writeText(message.content);
      setHasCopied(true);
    } catch {
      setHasCopied(false);
    }
  }, [message.content]);

  return (
    <article
      className={cn(
        "flex gap-3 transition-all duration-300",
        alignmentClassName,
        isVisible ? "translate-y-0 opacity-100" : "translate-y-3 opacity-0",
      )}
    >
      {isAssistant ? (
        <div
          className={cn(
            "flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl",
            iconClassName,
          )}
        >
          <Icon className="h-5 w-5" aria-hidden="true" />
        </div>
      ) : null}

      <div
        className={cn(
          "w-full max-w-3xl overflow-hidden px-5 py-4",
          bubbleClassName,
          isAssistant ? "" : "order-first",
        )}
      >
        <div className="mb-3 flex items-center justify-between gap-3">
          <div className="min-w-0">
            <p className={cn("text-sm font-semibold", isAssistant ? "text-white" : "text-slate-950")}>
              {isAssistant ? "AtlasAI" : "You"}
            </p>
            <p
              className={cn(
                "text-xs",
                isAssistant ? "text-slate-400" : "text-slate-900/70",
              )}
            >
              {timestamp}
            </p>
          </div>

          {isAssistant ? (
            <button
              type="button"
              onClick={handleCopy}
              className="inline-flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2 text-xs font-medium text-slate-300 transition-colors hover:border-slate-700 hover:bg-slate-950 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400"
            >
              <Copy className="h-3.5 w-3.5" aria-hidden="true" />
              {hasCopied ? "Copied" : "Copy"}
            </button>
          ) : null}
        </div>

        {isAssistant ? (
          <div className="space-y-4">
            <div className="space-y-3">
              <MarkdownAnswer content={message.content} />
            </div>
            <SourceList sources={message.sources} />
            <MetadataAccordion metadata={message.metadata} />
          </div>
        ) : (
          <p className="whitespace-pre-wrap text-sm leading-7 text-slate-950 sm:text-base">
            {message.content}
          </p>
        )}
      </div>

      {!isAssistant ? (
        <div
          className={cn(
            "flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl",
            iconClassName,
          )}
        >
          <Icon className="h-5 w-5" aria-hidden="true" />
        </div>
      ) : null}
    </article>
  );
}
