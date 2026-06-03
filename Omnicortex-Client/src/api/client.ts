import axios from 'axios';
import { getStoredToken } from '@/utils/storage';

export const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8000',
});

apiClient.interceptors.request.use((config) => {
  const token = getStoredToken();

  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});
