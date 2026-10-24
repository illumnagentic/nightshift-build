import { describe, expect, it } from "vitest";
import { ApiError } from "../api/client";
import type { Card, DeckResponse, SwipeResponse } from "../api/types";
import {
  GENERIC_ERROR_MESSAGE,
  canSwipe,
  currentCard,
  deckReducer,
  initialDeckState,
  needsRefetch,
  phase,
  type DeckAction,
  type DeckState,
} from "./deckState";

function card(id: string, feedbackHint = false): Card {
  return {
    decision_id: id,
    source: "ranked",
    feedback_required: feedbackHint,
    listing: {
      id: `l-${id}`,
      price_gbp: 500000,
      price_qualifier: null,
      bedrooms: 2,
      bathrooms: 1,
      property_type: "flat",
      address: null,
      postcode: null,
      lat: null,
      lon: null,
      tenure: null,
      epc_current: null,
      floor_level: null,
      key_features: [],
      photos: [],
    },
    commute: { minutes: null, postcode: "EC2N 2DB", assumptions: "weekday" },
    chips: [],
  };
}

function batch(ids: string[], empty_reason: DeckResponse["empty_reason"] = null): DeckResponse {
  return { cards: ids.map((id) => card(id)), empty_reason };
}

function swipeResponse(id: string, over: Partial<SwipeResponse> = {}): SwipeResponse {
  return {
    decision_id: id,
    action: "right",
    feedback_required: false,
    favourited: false,
    profile_version: 1,
    ...over,
  };
}

function run(actions: DeckAction[], from: DeckState = initialDeckState): DeckState {
  return actions.reduce(deckReducer, from);
}

const ids = (s: DeckState) => s.queue.map((c) => c.decision_id);

describe("fetching", () => {
  it("starts in the loading phase and asks for a first batch", () => {
    expect(phase(initialDeckState)).toBe("loading");
    expect(needsRefetch(initialDeckState)).toBe(true);
  });

  it("does not ask again while a fetch is in flight", () => {
    const s = run([{ type: "fetchStart" }]);
    expect(s.loading).toBe(true);
    expect(needsRefetch(s)).toBe(false);
  });

  it("appends a batch in order and shows the first card", () => {
    const s = run([{ type: "fetchOk", response: batch(["a", "b"]) }]);
    expect(ids(s)).toEqual(["a", "b"]);
    expect(currentCard(s)?.decision_id).toBe("a");
    expect(phase(s)).toBe("card");
  });

  it("does not append a decision_id already in the queue", () => {
    const s = run([
      { type: "fetchOk", response: batch(["a", "b"]) },
      { type: "fetchOk", response: batch(["a", "b", "c"]) },
    ]);
    expect(ids(s)).toEqual(["a", "b", "c"]);
  });

  it("does not bring back a decision swiped while a fetch was in flight", () => {
    const a = card("a");
    const s = run([
      { type: "fetchOk", response: batch(["a", "b"]) },
      { type: "swipeStart" },
      { type: "swipeOk", card: a, response: swipeResponse("a") },
      { type: "fetchOk", response: batch(["a", "b", "c"]) },
    ]);
    expect(ids(s)).toEqual(["b", "c"]);
  });

  it("stops refetching when a batch adds nothing new", () => {
    const s = run([
      { type: "fetchOk", response: batch(["a"]) },
      { type: "fetchOk", response: batch(["a"]) },
    ]);
    expect(ids(s)).toEqual(["a"]);
    expect(s.emptyReason).toBe("exhausted");
    expect(needsRefetch(s)).toBe(false);
    expect(phase(s)).toBe("card");
  });
});

describe("refetch threshold", () => {
  const withCards = (n: number) =>
    run([{ type: "fetchOk", response: batch(Array.from({ length: n }, (_, i) => `c${i}`)) }]);

  it("asks for more at exactly 3 cards", () => {
    expect(needsRefetch(withCards(3))).toBe(true);
  });

  it("does not ask for more at 4 cards", () => {
    expect(needsRefetch(withCards(4))).toBe(false);
  });

  it("does not ask for more once the deck is exhausted", () => {
    const s = run([{ type: "fetchOk", response: batch([], "exhausted") }]);
    expect(needsRefetch(s)).toBe(false);
  });
});

describe("empty deck", () => {
  it("carries exhausted", () => {
    const s = run([{ type: "fetchOk", response: batch([], "exhausted") }]);
    expect(phase(s)).toBe("empty");
    expect(s.emptyReason).toBe("exhausted");
  });

  it("carries no_matches", () => {
    const s = run([{ type: "fetchOk", response: batch([], "no_matches") }]);
    expect(phase(s)).toBe("empty");
    expect(s.emptyReason).toBe("no_matches");
  });

  it("shows the cards left before the empty state", () => {
    const s = run([
      { type: "fetchOk", response: batch(["a"]) },
      { type: "fetchOk", response: batch([], "exhausted") },
    ]);
    expect(phase(s)).toBe("card");
  });
});

describe("failures", () => {
  it.each(["prefs_missing", "commute_pending", "commute_failed"])(
    "blocks on %s and keeps the server message",
    (code) => {
      const s = run([{ type: "fetchFail", error: new ApiError(409, code, `Server says ${code}`) }]);
      expect(phase(s)).toBe("blocked");
      expect(s.failure).toEqual({ kind: "blocked", code, message: `Server says ${code}` });
      expect(needsRefetch(s)).toBe(false);
    },
  );

  it("shows the message of any other ApiError as a generic error", () => {
    const s = run([{ type: "fetchFail", error: new ApiError(422, "invalid_request", "n is out of range") }]);
    expect(phase(s)).toBe("error");
    expect(s.failure).toEqual({ kind: "error", message: "n is out of range" });
  });

  it("uses the fixed message for a network failure", () => {
    const s = run([{ type: "fetchFail", error: new TypeError("Failed to fetch") }]);
    expect(phase(s)).toBe("error");
    expect(s.failure).toEqual({ kind: "error", message: GENERIC_ERROR_MESSAGE });
  });

  it("does not refetch while failed, and does again after retry", () => {
    const failed = run([{ type: "fetchFail", error: new TypeError("x") }]);
    expect(needsRefetch(failed)).toBe(false);
    expect(needsRefetch(deckReducer(failed, { type: "retry" }))).toBe(true);
  });

  it("keeps the card and shows the message when a swipe fails", () => {
    const s = run([
      { type: "fetchOk", response: batch(["a", "b", "c", "d"]) },
      { type: "swipeStart" },
      { type: "swipeFail", error: new ApiError(404, "decision_not_found", "Decision not found") },
    ]);
    expect(phase(s)).toBe("error");
    expect(s.swiping).toBe(false);
    expect(ids(s)).toEqual(["a", "b", "c", "d"]);
    const retried = deckReducer(s, { type: "retry" });
    expect(phase(retried)).toBe("card");
    expect(canSwipe(retried)).toBe(true);
  });
});

describe("swiping", () => {
  const loaded = run([{ type: "fetchOk", response: batch(["a", "b", "c", "d", "e"]) }]);

  it("sets the in-flight flag and ignores a second swipe", () => {
    const s = deckReducer(loaded, { type: "swipeStart" });
    expect(s.swiping).toBe(true);
    expect(canSwipe(s)).toBe(false);
    expect(deckReducer(s, { type: "swipeStart" })).toBe(s);
  });

  it("does not start a swipe with no card", () => {
    expect(deckReducer(initialDeckState, { type: "swipeStart" })).toBe(initialDeckState);
  });

  it("drops the swiped card and shows the next when no feedback is required", () => {
    const s = run(
      [
        { type: "swipeStart" },
        { type: "swipeOk", card: card("a"), response: swipeResponse("a") },
      ],
      loaded,
    );
    expect(ids(s)).toEqual(["b", "c", "d", "e"]);
    expect(s.swiping).toBe(false);
    expect(s.pendingFeedback).toBeNull();
    expect(phase(s)).toBe("card");
  });

  it("pauses when the response requires feedback even if the card hint is false", () => {
    const a = card("a", false);
    const s = run(
      [
        { type: "swipeStart" },
        { type: "swipeOk", card: a, response: swipeResponse("a", { feedback_required: true }) },
      ],
      loaded,
    );
    expect(phase(s)).toBe("feedback");
    expect(s.pendingFeedback?.card.decision_id).toBe("a");
    expect(s.pendingFeedback?.response.decision_id).toBe("a");
    expect(canSwipe(s)).toBe(false);
  });

  it("does not pause when the response says false even if the card hint is true", () => {
    const a = card("a", true);
    const s = run(
      [
        { type: "swipeStart" },
        { type: "swipeOk", card: a, response: swipeResponse("a", { feedback_required: false }) },
      ],
      loaded,
    );
    expect(phase(s)).toBe("card");
    expect(s.pendingFeedback).toBeNull();
    expect(currentCard(s)?.decision_id).toBe("b");
  });

  it("moves to the next card on continue", () => {
    const paused = run(
      [
        { type: "swipeStart" },
        { type: "swipeOk", card: card("a"), response: swipeResponse("a", { feedback_required: true }) },
      ],
      loaded,
    );
    const s = deckReducer(paused, { type: "continue" });
    expect(phase(s)).toBe("card");
    expect(currentCard(s)?.decision_id).toBe("b");
    expect(canSwipe(s)).toBe(true);
  });

  it("keeps favourited from the response and clears it on the next swipe", () => {
    const s = run(
      [
        { type: "swipeStart" },
        { type: "swipeOk", card: card("a"), response: swipeResponse("a", { action: "superlike", favourited: true }) },
      ],
      loaded,
    );
    expect(s.favourited).toBe(true);
    expect(deckReducer(s, { type: "swipeStart" }).favourited).toBe(false);
  });

  it("does not favourite on a right swipe", () => {
    const s = run(
      [
        { type: "swipeStart" },
        { type: "swipeOk", card: card("a"), response: swipeResponse("a") },
      ],
      loaded,
    );
    expect(s.favourited).toBe(false);
  });

  it("empties the deck after the last swipe once exhausted", () => {
    const s = run([
      { type: "fetchOk", response: batch(["a"]) },
      { type: "fetchOk", response: batch([], "exhausted") },
      { type: "swipeStart" },
      { type: "swipeOk", card: card("a"), response: swipeResponse("a") },
    ]);
    expect(phase(s)).toBe("empty");
  });
});

describe("reset", () => {
  it("returns to the initial state", () => {
    const s = run([{ type: "fetchOk", response: batch(["a"]) }, { type: "reset" }]);
    expect(s).toEqual(initialDeckState);
  });
});
