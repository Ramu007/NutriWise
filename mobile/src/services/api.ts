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
  email?: string;
  country: 'US' | 'IN';
  city: string;
  credentials?: string[];
  specialties: string[];
  languages: string[];
  bio?: string;
  virtual_rate: number;
  in_home_rate: number | null;
  kitchen_audit_rate?: number | null;
  rating_avg: number;
  rating_count: number;
  verification_status: 'pending' | 'approved' | 'rejected';
  created_at?: string;
};

export type BookingType = 'virtual' | 'in_home' | 'kitchen_audit';
export type BookingStatus = 'pending' | 'confirmed' | 'completed' | 'cancelled';

export type BookingOut = {
  booking_id: string;
  nutritionist_id: string;
  user_id: string;
  type: BookingType;
  starts_at: string;
  duration_minutes: number;
  notes: string;
  status: BookingStatus;
  price: number;
  currency: string;
  created_at: string;
  chime_meeting_id?: string | null;
};

export type PresignOut = {
  url: string;
  s3_key: string;
  expires_in: number;
  method: 'PUT';
  required_headers: Record<string, string>;
};

export type FoodItem = {
  name: string;
  serving: string;
  kcal: number;
  protein_g?: number;
  carbs_g?: number;
  fat_g?: number;
  fiber_g?: number;
  confidence?: number;
};

export type FoodPhotoAnalysis = {
  items: FoodItem[];
  total_kcal: number;
  total_protein_g: number;
  total_carbs_g: number;
  total_fat_g: number;
  notes?: string;
  model_used: string;
};

export type MealSlot = 'breakfast' | 'lunch' | 'dinner' | 'snack';

export type FoodLogEntry = {
  entry_id: string;
  user_id: string;
  logged_at: string;
  meal: MealSlot;
  items: FoodItem[];
  source?: 'photo' | 'manual' | 'recommendation';
  photo_s3_key?: string | null;
};

export type DailySummary = {
  user_id: string;
  day: string;
  total_kcal: number;
  total_protein_g: number;
  total_carbs_g: number;
  total_fat_g: number;
  target_kcal: number;
  remaining_kcal: number;
  status: 'under' | 'on_track' | 'over';
  entry_count: number;
};

function contentTypeForUri(uri: string): ImageContentType {
  const lower = uri.toLowerCase();
  if (lower.endsWith('.png')) return 'image/png';
  if (lower.endsWith('.webp')) return 'image/webp';
  if (lower.endsWith('.gif')) return 'image/gif';
  return 'image/jpeg';
}

function isLocalBase(url: string): boolean {
  return /^https?:\/\/(localhost|127\.0\.0\.1|\[::1\]|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/.test(
    url,
  );
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

  getNutritionist(id: string): Promise<NutritionistOut> {
    return request<NutritionistOut>(`/v1/nutritionists/${encodeURIComponent(id)}`);
  },

  createBooking(
    userId: string,
    body: {
      nutritionist_id: string;
      type: BookingType;
      starts_at: string;
      duration_minutes: number;
      notes?: string;
    },
  ): Promise<BookingOut> {
    return request<BookingOut>('/v1/bookings', {
      method: 'POST',
      body: JSON.stringify({ notes: '', ...body }),
      userId,
    });
  },

  listMyBookings(userId: string): Promise<BookingOut[]> {
    return request<BookingOut[]>('/v1/bookings', { userId });
  },

  cancelBooking(userId: string, bookingId: string): Promise<BookingOut> {
    return request<BookingOut>(`/v1/bookings/${encodeURIComponent(bookingId)}/cancel`, {
      method: 'POST',
      userId,
    });
  },

  /**
   * Presign → PUT to S3 → analyze. This is the path mobile uses in prod.
   *
   * In local dev there's no reachable S3 bucket (or it's in the wrong region,
   * or CORS rejects the browser's PUT), so we fall back to the legacy
   * multipart `/analyze` path automatically. We also short-circuit the whole
   * S3 flow when the API points at localhost — it will never work from a
   * browser against a real S3 bucket, and the fallback is what we actually
   * want there.
   */
  async analyzeFoodPhotoByKey(
    userId: string,
    uri: string,
    hint?: string,
  ): Promise<FoodPhotoAnalysis> {
    if (isLocalBase(baseUrl)) {
      return api.analyzeFoodPhoto(userId, uri, hint);
    }

    try {
      const contentType = contentTypeForUri(uri);
      const presign = await request<PresignOut>('/v1/food/uploads/presign', {
        method: 'POST',
        body: JSON.stringify({ content_type: contentType }),
        userId,
      });

      // RN fetch streams a local file URI directly; web needs a real Blob.
      const fileRes = await fetch(uri);
      const blob = await fileRes.blob();
      const putRes = await fetch(presign.url, {
        method: 'PUT',
        headers: presign.required_headers,
        body: blob,
      });
      if (!putRes.ok) {
        throw new Error(`S3 PUT ${putRes.status}`);
      }

      return await request<FoodPhotoAnalysis>('/v1/food/analyze-key', {
        method: 'POST',
        body: JSON.stringify({ s3_key: presign.s3_key, hint }),
        userId,
      });
    } catch (e) {
      console.warn(
        '[nutriwise] presigned upload failed, using multipart fallback:',
        (e as Error).message,
      );
      return api.analyzeFoodPhoto(userId, uri, hint);
    }
  },

  /**
   * Legacy multipart upload — used directly in local dev (no S3 reachable)
   * and as the automatic fallback from `analyzeFoodPhotoByKey` when presign
   * or the S3 PUT fails. Prefer the key-based flow in prod.
   */
  async analyzeFoodPhoto(
    userId: string,
    uri: string,
    hint?: string,
  ): Promise<FoodPhotoAnalysis> {
    const contentType = contentTypeForUri(uri);

    // On web, `uri` is a blob URL — fetch it into a real Blob and send that.
    // On native, FormData happily accepts `{uri, name, type}`.
    const form = new FormData();
    const filename = `meal.${contentType.split('/')[1]}`;
    if (uri.startsWith('blob:') || uri.startsWith('data:') || uri.startsWith('http')) {
      const fileRes = await fetch(uri);
      const blob = await fileRes.blob();
      // Browser FormData supports (name, value, filename); RN types don't
      // declare the third arg but the native polyfill ignores it anyway.
      (form as unknown as { append: (n: string, v: Blob, f?: string) => void }).append(
        'photo',
        blob,
        filename,
      );
    } else {
      form.append('photo', {
        uri,
        name: filename,
        type: contentType,
      } as unknown as Blob);
    }
    if (hint) form.append('hint', hint);

    const headers: Record<string, string> = { 'X-User-Id': userId };
    if (_authToken) headers['Authorization'] = `Bearer ${_authToken}`;
    // Note: DO NOT set Content-Type — the browser/native stack sets the
    // multipart boundary automatically. Setting it manually breaks parsing.

    const res = await fetch(`${baseUrl}/v1/food/analyze`, {
      method: 'POST',
      body: form,
      headers,
    });
    if (!res.ok) {
      const body = await res.text().catch(() => '');
      throw new Error(`analyze failed ${res.status}: ${body || res.statusText}`);
    }
    return (await res.json()) as FoodPhotoAnalysis;
  },

  addFoodLog(
    userId: string,
    entry: {
      meal: MealSlot;
      items: FoodItem[];
      source?: 'photo' | 'manual' | 'recommendation';
      logged_at?: string;
    },
  ): Promise<FoodLogEntry> {
    const body: Partial<FoodLogEntry> = {
      entry_id: '',
      user_id: userId,
      logged_at: entry.logged_at ?? new Date().toISOString(),
      meal: entry.meal,
      items: entry.items,
      source: entry.source ?? 'photo',
    };
    return request<FoodLogEntry>('/v1/food/logs', {
      method: 'POST',
      body: JSON.stringify(body),
      userId,
    });
  },

  listFoodLogs(userId: string, day?: string): Promise<FoodLogEntry[]> {
    const suffix = day ? `?day=${encodeURIComponent(day)}` : '';
    return request<FoodLogEntry[]>(`/v1/food/logs${suffix}`, { userId });
  },

  getDailySummary(userId: string, day?: string): Promise<DailySummary> {
    const suffix = day ? `?day=${encodeURIComponent(day)}` : '';
    return request<DailySummary>(`/v1/food/summary${suffix}`, { userId });
  },

  getHealthProfile(userId: string): Promise<HealthProfileOut> {
    return request<HealthProfileOut>('/v1/health/profile', { userId });
  },
};
