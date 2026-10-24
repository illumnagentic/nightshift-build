import { ApiError } from "../api/client";
import type { Card, DeckResponse, SwipeResponse } from "../api/types";

export const REFETCH_THRESHOLD = 3;

export const BLOCKED_CODES = ["prefs_missing", "commute_pending", "commute_failed"] as const;
export type BlockedCode = (typeof BLOCKED_CODES)[number];

export const GENERIC_ERROR_MESSAGE = "Could not reach the server. Try again.";

export type EmptyReason = NonNullable<DeckResponse["empty_reason"]>;

export type Failure =
  | { kind: "blocked"; code: BlockedCode; message: string }
  | { kind: "error"; message: string };

export type FeedbackOutcome = "compulsory" | "optional" | "none";

export type PendingFeedback = { card: Card; response: SwipeResponse; compulsory: boolean };

// A left swipe on an exploration card teaches nothing: the curator was right.
export function feedbackOutcome(response: SwipeResponse, card: Card): FeedbackOutcome {
  if (response.feedback_required) return "compulsory";
  if (card.source === "exploration" && response.action === "left") return "none";
  return "optional";
}

export type DeckState = {
  // The first card is the one on show.
  queue: Card[];
  // Set once a fetch brought nothing new. Stops further refetching.
  emptyReason: EmptyReason | null;
  failure: Failure | null;
  loading: boolean;
  swiping: boolean;
  pendingFeedback: PendingFeedback | null;
  favourited: boolean;
  // Decisions already swiped, so a fetch that was in flight cannot bring them back.
  swipedIds: string[];
};

export type Phase = "feedback" | "blocked" | "error" | "card" | "empty" | "loading";

export type DeckAction =
  | { type: "reset" }
  | { type: "fetchStart" }
  | { type: "fetchOk"; response: DeckResponse }
  | { type: "fetchFail"; error: unknown }
  | { type: "swipeStart" }
  | { type: "swipeOk"; card: Card; response: SwipeResponse }
  | { type: "swipeFail"; error: unknown }
  | { type: "continue" }
  | { type: "retry" };

export const initialDeckState: DeckState = {
  queue: [],
  emptyReason: null,
  failure: null,
  loading: false,
  swiping: false,
  pendingFeedback: null,
  favourited: false,
  swipedIds: [],
};

export function toFailure(error: unknown): Failure {
  if (error instanceof ApiError) {
    const code = BLOCKED_CODES.find((c) => c === error.code);
    if (code) return { kind: "blocked", code, message: error.message };
    return { kind: "error", message: error.message };
  }
  return { kind: "error", message: GENERIC_ERROR_MESSAGE };
}

export function currentCard(state: DeckState): Card | null {
  return state.queue[0] ?? null;
}

export function phase(state: DeckState): Phase {
  if (state.pendingFeedback) return "feedback";
  if (state.failure?.kind === "blocked") return "blocked";
  if (state.failure) return "error";
  if (state.queue.length > 0) return "card";
  if (state.emptyReason) return "empty";
  return "loading";
}

export function needsRefetch(state: DeckState): boolean {
  return (
    state.queue.length <= REFETCH_THRESHOLD &&
    state.emptyReason === null &&
    state.failure === null &&
    !state.loading
  );
}

export function canSwipe(state: DeckState): boolean {
  return phase(state) === "card" && !state.swiping;
}

export function deckReducer(state: DeckState, action: DeckAction): DeckState {
  switch (action.type) {
    case "reset":
      return initialDeckState;

    case "fetchStart":
      return { ...state, loading: true };

    case "fetchOk": {
      const known = new Set([...state.queue.map((c) => c.decision_id), ...state.swipedIds]);
      const fresh = action.response.cards.filter((c) => !known.has(c.decision_id));
      return {
        ...state,
        loading: false,
        queue: [...state.queue, ...fresh],
        emptyReason: fresh.length > 0 ? null : (action.response.empty_reason ?? "exhausted"),
      };
    }

    case "fetchFail":
      return { ...state, loading: false, failure: toFailure(action.error) };

    case "swipeStart":
      return canSwipe(state) ? { ...state, swiping: true, favourited: false } : state;

    case "swipeOk": {
      const { card, response } = action;
      const outcome = feedbackOutcome(response, card);
      return {
        ...state,
        swiping: false,
        queue: state.queue.filter((c) => c.decision_id !== card.decision_id),
        swipedIds: [...state.swipedIds, card.decision_id],
        favourited: response.favourited,
        pendingFeedback: outcome === "none" ? null : { card, response, compulsory: outcome === "compulsory" },
      };
    }

    case "swipeFail":
      return { ...state, swiping: false, failure: toFailure(action.error) };

    case "continue":
      return { ...state, pendingFeedback: null, favourited: false };

    case "retry":
      return { ...state, failure: null };
  }
}
