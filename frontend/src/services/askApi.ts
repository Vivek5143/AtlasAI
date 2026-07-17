import { AxiosError } from "axios";

import { apiClient } from "@/api/client";
import type { AskRequest, AskResponse } from "@/types/chat";

export class AskApiError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "AskApiError";
    this.status = status;
  }
}

function getErrorMessage(error: AxiosError<{ detail?: string }>): string {
  const apiDetail = error.response?.data?.detail;
  if (apiDetail) {
    return apiDetail;
  }

  if (error.code === "ECONNABORTED") {
    return "AtlasAI took too long to respond. Please try again.";
  }

  if (error.message) {
    return error.message;
  }

  return "AtlasAI could not process your request right now.";
}

export async function askAtlasAI(payload: AskRequest): Promise<AskResponse> {
  try {
    const response = await apiClient.post<AskResponse>("/ask", payload);
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new AskApiError(getErrorMessage(error), error.response?.status);
    }

    throw new AskApiError("AtlasAI could not process your request right now.");
  }
}
