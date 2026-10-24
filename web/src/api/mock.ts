import { ApiError, type ApiClient } from "./client";
import { createFixtures, type Fixture } from "./fixtures";
import type {
  Card,
  ChipFeedback,
  ChipId,
  ChipStrength,
  ParsedPrefs,
  PrefsResponse,
  ProfileCauseType,
  ProfileResponse,
  SwipeAction,
} from "./types";

const ONBOARDING_SWIPES = 15;
const COMMUTE_ASSUMPTIONS = "weekday, arrive 08:30, public transport";
const STRENGTHS: ChipStrength[] = [
  "must_have",
  "nice_to_have",
  "would_prefer_not",
  "deal_breaker",
];
const ACTIONS: SwipeAction[] = ["left", "right", "superlike"];

type Decision = {
  userId: string;
  fixture: Fixture;
  card: Card;
  action: SwipeAction | null;
  feedback: {
    chips: ChipFeedback[];
    free_text: string | null;
    seq: number;
  } | null;
};

type Prefs = {
  text: string;
  commute_postcode: string;
  max_commute_min: number | null;
  parsed: ParsedPrefs;
  commute_status: "pending" | "ready" | "failed";
};

type UserState = {
  prefs: Prefs | null;
  swipes: number;
  newCards: number;
  version: number;
  favourites: { listingId: string; addedAt: string }[];
  history: ProfileResponse["history"];
};

function fail(status: number, code: string, message: string): never {
  throw new ApiError(status, code, message);
}
function invalid(message: string): never {
  return fail(422, "invalid_request", message);
}
const now = () => new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
const pad = (n: number, width: number) => String(n).padStart(width, "0");
const isText = (v: unknown): v is string =>
  typeof v === "string" && v.trim() !== "";
const hash = (s: string) => [...s].reduce((h, c) => h + c.charCodeAt(0), 0);

function savedPrefs(
  text: string,
  commute_postcode: string,
  max: number | null,
  commute_status: Prefs["commute_status"],
): Prefs {
  return {
    text,
    commute_postcode,
    max_commute_min: max,
    parsed: {
      hard: {
        max_price_gbp: null,
        min_bedrooms: null,
        property_types: null,
        min_epc: null,
        tenure: null,
        min_lease_years: null,
        max_commute_min: max,
      },
      soft: text
        .split(/[,.]/)
        .map((s) => s.trim())
        .filter(Boolean),
    },
    commute_status,
  };
}

// Seeded users start with saved prefs and finished commute times.
const SEED_PREFS: Record<string, () => Prefs> = {
  u_01: () =>
    savedPrefs(
      "Two bed flat under 550k, near a tube station, bright rooms, no ground floor.",
      "EC2N 2DB",
      45,
      "ready",
    ),
  u_02: () =>
    savedPrefs(
      "Two bed flat, near a station, bright rooms, no ground floor.",
      "N1C 4AG",
      null,
      "ready",
    ),
};

// Some listings have no TfL answer, like the real backend.
function commuteMinutes(listingId: string, postcode: string): number | null {
  const h = hash(listingId);
  return h % 4 === 0 ? null : 15 + ((h + hash(postcode)) % 46);
}

export function createMockClient(): ApiClient {
  const fixtures = createFixtures();
  const users: { user_id: string; username: string }[] = [
    { user_id: "u_01", username: "alex" },
    { user_id: "u_02", username: "jordan" },
  ];
  const state = new Map<string, UserState>(
    users.map((u) => [u.user_id, newUserState(SEED_PREFS[u.user_id]?.())]),
  );
  const decisions = new Map<string, Decision>();
  let decisionSeq = 0;
  let feedbackSeq = 0;

  function newUserState(prefs: Prefs | null = null): UserState {
    return {
      prefs,
      swipes: 0,
      newCards: 0,
      version: 0,
      favourites: [],
      history: [],
    };
  }

  function user(userId: string): UserState {
    return (
      state.get(userId) ?? fail(401, "unknown_user", "No user with that id.")
    );
  }

  function decisionFor(userId: string, decisionId: string): Decision {
    const d = decisions.get(decisionId);
    return d && d.userId === userId
      ? d
      : fail(404, "decision_not_found", "No decision with that id.");
  }

  function bump(
    u: UserState,
    type: ProfileCauseType,
    cause: { decision_id?: string; flag_id?: string; listing_id?: string },
  ) {
    u.version += 1;
    u.history.unshift({
      version: u.version,
      created_at: now(),
      cause: {
        type,
        decision_id: null,
        flag_id: null,
        listing_id: null,
        ...cause,
      },
    });
    u.history.length = Math.min(u.history.length, 10);
    return u.version;
  }

  const userDecisions = (userId: string) =>
    [...decisions.values()].filter((d) => d.userId === userId);

  function favouriteListing(id: string) {
    return fixtures.find((f) => f.listing.id === id)!.listing;
  }

  return {
    async listUsers() {
      return structuredClone({ users });
    },

    async createUser(req) {
      if (!isText(req?.username)) invalid("Username is required.");
      const username = req.username.trim();
      if (
        users.some((u) => u.username.toLowerCase() === username.toLowerCase())
      ) {
        fail(409, "username_taken", "That username is taken.");
      }
      const created = { user_id: `u_${pad(users.length + 1, 2)}`, username };
      users.push(created);
      state.set(created.user_id, newUserState());
      return { ...created };
    },

    async getPrefs(userId) {
      const p = user(userId).prefs;
      if (!p)
        return {
          text: null,
          commute_postcode: null,
          max_commute_min: null,
          parsed: null,
          commute_status: null,
        };
      const response: PrefsResponse = structuredClone(p);
      // Pending resolves on the first read after the save. A reserved postcode fails instead.
      if (p.commute_status === "pending") {
        p.commute_status =
          p.commute_postcode.trim().toUpperCase() === "FAIL 1AA"
            ? "failed"
            : "ready";
        response.commute_status = p.commute_status;
      }
      return response;
    },

    async putPrefs(userId, req) {
      const u = user(userId);
      if (!isText(req?.text)) invalid("Prefs text is required.");
      if (!isText(req.commute_postcode))
        invalid("A commute postcode is required.");
      u.prefs = savedPrefs(
        req.text,
        req.commute_postcode,
        req.max_commute_min ?? null,
        "pending",
      );
      for (const [id, d] of decisions) {
        if (d.userId === userId && d.action === null) decisions.delete(id);
      }
      return structuredClone(u.prefs);
    },

    async getDeck(userId, n) {
      const u = user(userId);
      const count = n ?? 10;
      if (!Number.isInteger(count) || count < 1 || count > 10)
        invalid("n must be an integer from 1 to 10.");
      if (!u.prefs) fail(409, "prefs_missing", "Save your preferences first.");
      if (u.prefs.commute_status === "pending")
        fail(
          409,
          "commute_pending",
          "Commute times are still being calculated.",
        );
      if (u.prefs.commute_status === "failed")
        fail(
          409,
          "commute_failed",
          "Commute times failed. Save your preferences again.",
        );

      const mine = userDecisions(userId);
      const taken = new Set(mine.map((d) => d.fixture.listing.id));
      const cards = mine
        .filter((d) => d.action === null)
        .map((d) => d.card)
        .slice(0, count);
      for (const f of fixtures) {
        if (cards.length >= count) break;
        if (taken.has(f.listing.id)) continue;
        const minutes = commuteMinutes(f.listing.id, u.prefs.commute_postcode);
        const card: Card = {
          decision_id: `d_${pad(++decisionSeq, 6)}`,
          // Every fifth new card stands in for the exploration band.
          source: ++u.newCards % 5 === 0 ? "exploration" : "ranked",
          feedback_required: false,
          listing: f.listing,
          commute: {
            minutes,
            postcode: u.prefs.commute_postcode,
            assumptions: COMMUTE_ASSUMPTIONS,
          },
          chips: minutes === null ? f.chips : f.chipsWithCommute,
        };
        decisions.set(card.decision_id, {
          userId,
          fixture: f,
          card,
          action: null,
          feedback: null,
        });
        cards.push(card);
      }
      return structuredClone({
        cards: cards.map((c, i) => ({
          ...c,
          feedback_required: u.swipes + i < ONBOARDING_SWIPES,
        })),
        empty_reason: cards.length === 0 ? "exhausted" : null,
      });
    },

    async getListing(userId, listingId) {
      user(userId);
      const f = fixtures.find((x) => x.listing.id === listingId);
      return f
        ? structuredClone(f.detail)
        : fail(404, "listing_not_found", "No listing with that id.");
    },

    async swipe(userId, decisionId, req) {
      const u = user(userId);
      const d = decisionFor(userId, decisionId);
      if (!ACTIONS.includes(req?.action))
        invalid("action must be left, right or superlike.");
      if (d.action !== null)
        fail(409, "already_swiped", "That card has already been swiped.");
      const feedbackRequired = u.swipes < ONBOARDING_SWIPES;
      d.action = req.action;
      u.swipes += 1;
      const favourited = req.action === "superlike";
      if (
        favourited &&
        !u.favourites.some((f) => f.listingId === d.fixture.listing.id)
      ) {
        u.favourites.push({ listingId: d.fixture.listing.id, addedAt: now() });
      }
      const profile_version = bump(u, "swipe", { decision_id: decisionId });
      return {
        decision_id: decisionId,
        action: req.action,
        feedback_required: feedbackRequired,
        favourited,
        profile_version,
      };
    },

    async putFeedback(userId, decisionId, req) {
      const u = user(userId);
      const d = decisionFor(userId, decisionId);
      if (d.action === null)
        fail(409, "not_swiped", "Swipe the card before sending feedback.");
      if (!Array.isArray(req?.chips) || !("free_text" in req))
        invalid("chips and free_text are required.");
      if (req.free_text !== null && typeof req.free_text !== "string")
        invalid("free_text must be text or null.");
      const seen = new Set<string>();
      for (const c of req.chips) {
        if (!isText(c?.chip_id) || !STRENGTHS.includes(c.strength))
          invalid("Each chip needs a chip_id and a strength.");
        if (c.text !== null && typeof c.text !== "string")
          invalid("Chip text must be text or null.");
        if (seen.has(c.chip_id)) invalid("A chip_id was repeated.");
        seen.add(c.chip_id);
        if (!d.card.chips.some((o) => o.chip_id === c.chip_id))
          fail(
            422,
            "chip_not_offered",
            "That chip was not offered on this card.",
          );
      }
      const chips = req.chips.map((c) => ({
        chip_id: c.chip_id,
        strength: c.strength,
        text: c.text?.trim() || null,
      }));
      const free_text = req.free_text?.trim() || null;
      d.feedback = { chips, free_text, seq: ++feedbackSeq };
      const profile_version = bump(u, "feedback", { decision_id: decisionId });
      return structuredClone({
        decision_id: decisionId,
        chips,
        free_text,
        profile_version,
      });
    },

    async correctFlag(userId, flagId, req) {
      const u = user(userId);
      if (!isText(req?.text)) invalid("Correction text is required.");
      const flag = fixtures
        .flatMap((f) => f.detail.photo_flags)
        .find((x) => x.flag_id === flagId);
      if (!flag) fail(404, "flag_not_found", "No flag with that id.");
      flag!.corrected_text = req.text.trim();
      const profile_version = bump(u, "flag_correction", { flag_id: flagId });
      return structuredClone({ ...flag!, profile_version });
    },

    async getFavourites(userId) {
      const u = user(userId);
      return structuredClone({
        favourites: u.favourites.map((f) => ({
          added_at: f.addedAt,
          listing: favouriteListing(f.listingId),
        })),
      });
    },

    async removeFavourite(userId, listingId, req) {
      const u = user(userId);
      if (!isText(req?.reason))
        fail(422, "reason_required", "Say why you are removing it.");
      const i = u.favourites.findIndex((f) => f.listingId === listingId);
      if (i < 0)
        fail(404, "not_favourited", "That listing is not in your favourites.");
      u.favourites.splice(i, 1);
      bump(u, "favourite_removed", { listing_id: listingId });
      return { listing_id: listingId, removed: true };
    },

    async getProfile(userId) {
      const u = user(userId);
      // One factor per chip the user has answered. Direction is the latest answer, weight is
      // answered over offered. This is not the learning model.
      const mine = userDecisions(userId);
      const answers = mine
        .flatMap((d) =>
          d.feedback
            ? d.feedback.chips.map((c) => ({ ...c, seq: d.feedback!.seq }))
            : [],
        )
        .sort((a, b) => a.seq - b.seq);
      const ids = [...new Set(answers.map((a) => a.chip_id))] as ChipId[];
      const factors = ids.map((factor) => {
        const mineAnswers = answers.filter((a) => a.chip_id === factor);
        const latest = mineAnswers[mineAnswers.length - 1];
        const offered = mine.filter((d) =>
          d.card.chips.some((c) => c.chip_id === factor),
        ).length;
        return {
          factor,
          direction: latest.text ?? latest.strength.replace(/_/g, " "),
          weight: Math.min(
            1,
            Math.round((mineAnswers.length / offered) * 100) / 100,
          ),
        };
      });
      return structuredClone({
        version: u.version,
        factors,
        history: u.history,
      });
    },

    async getStats() {
      const arm = (
        hits: number,
        hitsSd: number,
        fer: number,
        ferSd: number,
      ) => ({
        hits_top5: { mean: hits, sd: hitsSd, n_personas: 5 },
        false_exclude_rate: { mean: fer, sd: ferSd, n_personas: 5 },
      });
      return {
        arms: {
          base: arm(2.2, 0.8, 0.31, 0.09),
          base_memory: arm(3.1, 0.7, 0.22, 0.07),
          updated_memory: arm(3.8, 0.6, 0.15, 0.06),
        },
      };
    },
  };
}

export const mockClient = createMockClient();
