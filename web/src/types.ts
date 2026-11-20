export type Role = 'admin' | 'clinician' | 'researcher';
export type User = { id: number; username: string; email: string; role: Role; is_active: boolean };
export type Patient = {
  resourceType: 'Patient'; id: string; active?: boolean; name: Array<{ family?: string; given?: string[]; text?: string }>;
  gender?: string; birthDate?: string; meta?: { versionId?: string; lastUpdated?: string };
};
export type Quantity = { value: number; unit: string };
export type Trend = { code: string; name: string; unit: string; count: number; change: number; direction: string; points: Array<{ value: number; effectiveDateTime: string }> };
export type Analysis = { patient_id: string; trends: Trend[]; alerts: Array<{ code: string; label: string; value: number; message: string; severity: string }>; observation_count: number };
export type FhirBundle<T> = { resourceType: 'Bundle'; total: number; entry: Array<{ resource: T }> };
