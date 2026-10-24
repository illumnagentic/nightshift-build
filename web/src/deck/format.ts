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
  if (!text) return null;
  const label = /floor/i.test(text) ? text : `${text} floor`;
  return label.charAt(0).toUpperCase() + label.slice(1);
}

const squash = (text: string) => text.replace(/\s+/g, "").toLowerCase();

export function addressLine(address: string | null, postcode: string | null): string | null {
  const addr = address?.trim() || null;
  const code = postcode?.trim() || null;
  if (!addr || !code) return addr ?? code;
  if (squash(addr).includes(squash(code))) return addr;
  const outward = code.split(/\s+/)[0].replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const trailing = new RegExp(`(^|[^A-Za-z0-9])${outward}[\\s,.;]*$`, "i");
  return trailing.test(addr)
    ? addr.replace(trailing, (_, lead: string) => `${lead}${code}`)
    : `${addr}, ${code}`;
}

export function commuteLine(commute: Commute): string {
  return commute.minutes === null
    ? "Commute unknown"
    : `${commute.minutes} min to ${commute.postcode}`;
}
