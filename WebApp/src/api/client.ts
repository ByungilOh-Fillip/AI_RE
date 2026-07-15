export interface HealthResponse {
  service: "aire-backend";
  status: "ok";
  schema_version: number;
  ai_mode: "mock" | "local";
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
