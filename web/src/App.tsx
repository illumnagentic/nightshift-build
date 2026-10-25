import { useEffect, useState } from "react";
import { api, type User } from "./api";
import { clearSession, getSession, setSession } from "./session";
import DashboardScreen from "./dashboard/DashboardScreen";
import DeckScreen from "./deck/DeckScreen";
import { FavouritesScreen } from "./favourites/FavouritesScreen";
import { PrefsScreen } from "./prefs/PrefsScreen";
import UserPicker from "./UserPicker";
import "./nav.css";

type Tab = "deck" | "prefs" | "favourites" | "results";

const TABS: { id: Tab; label: string }[] = [
  { id: "deck", label: "Deck" },
  { id: "prefs", label: "Preferences" },
  { id: "favourites", label: "Favourites" },
  { id: "results", label: "Results" },
];

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [checking, setChecking] = useState(() => getSession() !== null);
  const [tab, setTab] = useState<Tab>("deck");
  const [deckKey, setDeckKey] = useState(0);

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
    setTab("deck");
  }

  return (
    <>
      <h1>Property Swipe</h1>
      {checking ? (
        <p>Loading…</p>
      ) : user ? (
        <>
          <p>
            Signed in as {user.username}{" "}
            <button type="button" onClick={switchUser}>
              Switch user
            </button>
          </p>
          <nav className="app-nav" aria-label="Sections">
            {TABS.map((t) => (
              <button
                key={t.id}
                type="button"
                className="app-nav__tab"
                aria-current={tab === t.id ? "page" : undefined}
                onClick={() => setTab(t.id)}
              >
                {t.label}
              </button>
            ))}
          </nav>
          <div hidden={tab !== "deck"}>
            <DeckScreen
              key={`${user.user_id}:${deckKey}`}
              userId={user.user_id}
              active={tab === "deck"}
              onNeedPrefs={() => setTab("prefs")}
            />
          </div>
          <div hidden={tab !== "prefs"}>
            <PrefsScreen
              key={user.user_id}
              userId={user.user_id}
              onSaved={() => setDeckKey((k) => k + 1)}
              onReady={() => {
                setDeckKey((k) => k + 1);
                setTab((t) => (t === "prefs" ? "deck" : t));
              }}
            />
          </div>
          {tab === "favourites" && <FavouritesScreen userId={user.user_id} />}
          {tab === "results" && <DashboardScreen />}
        </>
      ) : (
        <UserPicker onSelect={select} />
      )}
    </>
  );
}
