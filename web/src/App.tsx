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
      <h1 className="mx-auto mb-5 max-w-[440px] px-4 text-center text-2xl font-semibold tracking-tight text-ink sm:text-3xl">
        Property Swipe
      </h1>
      {checking ? (
        <p className="mx-auto max-w-[440px] px-4 text-center text-sm text-muted">
          Loading…
        </p>
      ) : user ? (
        <>
          <p className="mx-auto mb-3 max-w-[440px] px-4 text-center text-sm text-muted">
            Signed in as {user.username}{" "}
            <button
              type="button"
              className="min-h-11 text-ink underline underline-offset-2 focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-income-1"
              onClick={switchUser}
            >
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
          <div hidden={tab !== "deck"} className="px-4 pb-12">
            <DeckScreen
              key={`${user.user_id}:${deckKey}`}
              userId={user.user_id}
              active={tab === "deck"}
              onNeedPrefs={() => setTab("prefs")}
            />
          </div>
          <div
            hidden={tab !== "prefs"}
            className="px-4 pb-12 [&:not([hidden])]:flex [&:not([hidden])]:justify-center"
          >
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
