import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "../api";
import type { Chip, ChipStrength, FeedbackRequest, SwipeAction } from "../api";
import { addressLine, formatPriceWithQualifier } from "../deck/format";
import type { PendingFeedback } from "../deck/deckState";
import { ChipDialog } from "./ChipDialog";
import {
  canSubmit,
  emptyForm,
  removeAnswer,
  setAnswer,
  setFreeText,
  skipRequest,
  toRequest,
} from "./feedbackForm";
import "./feedback.css";

const ACTION_LINES: Record<SwipeAction, string> = {
  left: "You passed on this",
  right: "You liked this",
  superlike: "You loved this",
};

const STRENGTH_LABELS: Record<ChipStrength, string> = {
  must_have: "Must have",
  nice_to_have: "Nice to have",
  would_prefer_not: "Would prefer not",
  deal_breaker: "Deal-breaker",
};

type Props = {
  userId: string;
  pending: PendingFeedback;
  onDone: () => void;
};

export default function FeedbackScreen({ userId, pending, onDone }: Props) {
  const { card, response, compulsory } = pending;
  const [form, setForm] = useState(emptyForm);
  const [openChip, setOpenChip] = useState<Chip | null>(null);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const noteId = "feedback-screen-hint";

  useEffect(() => {
    heading.current?.focus();
  }, []);

  async function send(body: FeedbackRequest) {
    setSending(true);
    setError(null);
    try {
      await api.putFeedback(userId, card.decision_id, body);
      onDone();
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Could not reach the server. Try again.",
      );
      setSending(false);
    }
  }

  const ready = canSubmit(form, compulsory);
  const address = addressLine(card.listing.address, card.listing.postcode);
  const openAnswer = openChip ? (form.answers[openChip.chip_id] ?? null) : null;

  return (
    <section className="feedback-screen" aria-labelledby="feedback-screen-title">
      <h2 id="feedback-screen-title" className="feedback-screen__title" tabIndex={-1} ref={heading}>
        Tell us why
      </h2>
      <p className="feedback-screen__summary">
        {ACTION_LINES[response.action]}: {formatPriceWithQualifier(card.listing.price_gbp, card.listing.price_qualifier)}
        {address && `, ${address}`}
      </p>
      {response.favourited && (
        <p className="feedback-screen__note" role="status">
          Added to favourites
        </p>
      )}

      <ul className="feedback-screen__chips" aria-label="Features">
        {card.chips.map((chip) => {
          const answer = form.answers[chip.chip_id];
          return (
            <li key={chip.chip_id}>
              <button
                type="button"
                className="feedback-screen__chip"
                aria-pressed={answer !== undefined}
                disabled={sending}
                onClick={() => setOpenChip(chip)}
              >
                {chip.label}
                {answer && (
                  <span className="feedback-screen__strength">
                    {STRENGTH_LABELS[answer.strength]}
                  </span>
                )}
              </button>
            </li>
          );
        })}
      </ul>

      <label className="feedback-screen__label" htmlFor="feedback-screen-text">
        Anything else about this property?
      </label>
      <textarea
        id="feedback-screen-text"
        className="feedback-screen__text"
        rows={3}
        value={form.freeText}
        disabled={sending}
        onChange={(event) => setForm(setFreeText(form, event.target.value))}
      />

      {compulsory && !ready && (
        <p id={noteId} className="feedback-screen__hint">
          Pick a feature or write a note to continue.
        </p>
      )}
      {error && (
        <p className="feedback-screen__error" role="alert">
          {error}
        </p>
      )}

      <div className="feedback-screen__actions">
        <button
          type="button"
          className="feedback-screen__button feedback-screen__button--primary"
          disabled={!ready || sending}
          aria-describedby={compulsory && !ready ? noteId : undefined}
          onClick={() => send(toRequest(form, card.chips))}
        >
          Done
        </button>
        {!compulsory && (
          <button
            type="button"
            className="feedback-screen__button"
            disabled={sending}
            onClick={() => send(skipRequest())}
          >
            Skip
          </button>
        )}
      </div>

      <ChipDialog
        chip={openChip}
        initial={openAnswer}
        onSave={(strength, text) => {
          if (openChip) setForm(setAnswer(form, openChip.chip_id, strength, text));
          setOpenChip(null);
        }}
        onRemove={() => {
          if (openChip) setForm(removeAnswer(form, openChip.chip_id));
          setOpenChip(null);
        }}
        onClose={() => setOpenChip(null)}
      />
    </section>
  );
}
