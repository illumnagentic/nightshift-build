import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "../api";
import type { CommuteStatus, ParsedPrefs } from "../api";
import { formatPrice, propertyTypeLabel, tenureLabel } from "../deck/format";
import { canSave, formFromPrefs, limitError, toRequest } from "./prefsForm";
import type { PrefsForm } from "./prefsForm";
import "./prefs.css";

const POLL_MS = 1500;
const FAILED_MESSAGE =
  "Commute times could not be worked out. Check the postcode and save again.";

function hardLimits(hard: ParsedPrefs["hard"]): string[] {
  const lines: string[] = [];
  if (hard.max_price_gbp !== null)
    lines.push(`Up to ${formatPrice(hard.max_price_gbp)}`);
  if (hard.min_bedrooms !== null) {
    lines.push(
      `At least ${hard.min_bedrooms} bedroom${hard.min_bedrooms === 1 ? "" : "s"}`,
    );
  }
  if (hard.property_types !== null && hard.property_types.length > 0) {
    const names = hard.property_types.map((t) => propertyTypeLabel(t) ?? t);
    lines.push(names.map((n, i) => (i === 0 ? n : n.toLowerCase())).join(", "));
  }
  if (hard.min_epc !== null) lines.push(`EPC ${hard.min_epc} or better`);
  if (hard.tenure !== null) lines.push(tenureLabel(hard.tenure) ?? hard.tenure);
  if (hard.min_lease_years !== null)
    lines.push(`At least ${hard.min_lease_years} years on the lease`);
  if (hard.max_commute_min !== null)
    lines.push(`Max ${hard.max_commute_min} min commute`);
  return lines;
}

export function PrefsScreen({
  userId,
  onReady,
  onSaved,
}: {
  userId: string;
  onReady: () => void;
  onSaved: () => void;
}) {
  const [form, setForm] = useState<PrefsForm>({
    text: "",
    postcode: "",
    maxCommute: "",
  });
  const [parsed, setParsed] = useState<ParsedPrefs | null>(null);
  const [status, setStatus] = useState<CommuteStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onReadyRef = useRef(onReady);
  onReadyRef.current = onReady;
  const pollId = useRef(0);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  function stopPolling() {
    pollId.current += 1;
    clearTimeout(timer.current);
  }

  function startPolling() {
    stopPolling();
    const id = pollId.current;
    const tick = () => {
      timer.current = setTimeout(async () => {
        try {
          const res = await api.getPrefs(userId);
          if (id !== pollId.current) return;
          if (res.commute_status === "ready") {
            setStatus("ready");
            onReadyRef.current();
            return;
          }
          if (res.commute_status === "failed") {
            setStatus("failed");
            return;
          }
        } catch {
          if (id !== pollId.current) return;
        }
        tick();
      }, POLL_MS);
    };
    tick();
  }

  function applyStatus(next: CommuteStatus | null) {
    setStatus(next);
    if (next === "pending") startPolling();
    else if (next === "ready") onReadyRef.current();
  }

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setSaving(false);
    api
      .getPrefs(userId)
      .then((res) => {
        if (cancelled) return;
        setForm(formFromPrefs(res));
        setParsed(res.parsed);
        setStatus(res.commute_status);
        if (res.commute_status === "pending") startPolling();
      })
      .catch((err) => {
        if (cancelled) return;
        setError(
          err instanceof ApiError
            ? err.message
            : "Could not reach the server. Try again.",
        );
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
      stopPolling();
    };
  }, [userId]);

  async function save() {
    stopPolling();
    const id = pollId.current;
    setSaving(true);
    setError(null);
    try {
      const res = await api.putPrefs(userId, toRequest(form));
      if (id !== pollId.current) return;
      setParsed(res.parsed);
      onSaved();
      applyStatus(res.commute_status);
    } catch (err) {
      if (id !== pollId.current) return;
      setError(
        err instanceof ApiError
          ? err.message
          : "Could not reach the server. Try again.",
      );
    }
    setSaving(false);
  }

  const limitProblem = limitError(form);
  const limits = parsed === null ? [] : hardLimits(parsed.hard);
  const update = (patch: Partial<PrefsForm>) =>
    setForm((f) => ({ ...f, ...patch }));

  return (
    <form
      className="prefs-screen"
      onSubmit={(e) => {
        e.preventDefault();
        if (canSave(form) && !saving) void save();
      }}
    >
      <h2 className="prefs-screen__title">Preferences</h2>

      <label className="prefs-screen__label" htmlFor="prefs-text">
        What are you looking for?
      </label>
      <textarea
        id="prefs-text"
        className="prefs-screen__input"
        rows={5}
        value={form.text}
        disabled={loading}
        onChange={(e) => update({ text: e.target.value })}
      />

      <label className="prefs-screen__label" htmlFor="prefs-postcode">
        Workplace postcode
      </label>
      <input
        id="prefs-postcode"
        className="prefs-screen__input"
        type="text"
        autoComplete="postal-code"
        value={form.postcode}
        disabled={loading}
        onChange={(e) => update({ postcode: e.target.value })}
      />

      <label className="prefs-screen__label" htmlFor="prefs-limit">
        Maximum commute (minutes, optional)
      </label>
      <input
        id="prefs-limit"
        className="prefs-screen__input"
        type="text"
        inputMode="numeric"
        value={form.maxCommute}
        disabled={loading}
        aria-invalid={limitProblem !== null}
        aria-describedby={
          limitProblem !== null ? "prefs-limit-error" : undefined
        }
        onChange={(e) => update({ maxCommute: e.target.value })}
      />
      {limitProblem !== null && (
        <p id="prefs-limit-error" className="prefs-screen__error">
          {limitProblem}
        </p>
      )}

      {error !== null && (
        <p className="prefs-screen__error" role="alert">
          {error}
        </p>
      )}

      <button
        type="submit"
        className="prefs-screen__button"
        disabled={loading || saving || !canSave(form)}
      >
        {saving ? "Saving…" : "Save"}
      </button>

      {status === "pending" && (
        <p className="prefs-screen__status" role="status">
          Working out commute times…
        </p>
      )}
      {status === "failed" && (
        <p className="prefs-screen__error" role="alert">
          {FAILED_MESSAGE}
        </p>
      )}

      {parsed !== null && (limits.length > 0 || parsed.soft.length > 0) && (
        <section
          className="prefs-screen__parsed"
          aria-label="What we understood"
        >
          <h3 className="prefs-screen__subtitle">What we understood</h3>
          {limits.length > 0 && (
            <ul className="prefs-screen__list">
              {limits.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          )}
          {parsed.soft.length > 0 && (
            <>
              <h4 className="prefs-screen__subtitle">Nice to have</h4>
              <ul className="prefs-screen__list">
                {parsed.soft.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </>
          )}
        </section>
      )}
    </form>
  );
}
