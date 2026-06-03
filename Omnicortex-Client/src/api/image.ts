import { apiClient } from '@/api/client';
import type { ImagePayload, ImageResponse } from '@/types';

export async function generateImage(payload: ImagePayload) {
  const response = await apiClient.post<ImageResponse>('/generate-image', payload, {
    headers: {
      'Content-Type': 'application/json',
    },
  });

  return response.data;
}
