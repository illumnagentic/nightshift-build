import type {
  CreateUserRequest,
  DeckResponse,
  FavouritesResponse,
  FeedbackRequest,
  FeedbackResponse,
  FlagCorrectionRequest,
  FlagCorrectionResponse,
  ListingDetail,
  PrefsResponse,
  ProfileResponse,
  PutPrefsRequest,
  RemoveFavouriteRequest,
  RemoveFavouriteResponse,
  StatsResponse,
  SwipeRequest,
  SwipeResponse,
  User,
  UsersResponse,
} from "./types";

export class ApiError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

export interface ApiClient {
  listUsers(): Promise<UsersResponse>;
  createUser(req: CreateUserRequest): Promise<User>;
  getPrefs(userId: string): Promise<PrefsResponse>;
  putPrefs(userId: string, req: PutPrefsRequest): Promise<PrefsResponse>;
  getDeck(userId: string, n?: number): Promise<DeckResponse>;
  getListing(userId: string, listingId: string): Promise<ListingDetail>;
  swipe(userId: string, decisionId: string, req: SwipeRequest): Promise<SwipeResponse>;
  putFeedback(userId: string, decisionId: string, req: FeedbackRequest): Promise<FeedbackResponse>;
  correctFlag(userId: string, flagId: string, req: FlagCorrectionRequest): Promise<FlagCorrectionResponse>;
  getFavourites(userId: string): Promise<FavouritesResponse>;
  removeFavourite(userId: string, listingId: string, req: RemoveFavouriteRequest): Promise<RemoveFavouriteResponse>;
  getProfile(userId: string): Promise<ProfileResponse>;
  getStats(): Promise<StatsResponse>;
}
