import { useCallback, useEffect, useReducer, useRef } from "react";
import { api } from "../api";
import type { SwipeAction } from "../api";
import {
  canSwipe,
  currentCard,
  deckReducer,
  initialDeckState,
  needsRefetch,
  phase,
} from "./deckState";

export function useDeck(userId: string) {
  const [state, dispatch] = useReducer(deckReducer, initialDeckState);
  // Bumped on every reset, user change and unmount. A response from an earlier
  // generation is dropped, including a repeat request from a doubled effect run.
  const generation = useRef(0);
  const swipeBusy = useRef(false);

  useEffect(() => {
    swipeBusy.current = false;
    dispatch({ type: "reset" });
    return () => {
      generation.current += 1;
    };
  }, [userId]);

  useEffect(() => {
    if (!needsRefetch(state)) return;
    dispatch({ type: "fetchStart" });
    const requested = generation.current;
    api.getDeck(userId).then(
      (response) => {
        if (generation.current === requested)
          dispatch({ type: "fetchOk", response });
      },
      (error: unknown) => {
        if (generation.current === requested)
          dispatch({ type: "fetchFail", error });
      },
    );
  }, [state, userId]);

  const card = currentCard(state);

  const swipe = useCallback(
    (action: SwipeAction) => {
      if (!card || swipeBusy.current || !canSwipe(state)) return;
      swipeBusy.current = true;
      dispatch({ type: "swipeStart" });
      const requested = generation.current;
      api.swipe(userId, card.decision_id, { action }).then(
        (response) => {
          swipeBusy.current = false;
          if (generation.current === requested)
            dispatch({ type: "swipeOk", card, response });
        },
        (error: unknown) => {
          swipeBusy.current = false;
          if (generation.current === requested)
            dispatch({ type: "swipeFail", error });
        },
      );
    },
    [card, state, userId],
  );

  const continueAfterFeedback = useCallback(
    () => dispatch({ type: "continue" }),
    [],
  );
  const retry = useCallback(() => dispatch({ type: "retry" }), []);

  return {
    state,
    phase: phase(state),
    card,
    swipe,
    continueAfterFeedback,
    retry,
  };
}
