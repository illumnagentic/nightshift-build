import type { PrefsResponse, PutPrefsRequest } from "../api";

export type PrefsForm = {
  text: string;
  postcode: string;
  maxCommute: string;
};

export function formFromPrefs(p: PrefsResponse): PrefsForm {
  return {
    text: p.text ?? "",
    postcode: p.commute_postcode ?? "",
    maxCommute: p.max_commute_min === null ? "" : String(p.max_commute_min),
  };
}

const isWholeNumber = (s: string) => /^-?\d+$/.test(s);

export function limitError(form: PrefsForm): string | null {
  const limit = form.maxCommute.trim();
  return limit === "" || isWholeNumber(limit)
    ? null
    : "Enter a whole number of minutes.";
}

export function canSave(form: PrefsForm): boolean {
  return (
    form.text.trim() !== "" &&
    form.postcode.trim() !== "" &&
    limitError(form) === null
  );
}

export function toRequest(form: PrefsForm): PutPrefsRequest {
  const request: PutPrefsRequest = {
    text: form.text.trim(),
    commute_postcode: form.postcode.trim(),
  };
  const limit = form.maxCommute.trim();
  if (limit !== "") request.max_commute_min = Number(limit);
  return request;
}
