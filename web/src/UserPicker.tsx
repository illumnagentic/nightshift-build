import { useEffect, useState, type FormEvent } from "react";
import { api, ApiError, type User } from "./api";

function messageFor(err: unknown): string {
  return err instanceof ApiError
    ? err.message
    : "Could not reach the server. Try again.";
}

export default function UserPicker({
  onSelect,
}: {
  onSelect: (user: User) => void;
}) {
  const [users, setUsers] = useState<User[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [username, setUsername] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .listUsers()
      .then((res) => {
        if (!cancelled) setUsers(res.users);
      })
      .catch((err: unknown) => {
        if (!cancelled) setLoadError(messageFor(err));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function create(e: FormEvent) {
    e.preventDefault();
    if (username.trim() === "") return;
    setSubmitting(true);
    setCreateError(null);
    try {
      onSelect(await api.createUser({ username }));
    } catch (err) {
      setCreateError(messageFor(err));
      setSubmitting(false);
    }
  }

  return (
    <section className="mx-auto mb-12 w-[calc(100%-2rem)] max-w-[440px] rounded-[28px] border border-hairline bg-white p-6 shadow-[0_1px_2px_rgba(28,28,40,.06),0_24px_60px_-24px_rgba(79,95,208,.45)]">
      <h2 className="mb-4 text-xl font-semibold text-ink">
        Choose a user
      </h2>
      {loadError !== null ? (
        <p role="alert" className="mb-4">
          {loadError}
        </p>
      ) : users === null ? (
        <p className="mb-4 text-muted">Loading users…</p>
      ) : users.length === 0 ? (
        <p className="mb-4 text-muted">No users yet. Create one below.</p>
      ) : (
        <ul className="mb-4 flex flex-col gap-2">
          {users.map((u) => (
            <li key={u.user_id}>
              <button
                type="button"
                className="min-h-12 w-full cursor-pointer rounded-2xl bg-mist px-4 text-left font-medium hover:bg-income-3/40 focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-income-1"
                onClick={() => onSelect(u)}
              >
                {u.username}
              </button>
            </li>
          ))}
        </ul>
      )}
      <form onSubmit={create} className="flex flex-wrap items-end gap-2">
        <label
          htmlFor="new-username"
          className="mb-1 block w-full font-semibold"
        >
          New username
        </label>{" "}
        <input
          id="new-username"
          className="min-h-11 min-w-0 flex-1 rounded-xl border border-hairline bg-white px-3 focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-income-1"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoComplete="off"
        />{" "}
        <button
          type="submit"
          disabled={submitting}
          className="min-h-11 cursor-pointer rounded-full bg-pulse-1 px-5 font-semibold text-white shadow-[0_8px_20px_-8px_rgba(214,36,110,.6)] hover:brightness-95 focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-income-1 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Create user
        </button>
        {createError !== null && (
          <p role="alert" className="w-full">
            {createError}
          </p>
        )}
      </form>
    </section>
  );
}
