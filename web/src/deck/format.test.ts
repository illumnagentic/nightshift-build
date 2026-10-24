import { describe, expect, it } from "vitest";
import type { PriceQualifier, PropertyType, Tenure } from "../api/types";
import {
  commuteLine,
  floorLevelLabel,
  formatPrice,
  formatPriceWithQualifier,
  propertyTypeLabel,
  qualifierPhrase,
  tenureLabel,
} from "./format";

describe("formatPrice", () => {
  it("formats GBP with no pence and thousands separators", () => {
    expect(formatPrice(525000)).toBe("£525,000");
    expect(formatPrice(1250000)).toBe("£1,250,000");
    expect(formatPrice(99)).toBe("£99");
  });

  it("rounds away any pence", () => {
    expect(formatPrice(525000.4)).toBe("£525,000");
  });
});

describe("qualifierPhrase", () => {
  const cases: [PriceQualifier, string][] = [
    ["guide_price", "Guide price"],
    ["offers_over", "Offers over"],
    ["offers_in_region", "Offers in region of"],
    ["fixed_price", "Fixed price"],
  ];

  it.each(cases)("maps %s", (value, phrase) => {
    expect(qualifierPhrase(value)).toBe(phrase);
    expect(formatPriceWithQualifier(525000, value)).toBe(`${phrase} £525,000`);
  });

  it("gives just the price for a null qualifier", () => {
    expect(qualifierPhrase(null)).toBeNull();
    expect(formatPriceWithQualifier(525000, null)).toBe("£525,000");
  });
});

describe("propertyTypeLabel", () => {
  const cases: [PropertyType, string][] = [
    ["flat", "Flat"],
    ["maisonette", "Maisonette"],
    ["house", "House"],
    ["terraced", "Terraced"],
    ["semi_detached", "Semi-detached"],
    ["end_of_terrace", "End of terrace"],
    ["detached", "Detached"],
    ["bungalow", "Bungalow"],
    ["other", "Other"],
  ];

  it.each(cases)("maps %s", (value, label) => {
    expect(propertyTypeLabel(value)).toBe(label);
  });

  it("returns null for null", () => {
    expect(propertyTypeLabel(null)).toBeNull();
  });
});

describe("tenureLabel", () => {
  const cases: [Tenure, string][] = [
    ["freehold", "Freehold"],
    ["leasehold", "Leasehold"],
    ["share_of_freehold", "Share of freehold"],
  ];

  it.each(cases)("maps %s", (value, label) => {
    expect(tenureLabel(value)).toBe(label);
  });

  it("returns null for null", () => {
    expect(tenureLabel(null)).toBeNull();
  });
});

describe("floorLevelLabel", () => {
  it("capitalises the first letter and keeps the rest", () => {
    expect(floorLevelLabel("second floor")).toBe("Second floor");
  });

  it("returns null for null or blank text", () => {
    expect(floorLevelLabel(null)).toBeNull();
    expect(floorLevelLabel("  ")).toBeNull();
  });
});

describe("commuteLine", () => {
  it("shows minutes and postcode", () => {
    expect(commuteLine({ minutes: 32, postcode: "EC2N 2DB", assumptions: "x" })).toBe(
      "32 min to EC2N 2DB",
    );
  });

  it("says unknown when minutes is null", () => {
    expect(commuteLine({ minutes: null, postcode: "EC2N 2DB", assumptions: "x" })).toBe(
      "Commute unknown",
    );
  });
});
