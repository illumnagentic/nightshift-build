import type { Commute, PriceQualifier, PropertyType, Tenure } from "../api/types";

const priceFormat = new Intl.NumberFormat("en-GB", {
  style: "currency",
  currency: "GBP",
  maximumFractionDigits: 0,
});

const QUALIFIER_PHRASES: Record<PriceQualifier, string> = {
  guide_price: "Guide price",
  offers_over: "Offers over",
  offers_in_region: "Offers in region of",
  fixed_price: "Fixed price",
};

const PROPERTY_TYPE_LABELS: Record<PropertyType, string> = {
  flat: "Flat",
  maisonette: "Maisonette",
  house: "House",
  terraced: "Terraced",
  semi_detached: "Semi-detached",
  end_of_terrace: "End of terrace",
  detached: "Detached",
  bungalow: "Bungalow",
  other: "Other",
};

const TENURE_LABELS: Record<Tenure, string> = {
  freehold: "Freehold",
  leasehold: "Leasehold",
  share_of_freehold: "Share of freehold",
};

export function formatPrice(gbp: number): string {
  return priceFormat.format(gbp);
}

export function qualifierPhrase(qualifier: PriceQualifier | null): string | null {
  return qualifier === null ? null : QUALIFIER_PHRASES[qualifier];
}

export function formatPriceWithQualifier(gbp: number, qualifier: PriceQualifier | null): string {
  const phrase = qualifierPhrase(qualifier);
  return phrase === null ? formatPrice(gbp) : `${phrase} ${formatPrice(gbp)}`;
}

export function propertyTypeLabel(type: PropertyType | null): string | null {
  return type === null ? null : PROPERTY_TYPE_LABELS[type];
}

export function tenureLabel(tenure: Tenure | null): string | null {
  return tenure === null ? null : TENURE_LABELS[tenure];
}

export function floorLevelLabel(floor: string | null): string | null {
  const text = floor?.trim();
  return text ? text.charAt(0).toUpperCase() + text.slice(1) : null;
}

export function commuteLine(commute: Commute): string {
  return commute.minutes === null
    ? "Commute unknown"
    : `${commute.minutes} min to ${commute.postcode}`;
}
