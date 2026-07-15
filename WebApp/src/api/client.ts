export interface HealthResponse {
  service: "aire-backend";
  status: "ok";
  schema_version: number;
  ai_mode: "mock" | "local";
}

export interface OfflineChatRequest {
  schema_version: 1;
  request_id: string;
  save_slot_id: string;
  companion_id: string;
  session_id: string;
  interaction_mode: "Offline";
  message_id: string;
  user_message: string;
  time_context: {
    source: "RealWorld";
    observed_at: string;
    timezone: string;
  };
  recent_event_ids: string[];
}

export interface ChatResponse {
  schema_version: 1;
  request_id: string;
  response_id: string;
  display_text: string;
  interaction_mode: "InGame" | "Offline";
  command_candidates: unknown[];
  memory_candidates: unknown[];
  ai_metadata: {
    provider: string;
    model_version: string;
    prompt_version: string;
  };
}

interface ErrorEnvelope {
  schema_version: 1;
  request_id: string;
  error: {
    code: string;
    message: string;
    retryable: boolean;
  };
}

export class ChatApiError extends Error {
  constructor(
    public readonly code: string,
    public readonly retryable: boolean,
  ) {
    super(code);
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isHealthResponse(value: unknown): value is HealthResponse {
  if (!isRecord(value)) {
    return false;
  }

  return (
    value.service === "aire-backend" &&
    value.status === "ok" &&
    typeof value.schema_version === "number" &&
    (value.ai_mode === "mock" || value.ai_mode === "local")
  );
}

function isChatResponse(value: unknown): value is ChatResponse {
  if (!isRecord(value) || !isRecord(value.ai_metadata)) {
    return false;
  }
  return (
    value.schema_version === 1 &&
    typeof value.request_id === "string" &&
    typeof value.response_id === "string" &&
    typeof value.display_text === "string" &&
    (value.interaction_mode === "InGame" || value.interaction_mode === "Offline") &&
    Array.isArray(value.command_candidates) &&
    Array.isArray(value.memory_candidates) &&
    typeof value.ai_metadata.provider === "string" &&
    typeof value.ai_metadata.model_version === "string" &&
    typeof value.ai_metadata.prompt_version === "string"
  );
}

function isErrorEnvelope(value: unknown): value is ErrorEnvelope {
  return (
    isRecord(value) &&
    value.schema_version === 1 &&
    typeof value.request_id === "string" &&
    isRecord(value.error) &&
    typeof value.error.code === "string" &&
    typeof value.error.message === "string" &&
    typeof value.error.retryable === "boolean"
  );
}

export async function fetchHealth(apiBaseUrl: string): Promise<HealthResponse> {
  const response = await fetch(`${apiBaseUrl}/health`, {
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error(`Backend health request failed: ${response.status}`);
  }

  const body: unknown = await response.json();
  if (!isHealthResponse(body)) {
    throw new Error("Backend health response does not match the contract.");
  }

  return body;
}

export async function createOfflineChat(
  apiBaseUrl: string,
  deviceToken: string,
  request: OfflineChatRequest,
): Promise<ChatResponse> {
  const response = await fetch(`${apiBaseUrl}/api/v1/chat`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${deviceToken}`,
      "Content-Type": "application/json",
      "X-Request-ID": request.request_id,
    },
    body: JSON.stringify(request),
  });
  const body: unknown = await response.json();
  if (!response.ok) {
    if (isErrorEnvelope(body)) {
      throw new ChatApiError(body.error.code, body.error.retryable);
    }
    throw new ChatApiError("InvalidErrorResponse", false);
  }
  if (!isChatResponse(body) || body.request_id !== request.request_id) {
    throw new ChatApiError("InvalidChatResponse", false);
  }
  return body;
}
