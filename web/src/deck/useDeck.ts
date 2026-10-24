import { useCallback, useEffect, useReducer, useRef } from "react";
import { api } from "../api";
import type { SwipeAction } from "../api";
import { canSwipe, currentCard, deckReducer, initialDeckState, needsRefetch, phase } from "./deckState";

export function useDeck(userId: string) {
  const [state, dispatch] = useReducer(deckReducer, initialDeckState);
  // The user whose responses may still be applied. Cleared on unmount or user change.
  const live = useRef<string | null>(null);
  const swipeBusy = useRef(false);

  useEffect(() => {
    live.current = userId;
    swipeBusy.current = false;
    dispatch({ type: "reset" });
    return () => {
      live.current = null;
    };
  }, [userId]);

  useEffect(() => {
    if (!needsRefetch(state)) return;
    dispatch({ type: "fetchStart" });
    api.getDeck(userId).then(
      (response) => {
        if (live.current === userId) dispatch({ type: "fetchOk", response });
      },
      (error: unknown) => {
        if (live.current === userId) dispatch({ type: "fetchFail", error });
      },
    );
  }, [state, userId]);

  const card = currentCard(state);

  const swipe = useCallback(
    (action: SwipeAction) => {
      if (!card || swipeBusy.current || !canSwipe(state)) return;
      swipeBusy.current = true;
      dispatch({ type: "swipeStart" });
      api.swipe(userId, card.decision_id, { action }).then(
        (response) => {
          swipeBusy.current = false;
          if (live.current === userId) dispatch({ type: "swipeOk", card, response });
        },
        (error: unknown) => {
          swipeBusy.current = false;
          if (live.current === userId) dispatch({ type: "swipeFail", error });
        },
      );
    },
    [card, state, userId],
  );

  const continueAfterFeedback = useCallback(() => dispatch({ type: "continue" }), []);
  const retry = useCallback(() => dispatch({ type: "retry" }), []);

  return { state, phase: phase(state), card, swipe, continueAfterFeedback, retry };
}
