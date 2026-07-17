import { useCallback, useMemo, useState } from "react";

import { AskApiError, askAtlasAI } from "@/services/askApi";
import type {
  AskResponse,
  ChatMessage,
  Metadata,
  Source,
} from "@/types/chat";

type SendMessageOptions = {
  appendUserMessage: boolean;
};

export interface UseChatResult {
  error: string | null;
  loading: boolean;
  messages: ChatMessage[];
  clearChat: () => void;
  retryLastMessage: () => Promise<void>;
  sendMessage: (question: string) => Promise<void>;
}

function createMessageId(): string {
  return crypto.randomUUID();
}

function extractSourceTitle(label: string): string {
  return label
    .replace(/^\[\d+\]\s*/, "")
    .replace(/\s*\([^)]*\)\s*$/, "")
    .trim();
}

function buildSources(sources: string[], metadata: Metadata[]): Source[] {
  if (sources.length > 0) {
    return sources.map((label, index) => {
      const matchingMetadata = metadata[index];
      const title = matchingMetadata?.title?.trim() || extractSourceTitle(label);
      const companyId = matchingMetadata?.company_id?.trim() || undefined;

      return {
        id: `${title}-${index}`,
        label,
        title,
        href: companyId ? `/companies/${companyId}` : undefined,
        entityType: matchingMetadata?.entity_type,
        companyId,
      };
    });
  }

  return metadata.map((item, index) => {
    const title = item.title?.trim() || `Source ${index + 1}`;
    const companyId = item.company_id?.trim() || undefined;

    return {
      id: `${title}-${index}`,
      label: title,
      title,
      href: companyId ? `/companies/${companyId}` : undefined,
      entityType: item.entity_type,
      companyId,
    };
  });
}

function buildAssistantMessage(response: AskResponse): ChatMessage {
  return {
    id: createMessageId(),
    role: "assistant",
    content: response.answer,
    createdAt: new Date().toISOString(),
    sources: buildSources(response.sources, response.metadata),
    metadata: response.metadata,
  };
}

function buildUserMessage(question: string): ChatMessage {
  return {
    id: createMessageId(),
    role: "user",
    content: question,
    createdAt: new Date().toISOString(),
    sources: [],
    metadata: [],
  };
}

export function useChat(): UseChatResult {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastQuestion, setLastQuestion] = useState<string | null>(null);

  const requestAnswer = useCallback(
    async (question: string, options: SendMessageOptions): Promise<void> => {
      const trimmedQuestion = question.trim();
      if (!trimmedQuestion) {
        return;
      }

      setError(null);
      setLastQuestion(trimmedQuestion);
      setLoading(true);

      if (options.appendUserMessage) {
        const userMessage = buildUserMessage(trimmedQuestion);
        setMessages((currentMessages) => [...currentMessages, userMessage]);
      }

      try {
        const response = await askAtlasAI({ question: trimmedQuestion });
        const assistantMessage = buildAssistantMessage(response);
        setMessages((currentMessages) => [...currentMessages, assistantMessage]);
      } catch (errorValue) {
        const message =
          errorValue instanceof AskApiError
            ? errorValue.message
            : "AtlasAI could not process your request right now.";

        setError(message);
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const sendMessage = useCallback(
    async (question: string): Promise<void> => {
      if (loading) {
        return;
      }

      await requestAnswer(question, { appendUserMessage: true });
    },
    [loading, requestAnswer],
  );

  const retryLastMessage = useCallback(async (): Promise<void> => {
    if (!lastQuestion || loading) {
      return;
    }

    await requestAnswer(lastQuestion, { appendUserMessage: false });
  }, [lastQuestion, loading, requestAnswer]);

  const clearChat = useCallback((): void => {
    setMessages([]);
    setError(null);
    setLastQuestion(null);
  }, []);

  return useMemo(
    () => ({
      error,
      loading,
      messages,
      clearChat,
      retryLastMessage,
      sendMessage,
    }),
    [clearChat, error, loading, messages, retryLastMessage, sendMessage],
  );
}
