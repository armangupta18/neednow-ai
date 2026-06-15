/**
 * Re-exports the canonical Axios client from src/lib/api.ts.
 * Do not create a second Axios instance here — use the one from lib/api.ts.
 */
export { default, apiGet, apiPost, apiDelete } from "@/lib/api";
