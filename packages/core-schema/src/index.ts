export type UUID = string;

export type CardType = "work";

export type SkillLevel = "beginner" | "intermediate" | "advanced";

export type VerificationKind = "github" | "domain_email" | "education";
export type VerificationStatus = "pending" | "success" | "failed";

export interface PublicWorkCardProjection {
  headline: string;
  role_fit?: string;
  top_skills: string[];
  trust_score: number; // 0..100
  availability?: string | null;
  location?: string | null;
  highlights: string[];
  verification_badges: string[];
  share_assets: { qr_url: string };
  versions: { current: number };
}

export interface TrustScoreBreakdown {
  base: number;
  verified_skills: number;
  verified_experiences: number;
  recent_activity: number; // 0..10
  total: number; // capped 0..100
}


