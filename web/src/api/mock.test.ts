import { beforeEach, describe, expect, it } from "vitest";
import { ApiError, type ApiClient } from "./client";
import { createMockClient } from "./mock";
import type { Card, ChipId } from "./types";

const ALEX = "u_01";
const JORDAN = "u_02";
const PREFS = {
  text: "Two bed flat, near a station. Bright rooms",
  commute_postcode: "EC2N 2DB",
};

let api: ApiClient;

beforeEach(() => {
  api = createMockClient();
});

async function ready(userId = ALEX, postcode = PREFS.commute_postcode) {
  await api.putPrefs(userId, { ...PREFS, commute_postcode: postcode });
  return api.getPrefs(userId);
}

async function deck(userId = ALEX, n = 10) {
  return (await api.getDeck(userId, n)).cards;
}

async function expectError(p: Promise<unknown>, status: number, code: string) {
  const e = await p.then(
    () => null,
    (err: unknown) => err,
  );
  expect(e).toBeInstanceOf(ApiError);
  expect((e as ApiError).status).toBe(status);
  expect((e as ApiError).code).toBe(code);
}

describe("users", () => {
  it("lists the seeded users and creates a new one", async () => {
    expect((await api.listUsers()).users.map((u) => u.username)).toEqual([
      "alex",
      "jordan",
    ]);
    const created = await api.createUser({ username: "sam" });
    expect(created.username).toBe("sam");
    expect((await api.listUsers()).users).toHaveLength(3);
  });

  it("rejects a duplicate username with 409 username_taken", async () => {
    await expectError(
      api.createUser({ username: "alex" }),
      409,
      "username_taken",
    );
  });

  it("returns 401 unknown_user for an unknown user id on every user-scoped call", async () => {
    const calls = [
      api.getPrefs("nope"),
      api.putPrefs("nope", PREFS),
      api.getDeck("nope"),
      api.getListing("nope", "rm-163949006"),
      api.swipe("nope", "d_000001", { action: "left" }),
      api.putFeedback("nope", "d_000001", { chips: [], free_text: null }),
      api.correctFlag("nope", "f_00001", { text: "x" }),
      api.getFavourites("nope"),
      api.removeFavourite("nope", "rm-163949006", { reason: "x" }),
      api.getProfile("nope"),
    ];
    for (const c of calls) await expectError(c, 401, "unknown_user");
  });
});

describe("prefs", () => {
  it("returns the all-null shape before anything is saved", async () => {
    expect(await api.getPrefs(ALEX)).toEqual({
      text: null,
      commute_postcode: null,
      max_commute_min: null,
      parsed: null,
      commute_status: null,
    });
  });

  it("returns pending from the save and ready on the next read", async () => {
    const saved = await api.putPrefs(ALEX, { ...PREFS, max_commute_min: 40 });
    expect(saved.commute_status).toBe("pending");
    expect(saved.parsed?.hard.max_commute_min).toBe(40);
    expect(saved.parsed?.soft).toEqual([
      "Two bed flat",
      "near a station",
      "Bright rooms",
    ]);
    expect((await api.getPrefs(ALEX)).commute_status).toBe("ready");
    expect((await api.getPrefs(ALEX)).commute_status).toBe("ready");
  });

  it("returns 422 invalid_request for missing or empty text and a missing postcode", async () => {
    await expectError(
      api.putPrefs(ALEX, { text: "", commute_postcode: "EC2N 2DB" }),
      422,
      "invalid_request",
    );
    await expectError(
      api.putPrefs(ALEX, { text: "   ", commute_postcode: "EC2N 2DB" }),
      422,
      "invalid_request",
    );
    await expectError(
      api.putPrefs(ALEX, { text: "flat" } as never),
      422,
      "invalid_request",
    );
    await expectError(
      api.putPrefs(ALEX, { text: "flat", commute_postcode: "" }),
      422,
      "invalid_request",
    );
  });
});

describe("deck", () => {
  it("returns 409 prefs_missing, commute_pending and commute_failed", async () => {
    await expectError(api.getDeck(ALEX), 409, "prefs_missing");
    await api.putPrefs(ALEX, PREFS);
    await expectError(api.getDeck(ALEX), 409, "commute_pending");
    await ready(ALEX, "FAIL 1AA");
    await expectError(api.getDeck(ALEX), 409, "commute_failed");
  });

  it("returns 422 invalid_request for n outside 1-10 or not an integer", async () => {
    await ready();
    for (const n of [0, 11, 2.5, Number.NaN])
      await expectError(api.getDeck(ALEX, n), 422, "invalid_request");
  });

  it("defaults to 10 cards and honours n", async () => {
    await ready();
    expect(await deck(ALEX, 3)).toHaveLength(3);
    expect((await api.getDeck(ALEX)).cards).toHaveLength(10);
  });

  it("re-serves unswiped cards first with the same decision ids, never twice at once", async () => {
    await ready();
    const first = await deck(ALEX, 4);
    await api.swipe(ALEX, first[0].decision_id, { action: "left" });
    const second = await deck(ALEX, 6);
    expect(second.slice(0, 3).map((c) => c.decision_id)).toEqual(
      first.slice(1).map((c) => c.decision_id),
    );
    const ids = second.map((c) => c.listing.id);
    expect(new Set(ids).size).toBe(ids.length);
    expect(ids).not.toContain(first[0].listing.id);
  });

  it("marks about one card in five as exploration", async () => {
    await ready();
    const cards = await deck(ALEX, 10);
    expect(cards.filter((c) => c.source === "exploration")).toHaveLength(2);
    expect(cards.filter((c) => c.source === "ranked")).toHaveLength(8);
  });

  it("sets the feedback_required hint from swipes so far plus position", async () => {
    await ready();
    const cards = await deck(ALEX, 10);
    expect(cards.every((c) => c.feedback_required)).toBe(true);
    for (const c of cards)
      await api.swipe(ALEX, c.decision_id, { action: "left" });
    const next = await deck(ALEX, 10);
    expect(next.map((c) => c.feedback_required)).toEqual([
      true,
      true,
      true,
      true,
      true,
      false,
      false,
      false,
      false,
      false,
    ]);
  });

  it("returns an empty deck with empty_reason exhausted once every listing is swiped", async () => {
    await ready();
    for (;;) {
      const cards = await deck();
      if (cards.length === 0) break;
      for (const c of cards)
        await api.swipe(ALEX, c.decision_id, { action: "left" });
    }
    expect(await api.getDeck(ALEX)).toEqual({
      cards: [],
      empty_reason: "exhausted",
    });
  });

  it("gives a non-empty deck empty_reason null", async () => {
    await ready();
    expect((await api.getDeck(ALEX)).empty_reason).toBeNull();
  });

  it("gives commute minutes on some cards and null on others, and a commute chip only with minutes", async () => {
    await ready();
    const cards: Card[] = [];
    for (let i = 0; i < 2; i++) {
      const batch = await deck();
      cards.push(...batch);
      for (const c of batch)
        await api.swipe(ALEX, c.decision_id, { action: "left" });
    }
    expect(cards.some((c) => c.commute.minutes === null)).toBe(true);
    expect(cards.some((c) => c.commute.minutes !== null)).toBe(true);
    for (const c of cards) {
      expect(c.commute.postcode).toBe(PREFS.commute_postcode);
      expect(c.chips.some((x) => x.chip_id === "commute")).toBe(
        c.commute.minutes !== null,
      );
      expect(c.chips.length).toBeLessThanOrEqual(8);
    }
  });

  it("offers the chips the catalogue gives for a known listing", async () => {
    await ready();
    const cards: Card[] = [];
    for (let i = 0; i < 2; i++) {
      const batch = await deck();
      cards.push(...batch);
      for (const c of batch)
        await api.swipe(ALEX, c.decision_id, { action: "left" });
    }
    const card = cards.find((c) => c.listing.id === "rm-172366775")!;
    const expected: ChipId[] =
      card.commute.minutes === null
        ? [
            "parking",
            "balcony_terrace",
            "price_value",
            "space",
            "kitchen",
            "layout",
            "condition",
            "bathrooms",
          ]
        : [
            "parking",
            "balcony_terrace",
            "price_value",
            "commute",
            "space",
            "kitchen",
            "layout",
            "condition",
          ];
    expect(card.chips.map((c) => c.chip_id)).toEqual(expected);
    expect(card.chips[0].phrases).toEqual([
      "Parking is a big plus",
      "Hard to use",
      "Not enough space",
      "Don't need it",
    ]);
  });
});

describe("chip lists for hand-checked listings", () => {
  // Expected lists derived by hand from the contract's Chip catalogue: offered
  // rules, featured first then priority, at most 8. "with" has the commute chip.
  // The mock gives a listing commute minutes or not whatever the postcode, so
  // each listing has only one of the two lists.
  const expected: Record<string, { without?: ChipId[]; with?: ChipId[] }> = {
    // End-of-terrace house: garden offered by type and featured by mention;
    // station 0.789 km featured; "Refurbished" features condition.
    "rm-170906828": {
      with: [
        "garden",
        "price_value",
        "commute",
        "station_access",
        "condition",
        "natural_light",
        "area_busyness",
        "space",
      ],
    },
    // Share-of-freehold flat: floor_level, lease and service_charge offered
    // and featured; no garden, parking or balcony mention.
    "rm-91380246": {
      with: [
        "price_value",
        "commute",
        "station_access",
        "floor_level",
        "lease",
        "service_charge",
        "natural_light",
        "area_busyness",
      ],
    },
    // Semi-detached house with no commute minutes: garden, parking, kitchen
    // featured by mention.
    "rm-174367916": {
      without: [
        "garden",
        "parking",
        "price_value",
        "station_access",
        "kitchen",
        "natural_light",
        "area_busyness",
        "space",
      ],
    },
    // Maisonette with nine featured chips once commute is present, so the
    // cap cuts building_style (priority 20).
    "rm-171802127": {
      with: [
        "garden",
        "parking",
        "natural_light",
        "price_value",
        "commute",
        "station_access",
        "lease",
        "service_charge",
      ],
    },
  };

  // Copied from the contract's Preset phrases table.
  const phrases: Partial<Record<ChipId, string[]>> = {
    garden: ["Lovely garden", "Too small", "Too much upkeep", "Overlooked"],
    parking: [
      "Parking is a big plus",
      "Hard to use",
      "Not enough space",
      "Don't need it",
    ],
    floor_level: [
      "Love being up high",
      "Good floor for me",
      "Too low",
      "Too many stairs",
    ],
    lease: [
      "Long lease, fine",
      "Lease is too short",
      "Worried about extending",
      "Share of freehold helps",
    ],
    service_charge: [
      "Charge is reasonable",
      "Too high",
      "Worried it will rise",
      "Fine for what's included",
    ],
    building_style: [
      "Love the period character",
      "Prefer a modern build",
      "Too dated",
      "Character matters to me",
    ],
  };

  it("match the catalogue with and without a commute chip", async () => {
    const seen = { with: 0, without: 0 };
    for (const postcode of [
      "EC2N 2DB",
      "SW1A 1AA",
      "E1 6AN",
      "N1 9GU",
      "SE1 7PB",
    ]) {
      const client = createMockClient();
      await client.putPrefs(ALEX, { ...PREFS, commute_postcode: postcode });
      await client.getPrefs(ALEX);
      const cards: Card[] = [];
      for (let i = 0; i < 2; i++) {
        const batch = (await client.getDeck(ALEX, 10)).cards;
        cards.push(...batch);
        for (const c of batch)
          await client.swipe(ALEX, c.decision_id, { action: "left" });
      }
      for (const [id, lists] of Object.entries(expected)) {
        const card = cards.find((c) => c.listing.id === id)!;
        const key = card.commute.minutes === null ? "without" : "with";
        seen[key]++;
        expect(
          card.chips.map((c) => c.chip_id),
          `${id} ${postcode}`,
        ).toEqual(lists[key]);
        for (const chip of card.chips) {
          const want = phrases[chip.chip_id];
          if (want) expect(chip.phrases).toEqual(want);
        }
      }
    }
    expect(seen.with).toBeGreaterThan(0);
    expect(seen.without).toBeGreaterThan(0);
  });
});

describe("listings", () => {
  it("returns detail for a listing and 404 listing_not_found otherwise", async () => {
    const detail = await api.getListing(ALEX, "rm-172366775");
    expect(detail.stations.length).toBeGreaterThan(0);
    expect(detail.photo_flags.length).toBeGreaterThan(0);
    await expectError(
      api.getListing(ALEX, "rm-missing"),
      404,
      "listing_not_found",
    );
  });
});

describe("swipe", () => {
  it("sets feedback_required for the first 15 swipes only and keeps counting across a prefs re-save", async () => {
    await ready();
    const required: boolean[] = [];
    while (required.length < 16) {
      if (required.length === 8) await ready();
      for (const c of await deck(ALEX, 4)) {
        if (required.length === 16) break;
        required.push(
          (await api.swipe(ALEX, c.decision_id, { action: "left" }))
            .feedback_required,
        );
      }
    }
    expect(required.slice(0, 15).every(Boolean)).toBe(true);
    expect(required[15]).toBe(false);
  });

  it("counts onboarding per user", async () => {
    await ready();
    await ready(JORDAN);
    for (const c of await deck(ALEX, 3))
      await api.swipe(ALEX, c.decision_id, { action: "left" });
    const [card] = await deck(JORDAN, 1);
    expect(
      (await api.swipe(JORDAN, card.decision_id, { action: "right" }))
        .feedback_required,
    ).toBe(true);
  });

  it("adds a favourite on superlike only", async () => {
    await ready();
    const [a, b, c] = await deck(ALEX, 3);
    expect(
      (await api.swipe(ALEX, a.decision_id, { action: "right" })).favourited,
    ).toBe(false);
    expect(
      (await api.swipe(ALEX, b.decision_id, { action: "left" })).favourited,
    ).toBe(false);
    expect(
      (await api.swipe(ALEX, c.decision_id, { action: "superlike" }))
        .favourited,
    ).toBe(true);
    const { favourites } = await api.getFavourites(ALEX);
    expect(favourites.map((f) => f.listing.id)).toEqual([c.listing.id]);
    expect(favourites[0].added_at).toMatch(/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$/);
  });

  it("returns 404 decision_not_found for an unknown or another user's decision", async () => {
    await ready();
    const [card] = await deck(ALEX, 1);
    await expectError(
      api.swipe(ALEX, "d_unknown", { action: "left" }),
      404,
      "decision_not_found",
    );
    await expectError(
      api.swipe(JORDAN, card.decision_id, { action: "left" }),
      404,
      "decision_not_found",
    );
    await expectError(
      api.putFeedback(JORDAN, card.decision_id, { chips: [], free_text: null }),
      404,
      "decision_not_found",
    );
  });

  it("returns 409 already_swiped on a second swipe", async () => {
    await ready();
    const [card] = await deck(ALEX, 1);
    await api.swipe(ALEX, card.decision_id, { action: "left" });
    await expectError(
      api.swipe(ALEX, card.decision_id, { action: "right" }),
      409,
      "already_swiped",
    );
  });

  it("drops unswiped decisions on a prefs re-save and returns their listings to the pool", async () => {
    await ready();
    const [a, b] = await deck(ALEX, 2);
    await api.swipe(ALEX, a.decision_id, { action: "left" });
    await ready();
    await expectError(
      api.swipe(ALEX, b.decision_id, { action: "left" }),
      404,
      "decision_not_found",
    );
    await expectError(
      api.putFeedback(ALEX, b.decision_id, { chips: [], free_text: null }),
      404,
      "decision_not_found",
    );
    const next = await deck(ALEX, 10);
    expect(next.map((c) => c.listing.id)).toContain(b.listing.id);
    expect(next.map((c) => c.listing.id)).not.toContain(a.listing.id);
    expect(next.map((c) => c.decision_id)).not.toContain(b.decision_id);
    await expectError(
      api.swipe(ALEX, a.decision_id, { action: "left" }),
      409,
      "already_swiped",
    );
  });
});

describe("feedback", () => {
  async function swiped() {
    await ready();
    const [card] = await deck(ALEX, 1);
    await api.swipe(ALEX, card.decision_id, { action: "right" });
    return card;
  }

  it("returns 409 not_swiped before a swipe", async () => {
    await ready();
    const [card] = await deck(ALEX, 1);
    await expectError(
      api.putFeedback(ALEX, card.decision_id, { chips: [], free_text: null }),
      409,
      "not_swiped",
    );
  });

  it("stores chips, nulls blank text and replaces the whole answer", async () => {
    const card = await swiped();
    const id = card.chips[0].chip_id;
    const res = await api.putFeedback(ALEX, card.decision_id, {
      chips: [{ chip_id: id, strength: "must_have", text: "   " }],
      free_text: "  ",
    });
    expect(res.chips).toEqual([
      { chip_id: id, strength: "must_have", text: null },
    ]);
    expect(res.free_text).toBeNull();
    const edited = await api.putFeedback(ALEX, card.decision_id, {
      chips: [],
      free_text: "Nice",
    });
    expect(edited.chips).toEqual([]);
    expect(edited.free_text).toBe("Nice");
  });

  it("returns 422 invalid_request for missing keys and repeated chip ids", async () => {
    const card = await swiped();
    const id = card.chips[0].chip_id;
    await expectError(
      api.putFeedback(ALEX, card.decision_id, { free_text: null } as never),
      422,
      "invalid_request",
    );
    await expectError(
      api.putFeedback(ALEX, card.decision_id, { chips: [] } as never),
      422,
      "invalid_request",
    );
    const chip = { chip_id: id, strength: "nice_to_have", text: null } as const;
    await expectError(
      api.putFeedback(ALEX, card.decision_id, {
        chips: [chip, chip],
        free_text: null,
      }),
      422,
      "invalid_request",
    );
  });

  it("returns 422 chip_not_offered for a chip that was not on the card", async () => {
    const card = await swiped();
    const offered = new Set(card.chips.map((c) => c.chip_id));
    const other: ChipId = offered.has("lease") ? "garden" : "lease";
    expect(offered.has(other)).toBe(false);
    await expectError(
      api.putFeedback(ALEX, card.decision_id, {
        chips: [{ chip_id: other, strength: "must_have", text: null }],
        free_text: null,
      }),
      422,
      "chip_not_offered",
    );
  });
});

describe("flag correction", () => {
  it("sets corrected_text, shares it across users and returns the new version", async () => {
    const before = await api.getListing(ALEX, "rm-170560346");
    const flag = before.photo_flags.find((f) => f.corrected_text === null)!;
    const res = await api.correctFlag(ALEX, flag.flag_id, {
      text: "Not damp, just a shadow.",
    });
    expect(res.corrected_text).toBe("Not damp, just a shadow.");
    expect(res.profile_version).toBe(1);
    const seen = await api.getListing(JORDAN, "rm-170560346");
    expect(
      seen.photo_flags.find((f) => f.flag_id === flag.flag_id)?.corrected_text,
    ).toBe("Not damp, just a shadow.");
  });

  it("returns 422 invalid_request for empty text and 404 flag_not_found for an unknown flag", async () => {
    await expectError(
      api.correctFlag(ALEX, "f_00001", { text: " " }),
      422,
      "invalid_request",
    );
    await expectError(
      api.correctFlag(ALEX, "f_missing", { text: "x" }),
      404,
      "flag_not_found",
    );
  });

  it("does not leak into another client", async () => {
    await api.correctFlag(ALEX, "f_00001", { text: "Fixed" });
    const other = createMockClient();
    const detail = await other.getListing(ALEX, "rm-170560346");
    expect(detail.photo_flags.every((f) => f.corrected_text === null)).toBe(
      true,
    );
  });
});

describe("favourites", () => {
  async function favourited() {
    await ready();
    const [card] = await deck(ALEX, 1);
    await api.swipe(ALEX, card.decision_id, { action: "superlike" });
    return card;
  }

  it("removes a favourite with a reason", async () => {
    const card = await favourited();
    const res = await api.removeFavourite(ALEX, card.listing.id, {
      reason: "Too far",
    });
    expect(res).toEqual({ listing_id: card.listing.id, removed: true });
    expect((await api.getFavourites(ALEX)).favourites).toEqual([]);
  });

  it("returns 422 reason_required for a missing, null or blank reason", async () => {
    const card = await favourited();
    for (const reason of [undefined, null, "", "  "]) {
      await expectError(
        api.removeFavourite(ALEX, card.listing.id, { reason } as never),
        422,
        "reason_required",
      );
    }
  });

  it("returns 404 not_favourited for a listing that is not a favourite", async () => {
    await expectError(
      api.removeFavourite(ALEX, "rm-163949006", { reason: "x" }),
      404,
      "not_favourited",
    );
  });
});

describe("profile", () => {
  it("starts at version 0 with no factors or history", async () => {
    expect(await api.getProfile(ALEX)).toEqual({
      version: 0,
      factors: [],
      history: [],
    });
  });

  it("bumps the version once each for swipe, superlike, feedback, flag correction and favourite removal", async () => {
    await ready();
    const [a, b] = await deck(ALEX, 2);
    expect(
      (await api.swipe(ALEX, a.decision_id, { action: "right" }))
        .profile_version,
    ).toBe(1);
    expect(
      (await api.swipe(ALEX, b.decision_id, { action: "superlike" }))
        .profile_version,
    ).toBe(2);
    const fb = await api.putFeedback(ALEX, a.decision_id, {
      chips: [],
      free_text: null,
    });
    expect(fb.profile_version).toBe(3);
    const flag = (await api.getListing(ALEX, "rm-170560346")).photo_flags[0];
    expect(
      (await api.correctFlag(ALEX, flag.flag_id, { text: "Fine" }))
        .profile_version,
    ).toBe(4);
    await api.removeFavourite(ALEX, b.listing.id, { reason: "No" });

    const profile = await api.getProfile(ALEX);
    expect(profile.version).toBe(5);
    expect(profile.history.map((h) => h.version)).toEqual([5, 4, 3, 2, 1]);
    expect(profile.history.map((h) => h.cause)).toEqual([
      {
        type: "favourite_removed",
        decision_id: null,
        flag_id: null,
        listing_id: b.listing.id,
      },
      {
        type: "flag_correction",
        decision_id: null,
        flag_id: flag.flag_id,
        listing_id: null,
      },
      {
        type: "feedback",
        decision_id: a.decision_id,
        flag_id: null,
        listing_id: null,
      },
      {
        type: "swipe",
        decision_id: b.decision_id,
        flag_id: null,
        listing_id: null,
      },
      {
        type: "swipe",
        decision_id: a.decision_id,
        flag_id: null,
        listing_id: null,
      },
    ]);
  });

  it("keeps at most 10 history entries, newest first", async () => {
    await ready();
    const cards = await deck(ALEX, 10);
    for (const c of cards)
      await api.swipe(ALEX, c.decision_id, { action: "left" });
    await api.putFeedback(ALEX, cards[0].decision_id, {
      chips: [],
      free_text: null,
    });
    const profile = await api.getProfile(ALEX);
    expect(profile.version).toBe(11);
    expect(profile.history).toHaveLength(10);
    expect(profile.history[0].version).toBe(11);
    expect(profile.history[9].version).toBe(2);
  });

  it("lists one factor per answered chip with a weight between 0 and 1", async () => {
    await ready();
    const [card] = await deck(ALEX, 1);
    await api.swipe(ALEX, card.decision_id, { action: "right" });
    const id = card.chips[0].chip_id;
    await api.putFeedback(ALEX, card.decision_id, {
      chips: [
        {
          chip_id: id,
          strength: "deal_breaker",
          text: card.chips[0].phrases[0],
        },
      ],
      free_text: null,
    });
    const { factors } = await api.getProfile(ALEX);
    expect(factors).toEqual([
      { factor: id, direction: card.chips[0].phrases[0], weight: 1 },
    ]);
  });
});

describe("stats", () => {
  it("returns sample arms without a user", async () => {
    const { arms } = await api.getStats();
    expect(arms.base?.hits_top5.mean).toBe(2.2);
    expect(arms.updated_memory?.false_exclude_rate.n_personas).toBe(5);
  });
});
