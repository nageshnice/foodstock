import { useEffect, useRef } from "react";
import type { DashboardData } from "../types";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000/api/v1";

export function useLiveDashboard(onUpdate: (data: DashboardData) => void) {
  const handlerRef = useRef(onUpdate);
  handlerRef.current = onUpdate;

  useEffect(() => {
    const token = localStorage.getItem("food_stock_admin_token");
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
    };

    return () => source.close();
  }, []);
}
