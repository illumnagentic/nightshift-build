import { useEffect, useId, useRef, useState } from "react";
import { api, ApiError } from "../api";
import type { Favourite } from "../api";
import { addressLine, formatPriceWithQualifier } from "../deck/format";
import "./favourites.css";

const NETWORK_MESSAGE = "Could not reach the server. Try again.";

const errorText = (err: unknown) => (err instanceof ApiError ? err.message : NETWORK_MESSAGE);

function addedOn(addedAt: string): string | null {
  const date = new Date(addedAt);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

function summary(fav: Favourite) {
  const { listing } = fav;
  return {
    price: formatPriceWithQualifier(listing.price_gbp, listing.price_qualifier),
    address: addressLine(listing.address, listing.postcode),
  };
}

function RemoveForm({
  favourite,
  userId,
  sending,
  onSending,
  onRemoved,
  onClose,
  headingId,
}: {
  favourite: Favourite;
  userId: string;
  sending: boolean;
  onSending: (sending: boolean) => void;
  onRemoved: (listingId: string) => void;
  onClose: () => void;
  headingId: string;
}) {
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const textId = useId();
  const mounted = useRef(true);
  const { price, address } = summary(favourite);
  const trimmed = reason.trim();

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  function confirm() {
    onSending(true);
    setError(null);
    api
      .removeFavourite(userId, favourite.listing.id, { reason: trimmed })
      .then(() => {
        if (mounted.current) onRemoved(favourite.listing.id);
      })
      .catch((err: unknown) => {
        if (!mounted.current) return;
        setError(errorText(err));
        onSending(false);
      });
  }

  return (
    <form
      className="favourites-dialog__form"
      onSubmit={(event) => {
        event.preventDefault();
        if (trimmed && !sending) confirm();
      }}
    >
      <h2 id={headingId} className="favourites-dialog__title">
        Remove from favourites
      </h2>
      <p className="favourites-dialog__summary">
        <strong>{price}</strong>
        {address && <span>{address}</span>}
      </p>
      <label className="favourites-dialog__label" htmlFor={textId}>
        Why are you removing it?
      </label>
      <textarea
        id={textId}
        className="favourites-dialog__text"
        rows={3}
        required
        value={reason}
        onChange={(event) => setReason(event.target.value)}
      />
      {error && (
        <p className="favourites-dialog__error" role="alert">
          {error}
        </p>
      )}
      <div className="favourites-dialog__actions">
        <button
          type="submit"
          className="favourites-dialog__button favourites-dialog__button--primary"
          disabled={!trimmed || sending}
        >
          Confirm
        </button>
        <button
          type="button"
          className="favourites-dialog__button"
          disabled={sending}
          onClick={onClose}
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

export function FavouritesScreen({ userId }: { userId: string }) {
  const [favourites, setFavourites] = useState<Favourite[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [removing, setRemoving] = useState<Favourite | null>(null);
  const [sending, setSending] = useState(false);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const opener = useRef<Element | null>(null);
  const headingId = useId();
  const open = removing !== null;

  useEffect(() => {
    let current = true;
    setFavourites(null);
    setError(null);
    setRemoving(null);
    setSending(false);
    api
      .getFavourites(userId)
      .then((res) => {
        if (current) setFavourites(res.favourites);
      })
      .catch((err: unknown) => {
        if (current) setError(errorText(err));
      });
    return () => {
      current = false;
    };
  }, [userId, attempt]);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
      if (opener.current instanceof HTMLElement) opener.current.focus();
      opener.current = null;
    }
  }, [open]);

  function startRemove(fav: Favourite, button: HTMLButtonElement) {
    opener.current = button;
    setRemoving(fav);
  }

  function removed(listingId: string) {
    setFavourites((list) => list && list.filter((f) => f.listing.id !== listingId));
    setRemoving(null);
    setSending(false);
  }

  let body;
  if (error !== null) {
    body = (
      <div className="favourites-screen__state">
        <p className="favourites-screen__error" role="alert">
          {error}
        </p>
        <button
          type="button"
          className="favourites-screen__button"
          onClick={() => setAttempt((n) => n + 1)}
        >
          Retry
        </button>
      </div>
    );
  } else if (favourites === null) {
    body = <p className="favourites-screen__state">Loading favourites…</p>;
  } else if (favourites.length === 0) {
    body = (
      <p className="favourites-screen__state">
        No favourites yet. Love a property to save it here.
      </p>
    );
  } else {
    body = (
      <ul className="favourites-screen__list">
        {favourites.map((fav) => {
          const { price, address } = summary(fav);
          const { listing } = fav;
          const added = addedOn(fav.added_at);
          return (
            <li key={listing.id} className="favourites-screen__item">
              {listing.photos.length > 0 ? (
                <img
                  className="favourites-screen__thumb"
                  src={listing.photos[0]}
                  alt={address ?? "Property photo"}
                  loading="lazy"
                />
              ) : (
                <div className="favourites-screen__thumb favourites-screen__thumb--empty" />
              )}
              <div className="favourites-screen__info">
                <p className="favourites-screen__price">{price}</p>
                {address && <p className="favourites-screen__address">{address}</p>}
                {added && <p className="favourites-screen__meta">Added {added}</p>}
              </div>
              <button
                type="button"
                className="favourites-screen__button favourites-screen__remove"
                aria-label={`Remove ${address ?? price} from favourites`}
                onClick={(event) => startRemove(fav, event.currentTarget)}
              >
                Remove
              </button>
            </li>
          );
        })}
      </ul>
    );
  }

  return (
    <section className="favourites-screen" aria-labelledby={`${headingId}-title`}>
      <h2 id={`${headingId}-title`} className="favourites-screen__title">
        Favourites
      </h2>
      {body}
      <dialog
        ref={dialogRef}
        className="favourites-dialog"
        aria-labelledby={headingId}
        onCancel={(event) => {
          event.preventDefault();
          if (!sending) setRemoving(null);
        }}
      >
        {removing && (
          <RemoveForm
            key={removing.listing.id}
            favourite={removing}
            userId={userId}
            sending={sending}
            onSending={setSending}
            onRemoved={removed}
            onClose={() => setRemoving(null)}
            headingId={headingId}
          />
        )}
      </dialog>
    </section>
  );
}
