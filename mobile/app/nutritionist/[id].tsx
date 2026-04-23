import { Stack, useLocalSearchParams, useRouter } from 'expo-router';
import React, { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { Badge } from '../../src/components/Badge';
import { Button } from '../../src/components/Button';
import { Card } from '../../src/components/Card';
import { Screen } from '../../src/components/Screen';
import {
  api,
  type BookingType,
  type NutritionistOut,
} from '../../src/services/api';
import { currentUserId } from '../../src/services/auth';
import { colors } from '../../src/theme/colors';
import { radii, spacing, typography } from '../../src/theme/tokens';

type SessionOption = {
  type: BookingType;
  label: string;
  blurb: string;
  rateKey: 'virtual_rate' | 'in_home_rate' | 'kitchen_audit_rate';
  defaultMinutes: number;
};

const SESSION_OPTIONS: SessionOption[] = [
  {
    type: 'virtual',
    label: 'Virtual session',
    blurb: '1:1 video — anywhere, anytime.',
    rateKey: 'virtual_rate',
    defaultMinutes: 45,
  },
  {
    type: 'in_home',
    label: 'In-home visit',
    blurb: 'They come to you for a full consult.',
    rateKey: 'in_home_rate',
    defaultMinutes: 60,
  },
  {
    type: 'kitchen_audit',
    label: 'Kitchen audit',
    blurb: 'Pantry + habits review on-site.',
    rateKey: 'kitchen_audit_rate',
    defaultMinutes: 90,
  },
];

const DURATIONS = [30, 45, 60, 90];

export default function NutritionistDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();

  const [n, setN] = useState<NutritionistOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedType, setSelectedType] = useState<BookingType>('virtual');
  const [duration, setDuration] = useState(45);
  const [slot, setSlot] = useState<Date>(() => defaultSlot());
  const [notes, setNotes] = useState('');
  const [booking, setBooking] = useState(false);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    setLoading(true);
    api
      .getNutritionist(id)
      .then((res) => {
        if (!cancelled) setN(res);
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  const currency = n?.country === 'IN' ? '₹' : '$';

  const availableTypes = useMemo(() => {
    if (!n) return [];
    return SESSION_OPTIONS.filter((s) => {
      if (s.type === 'virtual') return true;
      return (n[s.rateKey] ?? null) != null;
    });
  }, [n]);

  async function book() {
    if (!n) return;
    setBooking(true);
    try {
      const created = await api.createBooking(currentUserId(), {
        nutritionist_id: n.nutritionist_id,
        type: selectedType,
        starts_at: slot.toISOString(),
        duration_minutes: duration,
        notes: notes.trim(),
      });
      Alert.alert(
        'Booked!',
        `Session on ${formatSlot(new Date(created.starts_at))} · ${currency}${created.price}`,
        [{ text: 'View my sessions', onPress: () => router.replace('/bookings') }],
      );
    } catch (e) {
      const msg = (e as Error).message;
      if (msg.includes('409')) {
        Alert.alert(
          'Slot unavailable',
          'That time conflicts with an existing booking. Try another slot.',
        );
      } else {
        Alert.alert('Booking failed', msg);
      }
    } finally {
      setBooking(false);
    }
  }

  if (loading) {
    return (
      <Screen>
        <Stack.Screen options={{ title: 'Nutritionist' }} />
        <View style={styles.center}>
          <ActivityIndicator color={colors.accent} />
        </View>
      </Screen>
    );
  }

  if (error || !n) {
    return (
      <Screen>
        <Stack.Screen options={{ title: 'Nutritionist' }} />
        <View style={styles.intro}>
          <Text style={styles.title}>Couldn't load</Text>
          <Text style={styles.help}>{error ?? 'Nutritionist not found.'}</Text>
        </View>
      </Screen>
    );
  }

  const selected =
    SESSION_OPTIONS.find((s) => s.type === selectedType) ?? SESSION_OPTIONS[0];
  const rate = (n[selected.rateKey] ?? n.virtual_rate) || 0;

  return (
    <Screen>
      <Stack.Screen options={{ title: n.name }} />

      <View style={styles.intro}>
        <View style={styles.headRow}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>{initials(n.name)}</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.name}>{n.name}</Text>
            <Text style={styles.meta}>
              {n.city}, {n.country} · ★ {n.rating_avg.toFixed(1)}
              <Text style={styles.metaFaint}> ({n.rating_count})</Text>
            </Text>
          </View>
          {n.verification_status === 'approved' && <Badge label="Verified" tone="accent" />}
        </View>

        {n.bio ? <Text style={styles.bio}>{n.bio}</Text> : null}
      </View>

      {(n.credentials?.length ?? 0) > 0 && (
        <Section label="Credentials">
          <View style={styles.chipRow}>
            {n.credentials!.map((c) => (
              <Chip key={c} label={c} tone="accent" />
            ))}
          </View>
        </Section>
      )}

      {n.specialties.length > 0 && (
        <Section label="Specialties">
          <View style={styles.chipRow}>
            {n.specialties.map((s) => (
              <Chip key={s} label={s.replace(/_/g, ' ')} tone="neutral" />
            ))}
          </View>
        </Section>
      )}

      {n.languages.length > 0 && (
        <Section label="Languages">
          <Text style={styles.body}>{n.languages.join(', ')}</Text>
        </Section>
      )}

      <Card>
        <Text style={styles.cardEyebrow}>Book a session</Text>

        <View style={styles.sessionCol}>
          {availableTypes.map((opt) => {
            const selected = opt.type === selectedType;
            const optRate = n[opt.rateKey] ?? 0;
            return (
              <Pressable
                key={opt.type}
                accessibilityRole="button"
                accessibilityState={{ selected }}
                onPress={() => {
                  setSelectedType(opt.type);
                  setDuration(opt.defaultMinutes);
                }}
                style={[styles.sessionCard, selected && styles.sessionCardActive]}
              >
                <View style={{ flex: 1 }}>
                  <Text
                    style={[styles.sessionTitle, selected && styles.sessionTitleActive]}
                  >
                    {opt.label}
                  </Text>
                  <Text style={styles.sessionBlurb}>{opt.blurb}</Text>
                </View>
                <Text
                  style={[styles.sessionRate, selected && styles.sessionRateActive]}
                >
                  {currency}
                  {optRate}
                </Text>
              </Pressable>
            );
          })}
        </View>

        <Text style={styles.fieldLabel}>Duration</Text>
        <View style={styles.chipRow}>
          {DURATIONS.map((d) => {
            const active = d === duration;
            return (
              <Pressable
                key={d}
                onPress={() => setDuration(d)}
                style={[styles.durChip, active && styles.durChipActive]}
              >
                <Text style={[styles.durChipText, active && styles.durChipTextActive]}>
                  {d} min
                </Text>
              </Pressable>
            );
          })}
        </View>

        <Text style={styles.fieldLabel}>When</Text>
        <SlotPicker value={slot} onChange={setSlot} />

        <Text style={styles.fieldLabel}>Notes (optional)</Text>
        <TextInput
          value={notes}
          onChangeText={setNotes}
          multiline
          numberOfLines={3}
          placeholder="Anything they should know — goals, allergies, recent labs…"
          placeholderTextColor={colors.muted}
          style={styles.notesInput}
        />

        <View style={styles.summary}>
          <View>
            <Text style={styles.summaryEyebrow}>Estimated total</Text>
            <Text style={styles.summaryPrice}>
              {currency}
              {rate}
            </Text>
          </View>
          <Text style={styles.summaryMeta}>
            {formatSlot(slot)} · {duration} min
          </Text>
        </View>

        <Button
          label={booking ? 'Booking…' : 'Confirm booking'}
          size="lg"
          onPress={book}
          disabled={booking || n.verification_status !== 'approved'}
        />
        {n.verification_status !== 'approved' && (
          <Text style={styles.pendingNote}>
            This nutritionist is still pending verification and can't take bookings yet.
          </Text>
        )}
      </Card>
    </Screen>
  );
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionEyebrow}>{label}</Text>
      {children}
    </View>
  );
}

function Chip({ label, tone }: { label: string; tone: 'accent' | 'neutral' }) {
  const bg = tone === 'accent' ? colors.accentSoft : colors.surfaceAlt;
  const fg = tone === 'accent' ? colors.accentDark : colors.textMuted;
  return (
    <View style={[styles.chip, { backgroundColor: bg }]}>
      <Text style={[styles.chipText, { color: fg }]}>{label}</Text>
    </View>
  );
}

function SlotPicker({
  value,
  onChange,
}: {
  value: Date;
  onChange: (d: Date) => void;
}) {
  const slots = useMemo(() => nextSlots(8), []);
  return (
    <View style={styles.slotGrid}>
      {slots.map((d) => {
        const active = sameSlot(d, value);
        return (
          <Pressable
            key={d.toISOString()}
            onPress={() => onChange(d)}
            style={[styles.slotBtn, active && styles.slotBtnActive]}
          >
            <Text style={[styles.slotDay, active && styles.slotDayActive]}>
              {d.toLocaleDateString(undefined, { weekday: 'short' })}
            </Text>
            <Text style={[styles.slotTime, active && styles.slotTimeActive]}>
              {d.toLocaleTimeString(undefined, {
                hour: 'numeric',
                minute: '2-digit',
              })}
            </Text>
            <Text style={[styles.slotDate, active && styles.slotDateActive]}>
              {d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

function defaultSlot(): Date {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  d.setHours(10, 0, 0, 0);
  return d;
}

function nextSlots(count: number): Date[] {
  const base = new Date();
  base.setMinutes(0, 0, 0);
  const startHour = 9;
  const hours = [9, 11, 14, 16];
  const out: Date[] = [];
  let dayOffset = 1;
  while (out.length < count) {
    for (const h of hours) {
      if (out.length >= count) break;
      const d = new Date(base);
      d.setDate(base.getDate() + dayOffset);
      d.setHours(h, 0, 0, 0);
      if (h >= startHour) out.push(d);
    }
    dayOffset += 1;
  }
  return out;
}

function sameSlot(a: Date, b: Date): boolean {
  return a.getTime() === b.getTime();
}

function formatSlot(d: Date): string {
  return d.toLocaleString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? '')
    .join('');
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingVertical: spacing['2xl'] },

  intro: { gap: spacing.md },
  headRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  avatar: {
    width: 56,
    height: 56,
    borderRadius: radii.pill,
    backgroundColor: colors.accentSoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    color: colors.accentDark,
    fontWeight: '700',
    fontSize: 18,
    letterSpacing: 0.5,
  },
  name: { ...typography.title, color: colors.text },
  meta: { ...typography.caption, color: colors.textMuted, marginTop: 2 },
  metaFaint: { color: colors.muted },
  title: { ...typography.title, color: colors.text },
  help: { ...typography.body, color: colors.textMuted },
  body: { ...typography.body, color: colors.text },
  bio: { ...typography.body, color: colors.textMuted },

  section: { gap: spacing.sm },
  sectionEyebrow: { ...typography.eyebrow, color: colors.muted },

  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  chip: {
    paddingHorizontal: spacing.md,
    paddingVertical: 6,
    borderRadius: radii.pill,
  },
  chipText: { fontSize: 12, fontWeight: '700', letterSpacing: 0.3 },

  cardEyebrow: { ...typography.eyebrow, color: colors.muted },

  sessionCol: { gap: spacing.sm },
  sessionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    borderRadius: radii.md,
  },
  sessionCardActive: {
    borderColor: colors.accentDark,
    backgroundColor: colors.accentSoft,
  },
  sessionTitle: { fontSize: 15, fontWeight: '700', color: colors.text },
  sessionTitleActive: { color: colors.accentDark },
  sessionBlurb: { ...typography.caption, color: colors.textMuted, marginTop: 2 },
  sessionRate: { fontSize: 18, fontWeight: '800', color: colors.text },
  sessionRateActive: { color: colors.accentDark },

  fieldLabel: {
    ...typography.eyebrow,
    color: colors.muted,
    marginTop: spacing.sm,
  },

  durChip: {
    paddingHorizontal: spacing.md,
    paddingVertical: 8,
    borderRadius: radii.pill,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  durChipActive: {
    backgroundColor: colors.accent,
    borderColor: colors.accentDark,
  },
  durChipText: { fontSize: 13, fontWeight: '600', color: colors.text },
  durChipTextActive: { color: '#FFFFFF' },

  slotGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  slotBtn: {
    width: 88,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    borderRadius: radii.md,
    alignItems: 'center',
  },
  slotBtnActive: {
    backgroundColor: colors.accent,
    borderColor: colors.accentDark,
  },
  slotDay: { fontSize: 11, fontWeight: '700', color: colors.muted, letterSpacing: 0.5 },
  slotDayActive: { color: '#E8FCEF' },
  slotTime: { fontSize: 16, fontWeight: '800', color: colors.text, marginVertical: 2 },
  slotTimeActive: { color: '#FFFFFF' },
  slotDate: { fontSize: 11, color: colors.textMuted },
  slotDateActive: { color: '#E8FCEF' },

  notesInput: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.md,
    padding: spacing.md,
    minHeight: 80,
    color: colors.text,
    backgroundColor: colors.surface,
    ...(Platform.OS === 'web' ? { outlineStyle: 'none' as unknown as 'none' } : null),
    textAlignVertical: 'top',
  },

  summary: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  summaryEyebrow: { ...typography.eyebrow, color: colors.muted },
  summaryPrice: { fontSize: 24, fontWeight: '800', color: colors.text },
  summaryMeta: { ...typography.caption, color: colors.textMuted },

  pendingNote: {
    ...typography.caption,
    color: colors.textMuted,
    textAlign: 'center',
  },
});
