import { SendHorizonal } from "lucide-react";
import {
  useCallback,
  useEffect,
  useRef,
  type ChangeEvent,
  type KeyboardEvent,
  type ReactElement,
} from "react";

type ChatInputProps = {
  disabled?: boolean;
  isLoading: boolean;
  onSubmit: () => void;
  onValueChange: (value: string) => void;
  value: string;
};

function resizeTextArea(textarea: HTMLTextAreaElement): void {
  textarea.style.height = "0px";
  textarea.style.height = `${Math.min(textarea.scrollHeight, 220)}px`;
}

export function ChatInput({
  disabled = false,
  isLoading,
  onSubmit,
  onValueChange,
  value,
}: ChatInputProps): ReactElement {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    if (!textareaRef.current) {
      return;
    }

    resizeTextArea(textareaRef.current);
  }, [value]);

  const handleChange = useCallback(
    (event: ChangeEvent<HTMLTextAreaElement>): void => {
      onValueChange(event.target.value);
    },
    [onValueChange],
  );

  const handleKeyDown = useCallback(
    (event: KeyboardEvent<HTMLTextAreaElement>): void => {
      if (event.key !== "Enter" || event.shiftKey) {
        return;
      }

      event.preventDefault();
      onSubmit();
    },
    [onSubmit],
  );

  const handleSubmitClick = useCallback((): void => {
    onSubmit();
  }, [onSubmit]);

  const isSubmitDisabled = disabled || isLoading || value.trim().length === 0;

  return (
    <div className="sticky bottom-0 border-t border-slate-800/80 bg-slate-950/95 px-4 pb-4 pt-4 backdrop-blur sm:px-6">
      <div className="mx-auto flex w-full max-w-4xl items-end gap-3 rounded-[2rem] border border-slate-800 bg-slate-900/90 p-3 shadow-[0_25px_120px_-45px_rgba(8,145,178,0.55)]">
        <label className="flex min-w-0 flex-1 items-end">
          <span className="sr-only">Ask AtlasAI a question</span>
          <textarea
            ref={textareaRef}
            rows={1}
            value={value}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder="Ask AtlasAI about companies, sectors, news, or problems..."
            className="max-h-[220px] min-h-[52px] w-full resize-none overflow-y-auto bg-transparent px-3 py-3 text-sm leading-6 text-slate-100 outline-none placeholder:text-slate-500 sm:text-base"
          />
        </label>

        <button
          type="button"
          onClick={handleSubmitClick}
          disabled={isSubmitDisabled}
          className="inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-cyan-500 text-slate-950 transition-all duration-200 hover:bg-cyan-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300 disabled:cursor-not-allowed disabled:bg-slate-800 disabled:text-slate-500"
          aria-label="Send message"
        >
          <SendHorizonal className="h-5 w-5" aria-hidden="true" />
        </button>
      </div>

      <p className="mx-auto mt-3 max-w-4xl px-2 text-xs text-slate-500">
        Press <span className="font-medium text-slate-400">Enter</span> to send and{" "}
        <span className="font-medium text-slate-400">Shift + Enter</span> for a
        new line.
      </p>
    </div>
  );
}
