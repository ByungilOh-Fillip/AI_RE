const rawApiBaseUrl = import.meta.env.VITE_API_BASE_URL as string | undefined;

export const apiBaseUrl = (rawApiBaseUrl ?? "").replace(/\/$/, "");
