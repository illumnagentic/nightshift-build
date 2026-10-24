import { useEffect } from "react";
import type { BlockedCode } from "./deckState";
import FeedbackStub from "./FeedbackStub";
import { PropertyCard } from "./PropertyCard";
import { useDeck } from "./useDeck";
import "./deck.css";

const BLOCKED_LINES: Record<BlockedCode, string> = {
  prefs_missing: "Save your preferences to see properties.",
  commute_pending: "Commute times are still being worked out.",
  commute_failed:
    "Commute times could not be worked out. Save your preferences again.",
};

function isTextInput(target: EventTarget | null): boolean {
  return (
    target instanceof HTMLElement &&
    (target.isContentEditable ||
      ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName))
  );
}

const FAVOURITES_NOTE = (
  <p className="deck-screen__note" role="status">
    Added to favourites
  </p>
);

export default function DeckScreen({ userId }: { userId: string }) {
  const { state, phase, card, swipe, continueAfterFeedback, retry } =
    useDeck(userId);
  const busy = state.swiping;

  useEffect(() => {
    if (phase !== "card" || busy) return;
    function onKey(e: KeyboardEvent) {
      if (
        e.repeat ||
        e.altKey ||
        e.ctrlKey ||
        e.metaKey ||
        isTextInput(e.target)
      )
        return;
      if (e.key === "ArrowLeft") swipe("left");
      else if (e.key === "ArrowRight") swipe("right");
      else if (e.key === "ArrowUp") swipe("superlike");
      else return;
      e.preventDefault();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [phase, busy, swipe]);

  const failure = state.failure;

  return (
    <div className="deck-screen">
      {phase === "loading" && <p>Loading cards…</p>}

      {phase === "card" && card && (
        <>
          {state.favourited && FAVOURITES_NOTE}
          <PropertyCard key={card.decision_id} card={card} />
          <div className="deck-screen__actions">
            <button
              type="button"
              className="deck-action"
              disabled={busy}
              onClick={() => swipe("left")}
            >
              Dislike
            </button>
            <button
              type="button"
              className="deck-action deck-action--superlike"
              disabled={busy}
              onClick={() => swipe("superlike")}
            >
              Superlike
            </button>
            <button
              type="button"
              className="deck-action"
              disabled={busy}
              onClick={() => swipe("right")}
            >
              Like
            </button>
          </div>
        </>
      )}

      {phase === "feedback" && (
        <>
          {state.pendingFeedback?.response.favourited && FAVOURITES_NOTE}
          <FeedbackStub onContinue={continueAfterFeedback} />
        </>
      )}

      {phase === "empty" && (
        <p>
          {state.emptyReason === "no_matches"
            ? "No properties match your preferences."
            : "You have seen every matching property."}
        </p>
      )}

      {phase === "blocked" && failure?.kind === "blocked" && (
        <div role="alert">
          <p>{failure.message}</p>
          <p>{BLOCKED_LINES[failure.code]}</p>
          {failure.code === "commute_pending" && (
            <button type="button" className="deck-action" onClick={retry}>
              Retry
            </button>
          )}
        </div>
      )}

      {phase === "error" && failure && (
        <div role="alert">
          <p>{failure.message}</p>
          <button type="button" className="deck-action" onClick={retry}>
            Retry
          </button>
        </div>
      )}
    </div>
  );
}
