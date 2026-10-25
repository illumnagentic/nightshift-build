import { useEffect } from "react";
import FeedbackScreen from "../feedback/FeedbackScreen";
import type { BlockedCode } from "./deckState";
import { PropertyCard } from "./PropertyCard";
import { SwipeableCard } from "./SwipeableCard";
import { useDeck } from "./useDeck";
import "./deck.css";

const BLOCKED_LINES: Record<BlockedCode, string> = {
  prefs_missing: "Save your preferences to see properties.",
  commute_pending: "Commute times are still being worked out.",
  commute_failed:
    "Commute times could not be worked out. Save your preferences again.",
};

function isPhotoButton(target: EventTarget | null): boolean {
  return (
    target instanceof Element &&
    target.tagName === "BUTTON" &&
    target.closest(".deck-card") !== null
  );
}

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

export default function DeckScreen({
  userId,
  active,
  onNeedPrefs,
}: {
  userId: string;
  active: boolean;
  onNeedPrefs: () => void;
}) {
  const { state, phase, card, swipe, continueAfterFeedback, retry } =
    useDeck(userId);
  const busy = state.swiping;

  useEffect(() => {
    if (!active || phase !== "card" || busy) return;
    function onKey(e: KeyboardEvent) {
      if (
        e.repeat ||
        e.altKey ||
        e.ctrlKey ||
        e.metaKey ||
        isTextInput(e.target) ||
        isPhotoButton(e.target)
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
  }, [active, phase, busy, swipe]);

  const failure = state.failure;
  const needsPrefs =
    phase === "blocked" &&
    failure?.kind === "blocked" &&
    failure.code === "prefs_missing";

  useEffect(() => {
    if (needsPrefs) onNeedPrefs();
  }, [needsPrefs]);

  return (
    <div className="deck-screen">
      {phase === "loading" && (
        <p className="deck-screen__state">Loading cards…</p>
      )}

      {phase === "card" && card && (
        <>
          {state.favourited && FAVOURITES_NOTE}
          {import.meta.env.VITE_API_MODE === "mock" &&
            card.source === "exploration" && (
              <p className="deck-screen__test-tag">Exploration (test only)</p>
            )}
          <SwipeableCard key={card.decision_id} disabled={busy} onSwipe={swipe}>
            <PropertyCard card={card} />
          </SwipeableCard>
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
              aria-label="Love"
              title="Love"
            >
              <svg
                viewBox="0 0 24 24"
                width="24"
                height="24"
                fill="currentColor"
                aria-hidden="true"
                focusable="false"
              >
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
              </svg>
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

      {phase === "feedback" && state.pendingFeedback && (
        <FeedbackScreen
          key={state.pendingFeedback.card.decision_id}
          userId={userId}
          pending={state.pendingFeedback}
          onDone={continueAfterFeedback}
        />
      )}

      {phase === "empty" && (
        <p className="deck-screen__state">
          {state.emptyReason === "no_matches"
            ? "No properties match your preferences."
            : "You have seen every matching property."}
        </p>
      )}

      {phase === "blocked" && failure?.kind === "blocked" && (
        <div role="alert" className="deck-screen__panel">
          <p>{failure.message}</p>
          <p>{BLOCKED_LINES[failure.code]}</p>
          {(failure.code === "prefs_missing" ||
            failure.code === "commute_failed") && (
            <button type="button" className="deck-action" onClick={onNeedPrefs}>
              Set preferences
            </button>
          )}
          {failure.code === "commute_pending" && (
            <button type="button" className="deck-action" onClick={retry}>
              Retry
            </button>
          )}
        </div>
      )}

      {phase === "error" && failure && (
        <div role="alert" className="deck-screen__panel">
          <p>{failure.message}</p>
          <button type="button" className="deck-action" onClick={retry}>
            Retry
          </button>
        </div>
      )}
    </div>
  );
}
