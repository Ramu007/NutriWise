/**
 * NutriWise API client.
 *
 * Phase 0 talks to a locally-running FastAPI; Phase 1 swaps the base URL for the
 * deployed API Gateway endpoint and adds Cognito bearer tokens.
 */
import Constants from 'expo-constants';

const baseUrl: string =
  (Constants.expoConfig?.extra?.apiBaseUrl as string | undefined) ??
  process.env.EXPO_PUBLIC_API_URL ??
  'http://localhost:8000';

type FetchOptions = RequestInit & { userId?: string };

async function request<T>(path: string, opts: FetchOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((opts.headers as Record<string, string>) ?? {}),
  };
  if (opts.userId) headers['X-User-Id'] = opts.userId;

  const res = await fetch(`${baseUrl}${path}`, { ...opts, headers });
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`API ${res.status}: ${body || res.statusText}`);
  }
  return (await res.json()) as T;
}

export type HealthProfileIn = {
  sex: 'male' | 'female';
  age_years: number;
  height_cm: number;
  weight_kg: number;
  activity_level?: 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active';
  goal?: 'lose' | 'maintain' | 'gain';
  country?: 'US' | 'IN';
  dietary_preferences?: string[];
  allergies?: string[];
  health_conditions?: string[];
};

export type HealthProfileOut = HealthProfileIn & {
  user_id: string;
  bmi: number;
  bmi_category: string;
  bmr_kcal: number;
  tdee_kcal: number;
  daily_target_kcal: number;
};

export type NutritionistOut = {
  nutritionist_id: string;
  name: string;
  country: 'US' | 'IN';
  city: string;
  specialties: string[];
  languages: string[];
  virtual_rate: number;
  in_home_rate: number | null;
  rating_avg: number;
  rating_count: number;
  verification_status: 'pending' | 'approved' | 'rejected';
};

export const api = {
  baseUrl,

  upsertHealthProfile(userId: string, body: HealthProfileIn): Promise<HealthProfileOut> {
    return request<HealthProfileOut>('/v1/health/profile', {
      method: 'POST',
      body: JSON.stringify(body),
      userId,
    });
  },

  searchNutritionists(params: {
    country?: 'US' | 'IN';
    city?: string;
    specialty?: string;
    language?: string;
  }): Promise<NutritionistOut[]> {
    const q = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v) q.set(k, v);
    }
    const suffix = q.toString() ? `?${q.toString()}` : '';
    return request<NutritionistOut[]>(`/v1/nutritionists${suffix}`);
  },

  async analyzeFoodPhoto(userId: string, uri: string): Promise<unknown> {
    const form = new FormData();
    // React Native's FormData accepts a { uri, name, type } file blob.
    form.append('photo', { uri, name: 'meal.jpg', type: 'image/jpeg' } as unknown as Blob);

    const res = await fetch(`${baseUrl}/v1/food/analyze`, {
      method: 'POST',
      body: form,
      headers: { 'X-User-Id': userId },
    });
    if (!res.ok) {
      throw new Error(`analyze failed: ${res.status}`);
    }
    return (await res.json()) as unknown;
  },
};
