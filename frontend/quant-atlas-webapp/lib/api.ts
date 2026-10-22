import axios from "axios";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  timeout: 30_000,
  headers: {
    "Content-Type": "application/json",
  },
});

export function getApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const payload = error.response?.data as { error?: string } | undefined;
    if (payload?.error) {
      return payload.error;
    }
    if (error.code === "ECONNABORTED") {
      return "The request timed out.";
    }
    if (!error.response) {
      return "Could not reach the QuantAtlas API.";
    }
    return `Request failed with status ${error.response.status}.`;
  }
  return "Something went wrong.";
}
