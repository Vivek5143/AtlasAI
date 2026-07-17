import { AlertTriangle, RefreshCcw } from "lucide-react";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactElement,
} from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { ChatHeader } from "@/components/chat/ChatHeader";
import { ChatInput } from "@/components/chat/ChatInput";
import { ChatMessage } from "@/components/chat/ChatMessage";
import { TypingIndicator } from "@/components/chat/TypingIndicator";
import { useChat } from "@/hooks/useChat";

type AskLocationState = {
  initialQuestion?: string;
} | null;

function EmptyState(): ReactElement {
  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 items-center justify-center px-4 py-10">
      <div className="w-full rounded-[2rem] border border-slate-800 bg-slate-900/70 p-8 text-center shadow-[0_30px_120px_-50px_rgba(8,145,178,0.5)] sm:p-10">
        <div className="mx-auto inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-500/15 text-cyan-200 ring-1 ring-cyan-500/20">
          <RefreshCcw className="h-6 w-6" aria-hidden="true" />
        </div>
        <h2 className="mt-5 text-2xl font-semibold tracking-tight text-white">
          Start a conversation with AtlasAI
        </h2>
        <p className="mx-auto mt-3 max-w-2xl text-sm leading-7 text-slate-400 sm:text-base">
          Ask about a company, compare vendors, inspect news coverage, or explore
          problem mappings from your AtlasAI knowledge base.
        </p>
      </div>
    </div>
  );
}

function ErrorCard({
  error,
  onRetry,
}: {
  error: string;
  onRetry: () => Promise<void>;
}): ReactElement {
  const handleRetry = useCallback((): void => {
    void onRetry();
  }, [onRetry]);

  return (
    <div className="mx-auto mb-4 w-full max-w-4xl rounded-3xl border border-red-500/30 bg-red-500/10 px-5 py-4 text-red-100 shadow-[0_30px_80px_-50px_rgba(239,68,68,0.7)]">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 rounded-xl bg-red-500/15 p-2 text-red-200">
            <AlertTriangle className="h-4 w-4" aria-hidden="true" />
          </div>
          <div>
            <p className="text-sm font-semibold text-red-50">AtlasAI hit an error</p>
            <p className="mt-1 text-sm leading-6 text-red-100/85">{error}</p>
          </div>
        </div>

        <button
          type="button"
          onClick={handleRetry}
          className="inline-flex items-center justify-center gap-2 rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-2.5 text-sm font-medium text-red-50 transition-colors hover:bg-red-500/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-300"
        >
          <RefreshCcw className="h-4 w-4" aria-hidden="true" />
          Retry
        </button>
      </div>
    </div>
  );
}

export function AskAtlasAI(): ReactElement {
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const autoAskedQuestionRef = useRef<string | null>(null);
  const location = useLocation();
  const navigate = useNavigate();
  const { clearChat, error, loading, messages, retryLastMessage, sendMessage } = useChat();
  const locationState = location.state as AskLocationState;

  const hasMessages = messages.length > 0;

  const scrollToLatestMessage = useCallback((): void => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, []);

  useEffect(() => {
    scrollToLatestMessage();
  }, [loading, messages, scrollToLatestMessage]);

  useEffect(() => {
    const initialQuestion = locationState?.initialQuestion?.trim();
    if (!initialQuestion) {
      return;
    }

    if (loading || messages.length > 0) {
      return;
    }

    if (autoAskedQuestionRef.current === initialQuestion) {
      return;
    }

    autoAskedQuestionRef.current = initialQuestion;
    void sendMessage(initialQuestion);
    navigate(location.pathname, { replace: true, state: null });
  }, [
    loading,
    location.pathname,
    locationState,
    messages.length,
    navigate,
    sendMessage,
  ]);

  const handleInputChange = useCallback((value: string): void => {
    setInputValue(value);
  }, []);

  const handleSendMessage = useCallback(async (): Promise<void> => {
    const trimmedValue = inputValue.trim();
    if (!trimmedValue || loading) {
      return;
    }

    setInputValue("");
    await sendMessage(trimmedValue);
  }, [inputValue, loading, sendMessage]);

  const handleClearChat = useCallback((): void => {
    clearChat();
    setInputValue("");
  }, [clearChat]);

  const handleRetry = useCallback(async (): Promise<void> => {
    await retryLastMessage();
  }, [retryLastMessage]);

  const renderedMessages = useMemo(
    () =>
      messages.map((message) => <ChatMessage key={message.id} message={message} />),
    [messages],
  );

  return (
    <section className="flex h-full min-h-0 flex-col bg-[radial-gradient(circle_at_top,_rgba(6,182,212,0.12),_transparent_32%),linear-gradient(180deg,_rgba(15,23,42,1)_0%,_rgba(2,6,23,1)_100%)]">
      <div className="mx-auto flex h-full min-h-0 w-full max-w-7xl flex-col px-3 py-3 sm:px-4 sm:py-4">
        <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-[2rem] border border-slate-800 bg-slate-950/85 shadow-[0_35px_140px_-60px_rgba(8,145,178,0.45)]">
          <ChatHeader
            canClear={hasMessages}
            messageCount={messages.length}
            onClear={handleClearChat}
          />

          <div className="flex min-h-0 flex-1 flex-col">
            <div className="min-h-0 flex-1 overflow-y-auto px-4 py-6 sm:px-6">
              {hasMessages ? (
                <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
                  {renderedMessages}
                  {loading ? <TypingIndicator /> : null}
                  <div ref={messagesEndRef} />
                </div>
              ) : (
                <EmptyState />
              )}
            </div>

            <div className="px-0 sm:px-0">
              {error ? <ErrorCard error={error} onRetry={handleRetry} /> : null}
              <ChatInput
                value={inputValue}
                onValueChange={handleInputChange}
                onSubmit={() => void handleSendMessage()}
                disabled={false}
                isLoading={loading}
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
