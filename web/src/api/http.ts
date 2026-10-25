import { ApiError, type ApiClient } from "./client";

const BASE = "/api";

async function toApiError(res: Response): Promise<ApiError> {
  try {
    const body = await res.json();
    const { code, message } = body.error;
    if (typeof code === "string" && typeof message === "string") {
      return new ApiError(res.status, code, message);
    }
  } catch {
    // Not the contract's error shape, for example a proxy 502 with no backend.
  }
  return new ApiError(
    res.status,
    "http_error",
    `Request failed with status ${res.status}.`,
  );
}

async function request<T>(
  method: string,
  path: string,
  opts: { userId?: string; body?: unknown } = {},
): Promise<T> {
  const headers: Record<string, string> = {};
  if (opts.userId !== undefined) headers["X-User-Id"] = opts.userId;
  if (opts.body !== undefined) headers["Content-Type"] = "application/json";
  const res = await fetch(BASE + path, {
    method,
    headers,
    body: opts.body === undefined ? undefined : JSON.stringify(opts.body),
  });
  if (!res.ok) throw await toApiError(res);
  return (await res.json()) as T;
}

const id = encodeURIComponent;

export const httpClient: ApiClient = {
  listUsers: () => request("GET", "/users"),
  createUser: (req) => request("POST", "/users", { body: req }),
  getPrefs: (userId) => request("GET", "/prefs", { userId }),
  putPrefs: (userId, req) => request("PUT", "/prefs", { userId, body: req }),
  getDeck: (userId, n) =>
    request("GET", n === undefined ? "/deck" : `/deck?n=${n}`, { userId }),
  getListing: (userId, listingId) =>
    request("GET", `/listings/${id(listingId)}`, { userId }),
  swipe: (userId, decisionId, req) =>
    request("POST", `/decisions/${id(decisionId)}/swipe`, {
      userId,
      body: req,
    }),
  putFeedback: (userId, decisionId, req) =>
    request("PUT", `/decisions/${id(decisionId)}/feedback`, {
      userId,
      body: req,
    }),
  correctFlag: (userId, flagId, req) =>
    request("POST", `/flags/${id(flagId)}/correction`, { userId, body: req }),
  getFavourites: (userId) => request("GET", "/favourites", { userId }),
  removeFavourite: (userId, listingId, req) =>
    request("DELETE", `/favourites/${id(listingId)}`, { userId, body: req }),
  getProfile: (userId) => request("GET", "/profile", { userId }),
  getStats: () => request("GET", "/stats"),
};
