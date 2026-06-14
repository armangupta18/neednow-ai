export interface ApiError {
  success: false;
  message: string;
  error_code?: string;
  details?: unknown;
  field_errors?: Array<{ field: string; message: string }>;
}

export interface ApiSuccess<T> {
  success: true;
  data: T;
  message?: string;
  timestamp?: string;
}

export type ApiResponse<T> = ApiSuccess<T> | ApiError;
