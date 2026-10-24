import { useState } from "react";
import type { Card } from "../api/types";
import {
  addressLine,
  commuteLine,
  floorLevelLabel,
  formatPriceWithQualifier,
  propertyTypeLabel,
  tenureLabel,
} from "./format";
import "./deck.css";

const MAX_FEATURES = 4;

export function PropertyCard({ card }: { card: Card }) {
  const { listing, commute } = card;
  const { photos } = listing;
  const [photoIndex, setPhotoIndex] = useState(0);
  const index = Math.min(photoIndex, Math.max(photos.length - 1, 0));

  const facts = [
    listing.bedrooms === null ? null : `${listing.bedrooms} bed`,
    listing.bathrooms === null ? null : `${listing.bathrooms} bath`,
    propertyTypeLabel(listing.property_type),
  ].filter((fact): fact is string => fact !== null);

  const details = [
    listing.epc_current === null ? null : `EPC ${listing.epc_current}`,
    tenureLabel(listing.tenure),
    floorLevelLabel(listing.floor_level),
  ].filter((detail): detail is string => detail !== null);

  const address = addressLine(listing.address, listing.postcode) ?? "";
  const features = listing.key_features.slice(0, MAX_FEATURES);

  return (
    <article className="deck-card" aria-label={address || "Property"}>
      <div className="deck-card__photo">
        {photos.length === 0 ? (
          <div className="deck-card__placeholder">No photos</div>
        ) : (
          <img
            className="deck-card__image"
            src={photos[index]}
            alt={address || `Property photo ${index + 1} of ${photos.length}`}
            draggable={false}
          />
        )}
        {photos.length > 1 && (
          <>
            <button
              type="button"
              className="deck-card__nav deck-card__nav--prev"
              onClick={() => setPhotoIndex((index + photos.length - 1) % photos.length)}
              aria-label="Previous photo"
            >
              ‹
            </button>
            <button
              type="button"
              className="deck-card__nav deck-card__nav--next"
              onClick={() => setPhotoIndex((index + 1) % photos.length)}
              aria-label="Next photo"
            >
              ›
            </button>
            <span className="deck-card__count" aria-live="polite">
              {index + 1} of {photos.length}
            </span>
          </>
        )}
      </div>
      <div className="deck-card__body">
        <p className="deck-card__price">
          {formatPriceWithQualifier(listing.price_gbp, listing.price_qualifier)}
        </p>
        {facts.length > 0 && <p className="deck-card__facts">{facts.join(" · ")}</p>}
        {address && <p className="deck-card__address">{address}</p>}
        {details.length > 0 && <p className="deck-card__details">{details.join(" · ")}</p>}
        {features.length > 0 && (
          <ul className="deck-card__features">
            {features.map((feature) => (
              <li key={feature}>{feature}</li>
            ))}
          </ul>
        )}
        <p className="deck-card__commute">
          <span className="deck-card__pill">{commuteLine(commute)}</span>
          {commute.minutes !== null && (
            <span className="deck-card__assumptions">{commute.assumptions}</span>
          )}
        </p>
      </div>
    </article>
  );
}
