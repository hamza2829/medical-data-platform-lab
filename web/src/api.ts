import type { Analysis, FhirBundle, Patient, User } from './types';

export async function api<T>(path: string, token: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: { Accept: 'application/json', ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...(token ? { Authorization: `Token ${token}` } : {}), ...options.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const login = (username: string, password: string) => api<{ token: string; user: User }>('/auth/token/', '', { method: 'POST', body: JSON.stringify({ username, password }) });
export const getPatients = (token: string) => api<FhirBundle<Patient>>('/patients/', token);
export const getPatient = (token: string, id: string) => api<Patient>(`/patients/${id}/`, token);
export const getAnalysis = (token: string, id: string) => api<Analysis>(`/patients/${id}/analysis/`, token);
export const getUsers = (token: string) => api<User[]>('/users/', token);
