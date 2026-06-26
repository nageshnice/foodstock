import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000/api/v1",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("food_stock_admin_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("food_stock_admin_token");
      if (!window.location.pathname.endsWith("/login")) {
        window.location.assign("/admin/login");
      }
    }
    return Promise.reject(error);
  },
);

export function apiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.message ?? error.message;
  }
  return "Something went wrong";
}
