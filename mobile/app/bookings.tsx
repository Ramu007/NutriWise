import { Link, useFocusEffect } from 'expo-router';
import React, { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { Badge } from '../src/components/Badge';
import { Button } from '../src/components/Button';
import { Card } from '../src/components/Card';
import { Screen } from '../src/components/Screen';
import { api, type BookingOut, type BookingStatus } from '../src/services/api';
import { currentUserId } from '../src/services/auth';
import { colors } from '../src/theme/colors';
import { radii, spacing, typography } from '../src/theme/tokens';

type State =
  | { kind: 'loading' }
  | { kind: 'error'; message: string }
  | { kind: 'ready'; upcoming: BookingOut[]; past: BookingOut[] };

const TYPE_LABELS: Record<BookingOut['type'], string> = {
  virtual: 'Virtual',
  in_home: 'In-home',
  kitchen_audit: 'Kitchen audit',
};

export default function Bookings() {
  const [state, setState] = useState<State>({ kind: 'loading' });
  const [cancelling, setCancelling] = useState<string | null>(null);

  const load = useCallback(async () => {
    setState({ kind: 'loading' });
    try {
      const all = await api.listMyBookings(currentUserId());
      const now = Date.now();
      const upcoming: BookingOut[] = [];
      const past: BookingOut[] = [];
      for (const b of all) {
        const isDone =
          b.status === 'cancelled' ||
          b.status === 'completed' ||
          new Date(b.starts_at).getTime() < now;
        (isDone ? past : upcoming).push(b);
      }
      upcoming.sort(
        (a, b) => new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime(),
      );
      past.sort(
        (a, b) => new Date(b.starts_at).getTime() - new Date(a.starts_at).getTime(),
      );
      setState({ kind: 'ready', upcoming, past });
    } catch (e) {
      setState({ kind: 'error', message: (e as Error).message });
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      void load();
    }, [load]),
  );

  async function doCancel(b: BookingOut) {
    setCancelling(b.booking_id);
    try {
      await api.cancelBooking(currentUserId(), b.booking_id);
      await load();
    } catch (e) {
      Alert.alert('Could not cancel', (e as Error).message);
    } finally {
      setCancelling(null);
    }
  }

  function confirmCancel(b: BookingOut) {
    Alert.alert(
      'Cancel this session?',
      `${TYPE_LABELS[b.type]} on ${formatWhen(b.starts_at)}`,
      [
        { text: 'Keep it', style: 'cancel' },
        { text: 'Cancel session', style: 'destructive', onPress: () => void doCancel(b) },
      ],
    );
  }

  if (state.kind === 'loading') {
    return (
      <Screen>
        <View style={styles.center}>
          <ActivityIndicator color={colors.accent} />
        </View>
      </Screen>
    );
  }

  if (state.kind === 'error') {
    return (
      <Screen>
        <View style={styles.intro}>
          <Badge label="My sessions" tone="accent" />
          <Text style={styles.title}>Couldn't load bookings</Text>
          <Text style={styles.help}>{state.message}</Text>
        </View>
        <Button label="Retry" size="lg" onPress={load} />
      </Screen>
    );
  }

  const { upcoming, past } = state;

  return (
    <Screen>
      <View style={styles.intro}>
        <Badge label="My sessions" tone="accent" />
        <Text style={styles.title}>
          {upcoming.length > 0
            ? `${upcoming.length} upcoming`
            : 'No sessions coming up'}
        </Text>
        <Text style={styles.help}>
          {upcoming.length > 0
            ? 'Review, reschedule by cancelling and rebooking, or add a new session.'
            : 'Find a nutritionist and book a virtual or in-home consult.'}
        </Text>
      </View>

      {upcoming.length === 0 && (
        <Link href="/find" asChild>
          <Button label="Find a nutritionist" size="lg" onPress={() => {}} />
        </Link>
      )}

      {upcoming.length > 0 && (
        <View style={styles.list}>
          {upcoming.map((b) => (
            <BookingCard
              key={b.booking_id}
              booking={b}
              onCancel={() => confirmCancel(b)}
              cancelling={cancelling === b.booking_id}
              tone="upcoming"
            />
          ))}
        </View>
      )}

      {past.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionEyebrow}>Past & cancelled</Text>
          <View style={styles.list}>
            {past.map((b) => (
              <BookingCard
                key={b.booking_id}
                booking={b}
                onCancel={() => confirmCancel(b)}
                cancelling={false}
                tone="past"
              />
            ))}
          </View>
        </View>
      )}
    </Screen>
  );
}

function BookingCard({
  booking,
  onCancel,
  cancelling,
  tone,
}: {
  booking: BookingOut;
  onCancel: () => void;
  cancelling: boolean;
  tone: 'upcoming' | 'past';
}) {
  const canCancel =
    tone === 'upcoming' &&
    booking.status !== 'cancelled' &&
    booking.status !== 'completed';
  const faded = tone === 'past';
  return (
    <Card style={faded ? styles.cardFaded : undefined}>
      <View style={styles.cardHead}>
        <View style={{ flex: 1 }}>
          <Text style={[styles.when, faded && styles.faded]}>{formatWhen(booking.starts_at)}</Text>
          <Text style={[styles.meta, faded && styles.faded]}>
            {TYPE_LABELS[booking.type]} · {booking.duration_minutes} min
          </Text>
        </View>
        <StatusBadge status={booking.status} />
      </View>

      <View style={styles.priceRow}>
        <Text style={[styles.priceLabel, faded && styles.faded]}>Total</Text>
        <Text style={[styles.price, faded && styles.faded]}>
          {symbol(booking.currency)}
          {booking.price}
        </Text>
      </View>

      {booking.notes ? (
        <Text style={[styles.notes, faded && styles.faded]}>"{booking.notes}"</Text>
      ) : null}

      {canCancel && (
        <Pressable
          accessibilityRole="button"
          onPress={onCancel}
          disabled={cancelling}
          style={({ pressed }) => [
            styles.cancelBtn,
            pressed && styles.cancelBtnPressed,
          ]}
        >
          <Text style={styles.cancelBtnText}>
            {cancelling ? 'Cancelling…' : 'Cancel session'}
          </Text>
        </Pressable>
      )}
    </Card>
  );
}

function StatusBadge({ status }: { status: BookingStatus }) {
  if (status === 'confirmed') return <Badge label="Confirmed" tone="accent" />;
  if (status === 'pending') return <Badge label="Pending" tone="highlight" />;
  if (status === 'completed') return <Badge label="Completed" tone="neutral" />;
  return <Badge label="Cancelled" tone="danger" />;
}

function formatWhen(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

function symbol(currency: string): string {
  if (currency === 'INR') return '₹';
  if (currency === 'USD') return '$';
  return `${currency} `;
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingVertical: spacing['2xl'] },
  intro: { gap: spacing.sm },
  title: { ...typography.title, color: colors.text },
  help: { ...typography.body, color: colors.textMuted },

  list: { gap: spacing.md },
  section: { gap: spacing.md },
  sectionEyebrow: { ...typography.eyebrow, color: colors.muted },

  cardFaded: { opacity: 0.7 },
  faded: { color: colors.textMuted },

  cardHead: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.sm,
  },
  when: { ...typography.heading, color: colors.text },
  meta: { ...typography.caption, color: colors.textMuted, marginTop: 2 },

  priceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  priceLabel: { ...typography.eyebrow, color: colors.muted },
  price: { fontSize: 18, fontWeight: '800', color: colors.text },
  notes: { ...typography.caption, color: colors.textMuted, fontStyle: 'italic' },

  cancelBtn: {
    alignSelf: 'flex-start',
    paddingVertical: 8,
    paddingHorizontal: spacing.md,
    borderRadius: radii.pill,
    borderWidth: 1,
    borderColor: colors.danger,
  },
  cancelBtnPressed: { backgroundColor: colors.dangerSoft },
  cancelBtnText: { color: colors.danger, fontWeight: '700', fontSize: 13 },
});
