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
    <section>
      <h2>Choose a user</h2>
      {loadError !== null ? (
        <p role="alert">{loadError}</p>
      ) : users === null ? (
        <p>Loading users…</p>
      ) : users.length === 0 ? (
        <p>No users yet. Create one below.</p>
      ) : (
        <ul>
          {users.map((u) => (
            <li key={u.user_id}>
              <button type="button" onClick={() => onSelect(u)}>
                {u.username}
              </button>
            </li>
          ))}
        </ul>
      )}
      <form onSubmit={create}>
        <label htmlFor="new-username">New username</label>{" "}
        <input
          id="new-username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoComplete="off"
        />{" "}
        <button type="submit" disabled={submitting}>
          Create user
        </button>
        {createError !== null && <p role="alert">{createError}</p>}
      </form>
    </section>
  );
}
