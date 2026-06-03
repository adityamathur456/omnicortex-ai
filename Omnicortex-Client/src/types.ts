export type AuthUser = {
  email: string;
  fullName?: string;
};

export type AuthSession = {
  accessToken: string;
  user: AuthUser;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export type RegisterPayload = {
  email: string;
  password: string;
  full_name: string;
};

export type ResumeResponse = {
  latex: string;
  context_sources: string[];
  tex_key: string;
  pdf_key: string;
  pdf_url: string;
  latex_url: string;
};

export type ImagePayload = {
  prompt: string;
  mode: string;
  person_generation: 'allow_adult';
  steps: number;
};

export type ImageResponse = {
  url: string;
};

export type MedicalResponse = {
  modality: string;
  findings: string;
  possible_conditions: string[];
  confidence: string;
  recommendation: string;
  disclaimer: string;
  image_url: string;
};

export type ResumeHistoryItem = {
  id: string;
  createdAt: string;
  input: string;
  pdfUrl: string;
  result: ResumeResponse;
};

export type ImageHistoryItem = {
  id: string;
  createdAt: string;
  prompt: string;
  mode: string;
  steps: number;
  imageUrl: string;
};
