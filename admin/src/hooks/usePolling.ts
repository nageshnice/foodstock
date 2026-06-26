import { useCallback, useEffect, useRef } from "react";

export function usePolling<T>(loader: () => Promise<T>, intervalMs = 15000) {
  const loaderRef = useRef(loader);
  loaderRef.current = loader;

  const refresh = useCallback(async () => {
    return loaderRef.current();
  }, []);

  useEffect(() => {
    let active = true;
    const tick = async () => {
      try {
        await loaderRef.current();
      } catch {
        /* caller handles errors */
      }
    };
    tick();
    const timer = window.setInterval(() => {
      if (active) void tick();
    }, intervalMs);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [intervalMs]);

  return refresh;
}
