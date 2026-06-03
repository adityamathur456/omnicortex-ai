import { apiClient } from '@/api/client';
import type { ResumeResponse } from '@/types';

export async function generateResume(input: string) {
  const response = await apiClient.post<ResumeResponse>('/generate-resume', input, {
    headers: {
      'Content-Type': 'text/plain',
    },
  });

  return response.data;
}
