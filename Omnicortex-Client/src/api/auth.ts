import { apiClient } from '@/api/client';
import type { AuthSession, LoginPayload, RegisterPayload } from '@/types';

type LoginResponse =
  | {
      access_token?: string;
      token?: string;
      user?: {
        email?: string;
        full_name?: string;
        fullName?: string;
      };
      full_name?: string;
      fullName?: string;
      email?: string;
    }
  | string;

export async function register(payload: RegisterPayload) {
  const response = await apiClient.post('/auth/register', payload);
  return response.data;
}

export async function login(payload: LoginPayload): Promise<AuthSession> {
  const response = await apiClient.post<LoginResponse>('/auth/login', payload);
  const data = response.data;

  const accessToken =
    typeof data === 'string'
      ? data
      : data.access_token || data.token;

  if (!accessToken) {
    throw new Error('Login response did not include an access token.');
  }

  const fullName =
    typeof data === 'string'
      ? undefined
      : data.user?.full_name || data.user?.fullName || data.full_name || data.fullName;

  const email =
    typeof data === 'string'
      ? payload.email
      : data.user?.email || data.email || payload.email;

  return {
    accessToken,
    user: {
      email,
      fullName,
    },
  };
}
