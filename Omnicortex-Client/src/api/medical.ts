import { apiClient } from '@/api/client';
import type { MedicalResponse } from '@/types';

export async function analyzeMedical(file: File, modalityHint: string) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('modality_hint', modalityHint);

  const response = await apiClient.post<MedicalResponse>('/analyze-medical', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
}
