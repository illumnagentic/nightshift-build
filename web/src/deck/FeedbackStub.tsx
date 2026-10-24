import { useEffect, useRef } from "react";
import "./deck.css";

export default function FeedbackStub({ onContinue }: { onContinue: () => void }) {
  const button = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    button.current?.focus();
  }, []);

  return (
    <section className="deck-feedback" aria-labelledby="deck-feedback-title">
      <h2 id="deck-feedback-title">Feedback</h2>
      <p>The feedback screen arrives in a later version.</p>
      <button type="button" className="deck-action" ref={button} onClick={onContinue}>
        Continue
      </button>
    </section>
  );
}
