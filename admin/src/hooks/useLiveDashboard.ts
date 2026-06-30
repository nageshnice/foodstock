import { useEffect, useRef } from "react";
import { getStoredToken, isAuthenticated, redirectToLogin } from "../authSession";
import type { DashboardData } from "../types";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000/api/v1";

export function useLiveDashboard(onUpdate: (data: DashboardData) => void) {
  const handlerRef = useRef(onUpdate);
  handlerRef.current = onUpdate;

  useEffect(() => {
    if (!isAuthenticated()) {
      if (getStoredToken()) redirectToLogin("expired");
      return;
    }

    const token = getStoredToken();
    if (!token) return;

    const source = new EventSource(
      `${API_BASE}/admin/events/stream?token=${encodeURIComponent(token)}`,
    );

    source.addEventListener("update", (event) => {
      try {
        const envelope = JSON.parse(event.data) as {
          event: string;
          data: DashboardData;
        };
        if (envelope.event === "dashboard") {
          handlerRef.current(envelope.data);
        }
      } catch {
        /* ignore malformed events */
      }
    });

    source.onerror = () => {
      source.close();
      if (!isAuthenticated()) {
        redirectToLogin("expired");
      }
    };

    return () => source.close();
  }, []);
}
