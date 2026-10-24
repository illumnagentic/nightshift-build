import type { ApiClient } from "./client";
import { httpClient } from "./http";
import { mockClient } from "./mock";

export const api: ApiClient = import.meta.env.VITE_API_MODE === "mock" ? mockClient : httpClient;

export { ApiError } from "./client";
export type { ApiClient } from "./client";
export type * from "./types";
