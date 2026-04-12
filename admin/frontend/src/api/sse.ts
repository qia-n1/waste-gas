import type { PredictionPayload, SensorPayload } from "@/types/dashboard";

interface SseHandlers {
  onSensorData?: (data: SensorPayload) => void;
  onPrediction?: (data: PredictionPayload) => void;
  onStatusChange?: (connected: boolean) => void;
}

interface SseMessage<T> {
  type: string;
  data?: T;
}

export function createVocsSseConnection(handlers: SseHandlers) {
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
    if (closed || reconnectTimer !== null) {
      return;
    }
    reconnectTimer = window.setTimeout(() => {
      reconnectTimer = null;
      connect();
    }, 2500);
  };

  const connect = () => {
    clearReconnectTimer();
    source?.close();
    source = new EventSource("/vocs/events");

    source.onopen = () => {
      handlers.onStatusChange?.(true);
    };

    source.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as SseMessage<
          SensorPayload | PredictionPayload
        >;

        if (message.type === "sensor_data" && message.data) {
          handlers.onSensorData?.(message.data as SensorPayload);
        }

        if (message.type === "prediction" && message.data) {
          handlers.onPrediction?.(message.data as PredictionPayload);
        }

        if (message.type === "connected") {
          handlers.onStatusChange?.(true);
        }
      } catch (error) {
        console.error("SSE 消息解析失败", error);
      }
    };

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
