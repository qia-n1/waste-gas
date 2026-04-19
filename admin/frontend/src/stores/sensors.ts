import { computed, ref } from "vue";
import { defineStore } from "pinia";

import type { SensorPayload } from "@/types/dashboard";

const emptySensor = (): SensorPayload => ({
  timestamp: "",
  ambient_temp: 0,
  ambient_humidity: 0,
  ambient_pressure: 0,
  coating_flow: 0,
  coating_conc: 0,
  coating_temp: 0,
  coating_pressure: 0,
  rotor_speed: 0,
  adsorption_fan_power: 0,
  desorption_fan_power: 0,
  rotor_inlet_temp: 0,
  rotor_inlet_humid: 0,
  desorption_temp: 0,
  concentrated_flow: 0,
  concentrated_conc: 0,
  concentrated_temp: 0,
  concentrated_pressure: 0,
  rto_in_flow: 0,
  rto_in_conc: 0,
  rto_in_temp: 0,
  rto_in_pressure: 0,
  burner_gas_flow: 0,
  combustion_temp: 0,
  rto_out_conc: 0,
  rto_out_temp: 0,
});

export const useSensorsStore = defineStore("sensors", () => {
  const latestSensorData = ref<SensorPayload>(emptySensor());
  const sensorHistory = ref<SensorPayload[]>([]);

  const hasData = computed(() => Boolean(latestSensorData.value.timestamp));

  const updateLatest = (payload: SensorPayload) => {
    latestSensorData.value = payload;
    sensorHistory.value = [...sensorHistory.value.slice(-95), payload];
  };

  return { latestSensorData, sensorHistory, hasData, updateLatest };
});
