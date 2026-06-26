import { useEffect, useRef } from "react";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000/api/v1";

interface DashboardPayload {
  products: number;
  active_products: number;
  low_stock_variants: number;
  customers: number;
  orders: number;
  revenue: string;
  pending_orders: number;
  recent_orders: Array<{
    id: number;
    order_number: string;
    status: string;
    total_amount: string;
    placed_at: string;
  }>;
}

export function useLiveDashboard(onUpdate: (data: DashboardPayload) => void) {
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
          data: DashboardPayload;
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
