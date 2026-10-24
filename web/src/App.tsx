import { useEffect, useState } from "react";
import { api, type User } from "./api";
import { clearSession, getSession, setSession } from "./session";
import UserPicker from "./UserPicker";

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [checking, setChecking] = useState(() => getSession() !== null);

  useEffect(() => {
    const stored = getSession();
    if (stored === null) return;
    let cancelled = false;
    api
      .listUsers()
      .then((res) => {
        if (cancelled) return;
        const match = res.users.find((u) => u.user_id === stored.user_id);
        if (match) setUser(match);
        else clearSession();
      })
      .catch(() => {
        // Backend unreachable: show the picker, which reports its own error.
      })
      .finally(() => {
        if (!cancelled) setChecking(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function select(u: User) {
    setSession(u);
    setUser(u);
  }

  function switchUser() {
    clearSession();
    setUser(null);
  }

  return (
    <>
      <h1>Property Swipe</h1>
      {checking ? (
        <p>Loading…</p>
      ) : user ? (
        <p>
          Signed in as {user.username}{" "}
          <button type="button" onClick={switchUser}>
            Switch user
          </button>
        </p>
      ) : (
        <UserPicker onSelect={select} />
      )}
    </>
  );
}
