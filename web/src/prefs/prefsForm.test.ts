import { describe, expect, it } from "vitest";
import type { PrefsResponse } from "../api";
import { canSave, formFromPrefs, limitError, toRequest } from "./prefsForm";

const nullPrefs: PrefsResponse = {
  text: null,
  commute_postcode: null,
  max_commute_min: null,
  parsed: null,
  commute_status: null,
};

const form = (over: Partial<Parameters<typeof canSave>[0]> = {}) => ({
  text: "Two bed near a park",
  postcode: "E1 6AN",
  maxCommute: "",
  ...over,
});

describe("formFromPrefs", () => {
  it("gives empty fields for all-null prefs", () => {
    expect(formFromPrefs(nullPrefs)).toEqual({
      text: "",
      postcode: "",
      maxCommute: "",
    });
  });

  it("copies saved values and turns the limit into a string", () => {
    expect(
      formFromPrefs({
        ...nullPrefs,
        text: "Quiet street",
        commute_postcode: "N1 9GU",
        max_commute_min: 45,
      }),
    ).toEqual({ text: "Quiet street", postcode: "N1 9GU", maxCommute: "45" });
  });

  it("keeps a limit of zero as a string", () => {
    expect(formFromPrefs({ ...nullPrefs, max_commute_min: 0 }).maxCommute).toBe(
      "0",
    );
  });
});

describe("limitError", () => {
  it("accepts a blank limit", () => {
    expect(limitError(form({ maxCommute: "" }))).toBeNull();
    expect(limitError(form({ maxCommute: "   " }))).toBeNull();
  });

  it("accepts whole numbers, including padded, zero and negative", () => {
    for (const v of ["45", " 45 ", "0", "-5"])
      expect(limitError(form({ maxCommute: v }))).toBeNull();
  });

  it("rejects anything else", () => {
    for (const v of ["45.5", "abc", "4 5", "45min", "1e3", "-", "+5"]) {
      expect(limitError(form({ maxCommute: v }))).toBe(
        "Enter a whole number of minutes.",
      );
    }
  });
});

describe("canSave", () => {
  it("is true with text and postcode and a blank limit", () => {
    expect(canSave(form())).toBe(true);
  });

  it("is false when text or postcode is blank or only spaces", () => {
    expect(canSave(form({ text: "" }))).toBe(false);
    expect(canSave(form({ text: "  " }))).toBe(false);
    expect(canSave(form({ postcode: "" }))).toBe(false);
    expect(canSave(form({ postcode: "  " }))).toBe(false);
  });

  it("is false when the limit is not a whole number", () => {
    expect(canSave(form({ maxCommute: "45.5" }))).toBe(false);
  });

  it("does not check the postcode format or the limit range", () => {
    expect(canSave(form({ postcode: "nowhere", maxCommute: "0" }))).toBe(true);
    expect(canSave(form({ maxCommute: "-10" }))).toBe(true);
  });
});

describe("toRequest", () => {
  it("trims text and postcode", () => {
    expect(
      toRequest(form({ text: "  Garden  ", postcode: " E1 6AN " })),
    ).toEqual({
      text: "Garden",
      commute_postcode: "E1 6AN",
    });
  });

  it("omits max_commute_min when blank", () => {
    const request = toRequest(form({ maxCommute: "  " }));
    expect("max_commute_min" in request).toBe(false);
  });

  it("sends the limit as a number", () => {
    expect(toRequest(form({ maxCommute: " 45 " })).max_commute_min).toBe(45);
  });

  it("sends zero as a number rather than dropping it", () => {
    expect(toRequest(form({ maxCommute: "0" })).max_commute_min).toBe(0);
  });

  it("never sends an empty string", () => {
    const request = toRequest(form({ maxCommute: "" }));
    expect(Object.values(request)).not.toContain("");
  });
});
