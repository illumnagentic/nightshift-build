import type { Chip, ChipId, ChipStrength, FeedbackRequest } from "../api";

export type FeedbackForm = {
  answers: Partial<Record<ChipId, { strength: ChipStrength; text: string }>>;
  freeText: string;
};

export function emptyForm(): FeedbackForm {
  return { answers: {}, freeText: "" };
}

export function setAnswer(
  form: FeedbackForm,
  chipId: ChipId,
  strength: ChipStrength,
  text: string,
): FeedbackForm {
  return { ...form, answers: { ...form.answers, [chipId]: { strength, text } } };
}

export function removeAnswer(form: FeedbackForm, chipId: ChipId): FeedbackForm {
  const { [chipId]: _removed, ...answers } = form.answers;
  return { ...form, answers };
}

export function setFreeText(form: FeedbackForm, freeText: string): FeedbackForm {
  return { ...form, freeText };
}

export function canSubmit(form: FeedbackForm, compulsory: boolean): boolean {
  return !compulsory || Object.keys(form.answers).length > 0 || form.freeText.trim() !== "";
}

const orNull = (s: string) => s.trim() || null;

export function toRequest(form: FeedbackForm, chips: Chip[]): FeedbackRequest {
  return {
    chips: chips.flatMap(({ chip_id }) => {
      const answer = form.answers[chip_id];
      return answer ? [{ chip_id, strength: answer.strength, text: orNull(answer.text) }] : [];
    }),
    free_text: orNull(form.freeText),
  };
}

export function skipRequest(): FeedbackRequest {
  return { chips: [], free_text: null, skipped: true };
}
