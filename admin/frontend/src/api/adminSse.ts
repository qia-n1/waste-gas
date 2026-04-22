import type { AlertItem } from "@/types/dashboard";

interface DeviceStatusPayload {
  online: boolean;
  lastSeen: string | null;
  elapsedSeconds: number | null;
  timeoutThreshold: number;
}

interface AdminSseHandlers {
  onDeviceAlert?: (alert: AlertItem & { source?: string }) => void;
  onConnected?: (status: DeviceStatusPayload) => void;
  onStatusChange?: (connected: boolean) => void;
}

export function createAdminSseConnection(handlers: AdminSseHandlers) {
  let source: EventSource | null = null;
  let reconnectTimer: number | null = null;
  let closed = false;

  const clearReconnectTimer = () => {
    if (reconnectTimer !== null) {
      window.clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
  };

  const scheduleReconnect = () => {
    if (closed || reconnectTimer !== null) return;
    reconnectTimer = window.setTimeout(() => {
      reconnectTimer = null;
      connect();
    }, 3000);
  };

  const connect = () => {
    clearReconnectTimer();
    source?.close();
    // Goes through Vite proxy `/api` → admin backend (8003)
    source = new EventSource("/api/events/device-alerts");

    source.onopen = () => {
      handlers.onStatusChange?.(true);
    };

    source.addEventListener("connected", (event) => {
      try {
        const payload = JSON.parse((event as MessageEvent).data) as DeviceStatusPayload;
        handlers.onConnected?.(payload);
      } catch (error) {
        console.error("admin SSE connected payload parse failed", error);
      }
    });

    source.addEventListener("device_alert", (event) => {
      try {
        const payload = JSON.parse((event as MessageEvent).data) as AlertItem & {
          source?: string;
        };
        handlers.onDeviceAlert?.(payload);
      } catch (error) {
        console.error("admin SSE device_alert parse failed", error);
      }
    });

    source.onerror = () => {
      handlers.onStatusChange?.(false);
      source?.close();
      scheduleReconnect();
    };
  };

  const disconnect = () => {
    closed = true;
    clearReconnectTimer();
    source?.close();
    source = null;
    handlers.onStatusChange?.(false);
  };

  return { connect, disconnect };
}
