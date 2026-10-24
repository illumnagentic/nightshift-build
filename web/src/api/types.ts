// Request and response shapes from docs/api-contract.md. IDs are opaque strings.

export type ErrorBody = { error: { code: string; message: string } };

export type ChipId =
  | "garden"
  | "parking"
  | "natural_light"
  | "balcony_terrace"
  | "price_value"
  | "commute"
  | "station_access"
  | "area_busyness"
  | "space"
  | "kitchen"
  | "layout"
  | "condition"
  | "bathrooms"
  | "floor_level"
  | "building_amenities"
  | "lease"
  | "service_charge"
  | "energy_efficiency"
  | "home_office"
  | "building_style";

export type PriceQualifier = "guide_price" | "offers_over" | "offers_in_region" | "fixed_price";
export type PropertyType =
  | "flat"
  | "maisonette"
  | "house"
  | "terraced"
  | "semi_detached"
  | "end_of_terrace"
  | "detached"
  | "bungalow"
  | "other";
export type Tenure = "freehold" | "leasehold" | "share_of_freehold";
export type EpcRating = "A" | "B" | "C" | "D" | "E" | "F" | "G";
export type CouncilTaxBand = EpcRating | "H";

// Users
export type User = { user_id: string; username: string };
export type UsersResponse = { users: User[] };
export type CreateUserRequest = { username: string };

// Prefs
export type CommuteStatus = "pending" | "ready" | "failed";

export type ParsedPrefs = {
  hard: {
    max_price_gbp: number | null;
    min_bedrooms: number | null;
    property_types: PropertyType[] | null;
    min_epc: EpcRating | null;
    tenure: Tenure | null;
    min_lease_years: number | null;
    max_commute_min: number | null;
  };
  soft: string[];
};

export type PrefsResponse = {
  text: string | null;
  commute_postcode: string | null;
  max_commute_min: number | null;
  parsed: ParsedPrefs | null;
  commute_status: CommuteStatus | null;
};

export type PutPrefsRequest = {
  text: string;
  commute_postcode: string;
  max_commute_min?: number;
};

// Listings
export type Listing = {
  id: string;
  price_gbp: number;
  price_qualifier: PriceQualifier | null;
  bedrooms: number | null;
  bathrooms: number | null;
  property_type: PropertyType | null;
  address: string | null;
  postcode: string | null;
  lat: number | null;
  lon: number | null;
  tenure: Tenure | null;
  epc_current: EpcRating | null;
  floor_level: string | null;
  key_features: string[];
  photos: string[];
};

export type Station = {
  name: string;
  distance_km: number | null;
  types: string[];
};

export type FlagRoom =
  | "living_room"
  | "kitchen"
  | "bedroom"
  | "bathroom"
  | "hallway"
  | "garden"
  | "exterior"
  | "other";

export type PhotoFlag = {
  flag_id: string;
  scope: "photo" | "listing";
  field: "room" | "light" | "size_tricks" | "defects" | "missing" | "floorplan_notes" | "sqm_estimate";
  // A number for sqm_estimate, text otherwise. Light values: none, poor, ok, bright.
  value: string | number;
  observation: string;
  source_photo: string;
  confidence: "high" | "medium" | "low";
  uncertainty: string | null;
  room: FlagRoom | null;
  corrected_text: string | null;
};

export type ListingDetail = Listing & {
  lease_years_remaining: number | null;
  service_charge_gbp_pa: number | null;
  ground_rent_gbp_pa: number | null;
  council_tax_band: CouncilTaxBand | null;
  epc_potential: EpcRating | null;
  description: string | null;
  agent_name: string | null;
  listed_date: string | null;
  floorplans: string[];
  stations: Station[];
  photo_flags: PhotoFlag[];
};

// Deck
export type Chip = { chip_id: ChipId; label: string; phrases: string[] };

export type Commute = {
  minutes: number | null;
  postcode: string;
  assumptions: string;
};

export type Card = {
  decision_id: string;
  source: "ranked" | "exploration";
  feedback_required: boolean;
  listing: Listing;
  commute: Commute;
  chips: Chip[];
};

export type DeckResponse = {
  cards: Card[];
  empty_reason: "exhausted" | "no_matches" | null;
};

// Swipe and feedback
export type SwipeAction = "left" | "right" | "superlike";
export type SwipeRequest = { action: SwipeAction };
export type SwipeResponse = {
  decision_id: string;
  action: SwipeAction;
  feedback_required: boolean;
  favourited: boolean;
  profile_version: number;
};

export type ChipStrength = "must_have" | "nice_to_have" | "would_prefer_not" | "deal_breaker";
export type ChipFeedback = { chip_id: ChipId; strength: ChipStrength; text: string | null };
export type FeedbackRequest = {
  chips: ChipFeedback[];
  free_text: string | null;
  skipped?: boolean;
};
export type FeedbackResponse = Omit<FeedbackRequest, "skipped"> & {
  decision_id: string;
  skipped: boolean;
  profile_version: number;
};

// Flag corrections
export type FlagCorrectionRequest = { text: string };
export type FlagCorrectionResponse = PhotoFlag & { profile_version: number };

// Favourites
export type Favourite = { added_at: string; listing: Listing };
export type FavouritesResponse = { favourites: Favourite[] };
export type RemoveFavouriteRequest = { reason: string };
export type RemoveFavouriteResponse = { listing_id: string; removed: boolean };

// Profile
export type ProfileCauseType = "swipe" | "feedback" | "flag_correction" | "favourite_removed";
export type ProfileResponse = {
  version: number;
  factors: { factor: ChipId; direction: string; weight: number }[];
  history: {
    version: number;
    created_at: string;
    cause: {
      type: ProfileCauseType;
      decision_id: string | null;
      flag_id: string | null;
      listing_id: string | null;
    };
  }[];
};

// Stats
export type StatSummary = { mean: number; sd: number; n_personas: number };
export type StatsArm = { hits_top5: StatSummary; false_exclude_rate: StatSummary };
export type StatsResponse = {
  arms: {
    base: StatsArm | null;
    base_memory: StatsArm | null;
    updated_memory: StatsArm | null;
  };
};
