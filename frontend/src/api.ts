import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api",
  timeout: 20000,
});

export const kycProcessingTimeoutMs = 60000;

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("bizflow_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export type Product = {
  product_id: string; product_name: string; category: string; description?: string;
  unit: string; price_min_inr_per_month: number; price_max_inr_per_month: number;
  one_time_setup_inr: number; min_contract_months: number; target_segments: string[];
  available_city_tiers: number[]; requires_gstin: boolean; min_employees: number;
  min_sites: number; requires_one_of: string[];
};
export type Profile = {
  business_type: string; segment: string; city_tier: 1 | 2; employees: number;
  sites: number; gstin_active: boolean;
};
export type Quote = {
  quote_id: string; status: string; pricing_version: string; profile: Profile;
  items: { product_id: string; product_name: string; quantity: number; unit_price_inr: string; monthly_total_inr: string; setup_total_inr: string; min_contract_months: number }[];
  monthly_total_inr: string; setup_total_inr: string; accepted_at?: string | null;
};
export type Order = { order_id: string; quote_id: string; status: string; payment_status: string; installation_status: string; snapshot: Record<string, unknown>; events: { actor: string; previous_state: string; new_state: string; reason: string; at: string }[] };
export type Funnel = {
  historical_baseline: { leads: number; activated: number; conversion_rate: number };
  live_prototype: { quotes_total: number; quotes_accepted: number; kyc_verified: number; orders_total: number; orders_activated: number };
};

export const errorMessage = (error: unknown) =>
  axios.isAxiosError(error) ? (error.response?.data?.detail ?? error.message) : "Something went wrong. Please retry.";
