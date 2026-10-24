import type { User } from "./api";

const KEY = "session.user";

export function getSession(): User | null {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw === null) return null;
    const v: unknown = JSON.parse(raw);
    if (
      typeof v === "object" &&
      v !== null &&
      "user_id" in v &&
      "username" in v &&
      typeof v.user_id === "string" &&
      typeof v.username === "string"
    ) {
      return { user_id: v.user_id, username: v.username };
    }
  } catch {
    // Storage unavailable or value unreadable: behave as signed out.
  }
  return null;
}

export function setSession(user: User): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(user));
  } catch {
    // Storage unavailable: the session lasts until reload.
  }
}

export function clearSession(): void {
  try {
    localStorage.removeItem(KEY);
  } catch {
    // Storage unavailable: nothing to clear.
  }
}
