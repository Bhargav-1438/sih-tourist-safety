/**
 * Generic polling hook - the ONLY place in the app that creates an interval.
 *
 * Guarantees:
 *  - exactly one interval per mounted instance (StrictMode-safe)
 *  - overlapping requests impossible (in-flight guard skips ticks)
 *  - ticks are skipped while document.hidden, with an immediate catch-up
 *    tick + timer restart when the tab becomes visible again
 *  - full cleanup of timer and listener on unmount
 */
/**
 * Pollable wrapper around {@link usePolling}: owns request sequencing
 * (stale responses can never overwrite newer ones), retains the last
 * successful payload on failures, and exposes a manual reload.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import type { Pollable } from "../types/api";

export function usePolledSource<T>(
  loader: () => Promise<T>,
  intervalMs: number,
): Pollable<T> & { reload: () => void } {
  const [state, setState] = useState<Pollable<T>>({
    data: null,
    loading: true,
    error: null,
    stale: false,
    lastUpdated: null,
  });

  // Monotonic id: only the newest request may commit its result.
  const requestRef = useRef(0);

  const load = useCallback(async (): Promise<void> => {
    const requestId = ++requestRef.current;
    setState((prev) => ({ ...prev, loading: prev.data === null, error: null }));
    try {
      const data = await loader();
      if (requestRef.current !== requestId) return; // a newer poll finished first
      setState({
        data,
        loading: false,
        error: null,
        stale: false,
        lastUpdated: new Date().toISOString(),
      });
    } catch (cause) {
      if (requestRef.current !== requestId) return;
      const message =
        cause instanceof Error ? cause.message : "Request failed.";
      setState((prev) => ({
        ...prev,
        loading: false,
        error: message,
        stale: prev.data !== null,
      }));
    }
  }, [loader]);

  usePolling(load, intervalMs);

  return { ...state, reload: () => void load() };
}

export function usePolling(
  callback: () => void | Promise<void>,
  intervalMs: number,
  enabled = true,
): void {
  const callbackRef = useRef(callback);
  callbackRef.current = callback;

  const inFlightRef = useRef(false);
  const aliveRef = useRef(true);

  useEffect(() => {
    aliveRef.current = true;
    if (!enabled || intervalMs <= 0) return;

    let timerId: number | undefined;

    async function tick() {
      if (document.hidden || inFlightRef.current || !aliveRef.current) return;
      inFlightRef.current = true;
      try {
        await callbackRef.current();
      } catch {
        // Callers own their error handling; nothing escapes the timer.
      } finally {
        inFlightRef.current = false;
      }
    }

    function stop(): void {
      if (timerId !== undefined) {
        window.clearInterval(timerId);
        timerId = undefined;
      }
    }

    function start(): void {
      stop();
      timerId = window.setInterval(() => {
        void tick();
      }, intervalMs);
    }

    function onVisibilityChange(): void {
      if (document.hidden) {
        stop();
      } else {
        void tick();
        start();
      }
    }

    start();
    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      aliveRef.current = false;
      stop();
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [enabled, intervalMs]);
}