import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ApiError } from "./client";
import { httpClient } from "./http";

const fetchMock = vi.fn();

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status });
}

function lastCall(): [string, RequestInit] {
  return fetchMock.mock.calls[0] as [string, RequestInit];
}

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

it("sends X-User-Id on a user-scoped call", async () => {
  fetchMock.mockResolvedValue(json({ version: 0, factors: [], history: [] }));
  await httpClient.getProfile("u_01");
  const [url, init] = lastCall();
  expect(url).toBe("/api/profile");
  expect((init.headers as Record<string, string>)["X-User-Id"]).toBe("u_01");
});

it("omits X-User-Id on GET /users, POST /users and GET /stats", async () => {
  fetchMock.mockImplementation(async () => json({}));
  await httpClient.listUsers();
  await httpClient.createUser({ username: "alex" });
  await httpClient.getStats();
  expect(fetchMock).toHaveBeenCalledTimes(3);
  for (const [, init] of fetchMock.mock.calls as [string, RequestInit][]) {
    expect(init.headers).not.toHaveProperty("X-User-Id");
  }
});

it("sends a JSON body with a content type on POST /users", async () => {
  fetchMock.mockResolvedValue(json({ user_id: "u_01", username: "alex" }, 201));
  const user = await httpClient.createUser({ username: "alex" });
  const [url, init] = lastCall();
  expect(user).toEqual({ user_id: "u_01", username: "alex" });
  expect(url).toBe("/api/users");
  expect(init.method).toBe("POST");
  expect((init.headers as Record<string, string>)["Content-Type"]).toBe(
    "application/json",
  );
  expect(init.body).toBe(JSON.stringify({ username: "alex" }));
});

it("turns an error body into an ApiError", async () => {
  fetchMock.mockResolvedValue(
    json(
      { error: { code: "username_taken", message: "That username is taken." } },
      409,
    ),
  );
  const err = await httpClient
    .createUser({ username: "alex" })
    .catch((e: unknown) => e);
  expect(err).toBeInstanceOf(ApiError);
  expect(err).toMatchObject({
    status: 409,
    code: "username_taken",
    message: "That username is taken.",
  });
});

it("falls back to http_error when the error body is not JSON", async () => {
  fetchMock.mockResolvedValue(new Response("Bad Gateway", { status: 502 }));
  const err = await httpClient.listUsers().catch((e: unknown) => e);
  expect(err).toBeInstanceOf(ApiError);
  expect(err).toMatchObject({
    status: 502,
    code: "http_error",
    message: "Request failed with status 502.",
  });
});

it("falls back to http_error when the JSON is not the error shape", async () => {
  fetchMock.mockResolvedValue(json({ detail: "nope" }, 500));
  const err = await httpClient.listUsers().catch((e: unknown) => e);
  expect(err).toMatchObject({ status: 500, code: "http_error" });
});

it("sends a JSON body with the reason on DELETE /favourites", async () => {
  fetchMock.mockResolvedValue(json({ listing_id: "rm-1", removed: true }));
  await httpClient.removeFavourite("u_01", "rm-1", { reason: "Too far." });
  const [url, init] = lastCall();
  expect(url).toBe("/api/favourites/rm-1");
  expect(init.method).toBe("DELETE");
  const headers = init.headers as Record<string, string>;
  expect(headers["Content-Type"]).toBe("application/json");
  expect(headers["X-User-Id"]).toBe("u_01");
  expect(init.body).toBe(JSON.stringify({ reason: "Too far." }));
});

it("passes n as a query parameter on GET /deck", async () => {
  fetchMock.mockResolvedValue(json({ cards: [], empty_reason: "exhausted" }));
  await httpClient.getDeck("u_01", 5);
  expect(lastCall()[0]).toBe("/api/deck?n=5");
});

it("omits n on GET /deck when not given", async () => {
  fetchMock.mockResolvedValue(json({ cards: [], empty_reason: "exhausted" }));
  await httpClient.getDeck("u_01");
  expect(lastCall()[0]).toBe("/api/deck");
});

it("URL-encodes path ids", async () => {
  fetchMock.mockResolvedValue(json({}));
  await httpClient.getListing("u_01", "a/b c");
  expect(lastCall()[0]).toBe("/api/listings/a%2Fb%20c");
});

it("sends skipped in the PUT feedback body", async () => {
  fetchMock.mockResolvedValue(
    json({
      decision_id: "d_000001",
      chips: [],
      free_text: null,
      skipped: true,
      profile_version: 2,
    }),
  );
  const res = await httpClient.putFeedback("u_01", "d_000001", {
    chips: [],
    free_text: null,
    skipped: true,
  });
  const [url, init] = lastCall();
  expect(url).toBe("/api/decisions/d_000001/feedback");
  expect(init.method).toBe("PUT");
  expect(init.body).toBe(
    JSON.stringify({ chips: [], free_text: null, skipped: true }),
  );
  expect(res.skipped).toBe(true);
});
