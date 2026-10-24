import { useEffect, useId, useRef, useState } from "react";
import type { Chip, ChipStrength } from "../api";
import "./feedback.css";

type Answer = { strength: ChipStrength; text: string };

type Props = {
  chip: Chip | null;
  initial: Answer | null;
  onSave: (strength: ChipStrength, text: string) => void;
  onRemove: () => void;
  onClose: () => void;
};

const STRENGTHS: { value: ChipStrength; label: string }[] = [
  { value: "must_have", label: "Must have" },
  { value: "nice_to_have", label: "Nice to have" },
  { value: "would_prefer_not", label: "Would prefer not" },
  { value: "deal_breaker", label: "Deal-breaker" },
];

function ChipForm({
  chip,
  initial,
  headingId,
  onSave,
  onRemove,
  onClose,
}: Props & { chip: Chip; headingId: string }) {
  const [strength, setStrength] = useState<ChipStrength | null>(initial?.strength ?? null);
  const [text, setText] = useState(initial?.text ?? "");
  const textId = useId();

  return (
    <form
      className="feedback-dialog__form"
      onSubmit={(event) => {
        event.preventDefault();
        if (strength) onSave(strength, text);
      }}
    >
      <h2 id={headingId} className="feedback-dialog__title">
        {chip.label}
      </h2>

      {chip.phrases.length > 0 && (
        <ul className="feedback-dialog__phrases" aria-label="Suggested phrases">
          {chip.phrases.map((phrase) => (
            <li key={phrase}>
              <button
                type="button"
                className="feedback-dialog__phrase"
                onClick={() => setText(phrase)}
              >
                {phrase}
              </button>
            </li>
          ))}
        </ul>
      )}

      <label className="feedback-dialog__label" htmlFor={textId}>
        Your words
      </label>
      <textarea
        id={textId}
        className="feedback-dialog__text"
        rows={3}
        value={text}
        onChange={(event) => setText(event.target.value)}
      />

      <fieldset className="feedback-dialog__strengths">
        <legend>How much does this matter?</legend>
        {STRENGTHS.map((option) => (
          <label key={option.value} className="feedback-dialog__strength">
            <input
              type="radio"
              name="strength"
              value={option.value}
              required
              checked={strength === option.value}
              onChange={() => setStrength(option.value)}
            />
            <span>{option.label}</span>
          </label>
        ))}
      </fieldset>

      <div className="feedback-dialog__actions">
        <button
          type="submit"
          className="feedback-dialog__button feedback-dialog__button--primary"
          disabled={strength === null}
        >
          Save
        </button>
        <button type="button" className="feedback-dialog__button" onClick={onClose}>
          Cancel
        </button>
        {initial && (
          <button
            type="button"
            className="feedback-dialog__button feedback-dialog__button--remove"
            onClick={onRemove}
          >
            Remove
          </button>
        )}
      </div>
    </form>
  );
}

export function ChipDialog(props: Props) {
  const { chip, onClose } = props;
  const dialogRef = useRef<HTMLDialogElement>(null);
  const opener = useRef<Element | null>(null);
  const headingId = useId();
  const open = chip !== null;

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      opener.current = document.activeElement;
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
      if (opener.current instanceof HTMLElement) opener.current.focus();
      opener.current = null;
    }
  }, [open]);

  return (
    <dialog
      ref={dialogRef}
      className="feedback-dialog"
      aria-labelledby={headingId}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
    >
      {chip && <ChipForm key={chip.chip_id} {...props} chip={chip} headingId={headingId} />}
    </dialog>
  );
}
