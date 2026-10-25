import { describe, expect, it } from "vitest";
import type { Chip } from "../api";
import {
  canSubmit,
  emptyForm,
  removeAnswer,
  setAnswer,
  setFreeText,
  skipRequest,
  toRequest,
} from "./feedbackForm";

const chips: Chip[] = [
  { chip_id: "garden", label: "Garden", phrases: [] },
  { chip_id: "parking", label: "Parking", phrases: [] },
  { chip_id: "natural_light", label: "Natural light", phrases: [] },
];

describe("emptyForm", () => {
  it("has no answers and no free text", () => {
    expect(emptyForm()).toEqual({ answers: {}, freeText: "" });
  });
});

describe("setAnswer", () => {
  it("stores strength and text for a chip", () => {
    const form = setAnswer(emptyForm(), "garden", "must_have", "big lawn");
    expect(form.answers).toEqual({
      garden: { strength: "must_have", text: "big lawn" },
    });
  });

  it("replaces an existing answer for the same chip", () => {
    let form = setAnswer(emptyForm(), "garden", "must_have", "big lawn");
    form = setAnswer(form, "garden", "deal_breaker", "none");
    expect(form.answers).toEqual({
      garden: { strength: "deal_breaker", text: "none" },
    });
  });

  it("does not mutate the form it was given", () => {
    const before = emptyForm();
    setAnswer(before, "garden", "must_have", "x");
    expect(before).toEqual({ answers: {}, freeText: "" });
  });
});

describe("removeAnswer", () => {
  it("removes one chip and keeps the others", () => {
    let form = setAnswer(emptyForm(), "garden", "must_have", "");
    form = setAnswer(form, "parking", "nice_to_have", "");
    form = removeAnswer(form, "garden");
    expect(Object.keys(form.answers)).toEqual(["parking"]);
  });

  it("is a no-op for a chip with no answer", () => {
    const form = setAnswer(emptyForm(), "garden", "must_have", "");
    expect(removeAnswer(form, "parking")).toEqual(form);
  });
});

describe("setFreeText", () => {
  it("sets the card free text", () => {
    expect(setFreeText(emptyForm(), "lovely").freeText).toBe("lovely");
  });
});

describe("canSubmit", () => {
  it("is always true when optional", () => {
    expect(canSubmit(emptyForm(), false)).toBe(true);
  });

  it("is false when compulsory and empty", () => {
    expect(canSubmit(emptyForm(), true)).toBe(false);
  });

  it("is false when compulsory and the free text is only whitespace", () => {
    expect(canSubmit(setFreeText(emptyForm(), "  \n "), true)).toBe(false);
  });

  it("is true when compulsory with free text", () => {
    expect(canSubmit(setFreeText(emptyForm(), "noisy road"), true)).toBe(true);
  });

  it("is true when compulsory with a chip answer and blank text", () => {
    expect(
      canSubmit(setAnswer(emptyForm(), "garden", "nice_to_have", ""), true),
    ).toBe(true);
  });

  it("is false again once the only answer is removed", () => {
    const form = removeAnswer(
      setAnswer(emptyForm(), "garden", "nice_to_have", ""),
      "garden",
    );
    expect(canSubmit(form, true)).toBe(false);
  });
});

describe("toRequest", () => {
  it("follows the card order, not the order answers were given", () => {
    let form = setAnswer(emptyForm(), "natural_light", "must_have", "");
    form = setAnswer(form, "garden", "nice_to_have", "");
    expect(toRequest(form, chips).chips.map((c) => c.chip_id)).toEqual([
      "garden",
      "natural_light",
    ]);
  });

  it("trims text and turns blank text into null", () => {
    let form = setAnswer(emptyForm(), "garden", "must_have", "  big lawn  ");
    form = setAnswer(form, "parking", "would_prefer_not", "   ");
    form = setAnswer(form, "natural_light", "nice_to_have", "");
    expect(toRequest(form, chips).chips).toEqual([
      { chip_id: "garden", strength: "must_have", text: "big lawn" },
      { chip_id: "parking", strength: "would_prefer_not", text: null },
      { chip_id: "natural_light", strength: "nice_to_have", text: null },
    ]);
  });

  it("trims free text and turns blank free text into null", () => {
    expect(
      toRequest(setFreeText(emptyForm(), "  nice  "), chips).free_text,
    ).toBe("nice");
    expect(
      toRequest(setFreeText(emptyForm(), " \t"), chips).free_text,
    ).toBeNull();
    expect(toRequest(emptyForm(), chips).free_text).toBeNull();
  });

  it("ignores an answer for a chip that is not on the card", () => {
    let form = setAnswer(emptyForm(), "kitchen", "must_have", "big");
    form = setAnswer(form, "garden", "must_have", "");
    expect(toRequest(form, chips).chips.map((c) => c.chip_id)).toEqual([
      "garden",
    ]);
  });

  it("sends empty chips and no skipped key for an empty form", () => {
    const body = toRequest(emptyForm(), chips);
    expect(body).toEqual({ chips: [], free_text: null });
    expect("skipped" in body).toBe(false);
  });

  it("has no repeated chip_id", () => {
    let form = setAnswer(emptyForm(), "garden", "must_have", "a");
    form = setAnswer(form, "garden", "deal_breaker", "b");
    expect(toRequest(form, chips).chips).toEqual([
      { chip_id: "garden", strength: "deal_breaker", text: "b" },
    ]);
  });
});

describe("skipRequest", () => {
  it("is exactly the skip body", () => {
    expect(skipRequest()).toStrictEqual({
      chips: [],
      free_text: null,
      skipped: true,
    });
  });
});
