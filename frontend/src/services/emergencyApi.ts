import api from "./api";
import { ENDPOINTS } from "@/constants/api";
import type { EmergencyAnalyzeRequest, EmergencyAnalyzeResponse, EmergencyEscalateRequest, EmergencyEscalateResponse } from "@/types/emergency";

export async function analyzeEmergency(request: EmergencyAnalyzeRequest) {
  const response = await api.post<EmergencyAnalyzeResponse>(
    ENDPOINTS.EMERGENCY.ANALYZE,
    request
  );
  return response.data;
}

export async function escalateEmergency(request: EmergencyEscalateRequest) {
  const response = await api.post<EmergencyEscalateResponse>(
    ENDPOINTS.EMERGENCY.ESCALATE,
    request
  );
  return response.data;
}

export async function checkEmergencyHealth() {
  const response = await api.get(ENDPOINTS.EMERGENCY.HEALTH);
  return response.data;
}
