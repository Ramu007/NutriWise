/**
 * NutriWise API client.
 *
 * Auth: when a bearer token is set via `api.setAuthToken(...)`, every request
 * sends `Authorization: Bearer <token>`. For local dev without Cognito, pass
 * `userId` on the call site and the client will send `X-User-Id` — the API's
 * dev bypass will accept it.
 *
 * Food photo upload: `analyzeFoodPhotoByKey` does the recommended 3-step flow
 * — request a presigned URL, PUT the bytes straight to S3, then call
 * `/v1/food/analyze-key` with the resulting key. Keeps large image payloads
 * off the Lambda request path.
 */
import Constants from 'expo-constants';

const baseUrl: string =
  (Constants.expoConfig?.extra?.apiBaseUrl as string | undefined) ??
  process.env.EXPO_PUBLIC_API_URL ??
  'http://localhost:8000';

type ImageContentType = 'image/jpeg' | 'image/png' | 'image/webp' | 'image/gif';

let _authToken: string | null = null;

function setAuthToken(token: string | null): void {
  _authToken = token;
}

type FetchOptions = RequestInit & { userId?: string };

async function request<T>(path: string, opts: FetchOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((opts.headers as Record<string, string>) ?? {}),
  };
  if (_authToken) headers['Authorization'] = `Bearer ${_authToken}`;
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

export type PresignOut = {
  url: string;
  s3_key: string;
  expires_in: number;
  method: 'PUT';
  required_headers: Record<string, string>;
};

export type FoodPhotoAnalysis = {
  items: { name: string; serving: string; kcal: number }[];
  total_kcal: number;
  total_protein_g: number;
  total_carbs_g: number;
  total_fat_g: number;
  notes?: string;
  model_used: string;
};

function contentTypeForUri(uri: string): ImageContentType {
  const lower = uri.toLowerCase();
  if (lower.endsWith('.png')) return 'image/png';
  if (lower.endsWith('.webp')) return 'image/webp';
  if (lower.endsWith('.gif')) return 'image/gif';
  return 'image/jpeg';
}

export const api = {
  baseUrl,
  setAuthToken,

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

  /**
   * Presign → PUT to S3 → analyze. This is the path mobile should use in prod.
   */
  async analyzeFoodPhotoByKey(
    userId: string,
    uri: string,
    hint?: string,
  ): Promise<FoodPhotoAnalysis> {
    const contentType = contentTypeForUri(uri);

    const presign = await request<PresignOut>('/v1/food/uploads/presign', {
      method: 'POST',
      body: JSON.stringify({ content_type: contentType }),
      userId,
    });

    // React Native's fetch can stream a local file URI straight into a PUT body,
    // but the cleanest cross-platform path is to read the blob and send that.
    const fileRes = await fetch(uri);
    const blob = await fileRes.blob();
    const putRes = await fetch(presign.url, {
      method: 'PUT',
      headers: presign.required_headers,
      body: blob,
    });
    if (!putRes.ok) {
      const body = await putRes.text().catch(() => '');
      throw new Error(`S3 upload ${putRes.status}: ${body || putRes.statusText}`);
    }

    return request<FoodPhotoAnalysis>('/v1/food/analyze-key', {
      method: 'POST',
      body: JSON.stringify({ s3_key: presign.s3_key, hint }),
      userId,
    });
  },

  /**
   * Legacy multipart upload — handy for local dev where S3 isn't reachable
   * (e.g. behind a captive portal). Prefer `analyzeFoodPhotoByKey` in prod.
   */
  async analyzeFoodPhoto(userId: string, uri: string): Promise<FoodPhotoAnalysis> {
    const form = new FormData();
    form.append('photo', { uri, name: 'meal.jpg', type: 'image/jpeg' } as unknown as Blob);

    const headers: Record<string, string> = { 'X-User-Id': userId };
    if (_authToken) headers['Authorization'] = `Bearer ${_authToken}`;

    const res = await fetch(`${baseUrl}/v1/food/analyze`, {
      method: 'POST',
      body: form,
      headers,
    });
    if (!res.ok) {
      throw new Error(`analyze failed: ${res.status}`);
    }
    return (await res.json()) as FoodPhotoAnalysis;
  },
};
