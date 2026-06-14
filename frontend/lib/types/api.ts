export type TokenResponse = {
  access_token: string;
  token_type: string;
  expires_in: number;
};

export type GymMembership = {
  gym_id: string;
  gym_name: string;
  role: "client" | "manager" | "owner" | string;
};

export type MeResponse = {
  id: string;
  email: string;
  full_name: string;
  is_superadmin: boolean;
  is_active: boolean;
  created_at: string;
  memberships: GymMembership[];
};

export type GymResponse = {
  id: string;
  name: string;
  address: string | null;
  phone: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type ActiveMembershipSummary = {
  id: string;
  status: string;
  start_date: string;
  end_date: string | null;
};

export type GymClient = {
  id: string;
  email: string;
  full_name: string;
  document: string | null;
  role: string;
  gym_id: string;
  is_active: boolean;
  biometric_consent_at: string | null;
  active_membership: ActiveMembershipSummary | null;
  created_at: string;
};

export type UserCreatedResponse = {
  id: string;
  email: string;
  full_name: string;
  document: string | null;
  role: string;
  gym_id: string;
  is_active: boolean;
  biometric_consent_at: string | null;
  created_at: string;
  temporary_password?: string | null;
};

export type CreateGymUserPayload = {
  email?: string;
  password?: string;
  full_name: string;
  document?: string;
  kind_role?: "client" | "manager";
};

export type UpdateGymUserPayload = {
  document?: string;
  grant_biometric_consent?: boolean;
};

export type FaceEmbedding = {
  id: string;
  gym_id: string;
  user_id: string;
  created_at: string;
};

export type FaceEnrollResponse = {
  id: string;
  gym_id: string;
  user_id: string;
  created_at: string;
};

export type MembershipBrief = {
  id: string;
  status: string;
  start_date: string;
  end_date: string | null;
};

export type UserBrief = {
  id: string;
  full_name: string;
  document: string | null;
  email: string;
};

export type VerifyFaceResponse = {
  matched: boolean;
  confidence: number | null;
  result: "granted" | "denied" | "unknown" | "low_confidence" | string;
  access: "granted" | "denied" | string;
  user: UserBrief | null;
  membership: MembershipBrief | null;
  reason: string | null;
  log_id: string;
};

export type AccessLog = {
  id: string;
  gym_id: string;
  user_id: string | null;
  user_full_name: string | null;
  user_document: string | null;
  result: string;
  confidence: number | null;
  membership_status: string | null;
  detail: string | null;
  created_at: string;
};

export type AccessLogListResponse = {
  items: AccessLog[];
  limit: number;
  offset: number;
};

export type GymOnboardingRequest = {
  gym_name: string;
  gym_address: string;
  gym_phone: string;
  owner_name: string;
  password: string;
  email: string;
};

export type GymOnboardingResponse = {
  gym_name: string;
  gym_address: string;
  owner_name: string;
  owner_email: string;
  owner_access_token: string;
};

export type ApiError = {
  status: number;
  detail: string;
};
