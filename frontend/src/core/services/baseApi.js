import axios from 'axios';
import { getAccessToken, clearAccessToken } from '../utils/accessToken';

const isDevelopment = import.meta.env.DEV;
export const baseURL = isDevelopment
  ? 'http://localhost:8000'
  : '';

const api = axios.create({
  baseURL: baseURL,
});

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Only react if a token was actually sent: with no token yet, AccessGate
    // (core/components/ui/AccessGate.jsx) is already showing, and background
    // requests firing before the user submits one are expected, not an error
    // to recover from - reloading here would loop forever.
    if (error.response?.status === 401 && getAccessToken()) {
      clearAccessToken();
      window.location.reload();
    }
    return Promise.reject(error);
  }
);

export default api;
