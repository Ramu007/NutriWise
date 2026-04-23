import { Link, useFocusEffect } from 'expo-router';
import React, { useCallback, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { Badge } from '../src/components/Badge';
import { Button } from '../src/components/Button';
import { Card } from '../src/components/Card';
import { Screen } from '../src/components/Screen';
import {
  api,
  type DailySummary,
  type FoodLogEntry,
  type MealSlot,
} from '../src/services/api';
import { currentUserId } from '../src/services/auth';
import { colors } from '../src/theme/colors';
import { radii, spacing, typography } from '../src/theme/tokens';

const SLOT_ORDER: MealSlot[] = ['breakfast', 'lunch', 'dinner', 'snack'];
const SLOT_EMOJI: Record<MealSlot, string> = {
  breakfast: '🥣',
  lunch: '🥗',
  dinner: '🍲',
  snack: '🍎',
};

type State =
  | { kind: 'loading' }
  | { kind: 'no_profile' }
  | { kind: 'error'; message: string }
  | { kind: 'ready'; summary: DailySummary; logs: FoodLogEntry[] };

export default function Today() {
  const [state, setState] = useState<State>({ kind: 'loading' });

  const load = useCallback(async () => {
    setState({ kind: 'loading' });
    try {
      const uid = currentUserId();
      const [summary, logs] = await Promise.all([
        api.getDailySummary(uid),
        api.listFoodLogs(uid),
      ]);
      setState({ kind: 'ready', summary, logs });
    } catch (e) {
      const msg = (e as Error).message;
      if (msg.includes('409')) {
        setState({ kind: 'no_profile' });
      } else {
        setState({ kind: 'error', message: msg });
      }
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      void load();
    }, [load]),
  );

  if (state.kind === 'loading') {
    return (
      <Screen>
        <View style={styles.center}>
          <ActivityIndicator color={colors.accent} />
        </View>
      </Screen>
    );
  }

  if (state.kind === 'no_profile') {
    return (
      <Screen>
        <View style={styles.intro}>
          <Badge label="Today" tone="highlight" />
          <Text style={styles.title}>Set up your target first</Text>
          <Text style={styles.help}>
            We need your health profile so we can roll meals up against a daily calorie target.
          </Text>
        </View>
        <Link href="/profile" asChild>
          <Button label="Go to profile" size="lg" onPress={() => {}} />
        </Link>
      </Screen>
    );
  }

  if (state.kind === 'error') {
    return (
      <Screen>
        <View style={styles.intro}>
          <Badge label="Today" tone="highlight" />
          <Text style={styles.title}>Couldn't load today</Text>
          <Text style={styles.help}>{state.message}</Text>
        </View>
        <Button label="Retry" size="lg" onPress={load} />
      </Screen>
    );
  }

  const { summary, logs } = state;
  const pct = summary.target_kcal > 0 ? summary.total_kcal / summary.target_kcal : 0;
  const grouped = groupByMeal(logs);

  return (
    <Screen>
      <View style={styles.intro}>
        <Badge label="Today" tone="highlight" />
        <Text style={styles.title}>{prettyDate(summary.day)}</Text>
        <Text style={styles.help}>
          {summary.entry_count === 0
            ? 'Nothing logged yet. Snap a meal to get started.'
            : `${summary.entry_count} meal${summary.entry_count === 1 ? '' : 's'} logged so far.`}
        </Text>
      </View>

      <Card>
        <View style={styles.kcalHead}>
          <View style={{ flex: 1 }}>
            <Text style={styles.kcalEyebrow}>Calories</Text>
            <Text style={styles.kcalBig}>
              {Math.round(summary.total_kcal)}
              <Text style={styles.kcalTarget}> / {Math.round(summary.target_kcal)}</Text>
            </Text>
          </View>
          <StatusPill status={summary.status} />
        </View>

        <ProgressBar pct={pct} status={summary.status} />

        <Text style={styles.remaining}>
          {summary.remaining_kcal >= 0
            ? `${Math.round(summary.remaining_kcal)} kcal remaining`
            : `${Math.round(Math.abs(summary.remaining_kcal))} kcal over target`}
        </Text>

        <View style={styles.macroRow}>
          <Macro
            label="Protein"
            grams={summary.total_protein_g}
            kcalPerG={4}
            totalKcal={summary.total_kcal}
            tone="accent"
          />
          <Macro
            label="Carbs"
            grams={summary.total_carbs_g}
            kcalPerG={4}
            totalKcal={summary.total_kcal}
            tone="highlight"
          />
          <Macro
            label="Fat"
            grams={summary.total_fat_g}
            kcalPerG={9}
            totalKcal={summary.total_kcal}
            tone="neutral"
          />
        </View>
      </Card>

      <View style={styles.mealList}>
        {SLOT_ORDER.map((slot) => {
          const entries = grouped[slot] ?? [];
          return <MealSection key={slot} slot={slot} entries={entries} />;
        })}
      </View>

      <Link href="/log" asChild>
        <Button label="Log another meal" size="lg" onPress={() => {}} />
      </Link>
    </Screen>
  );
}

function MealSection({ slot, entries }: { slot: MealSlot; entries: FoodLogEntry[] }) {
  const kcal = entries.reduce(
    (acc, e) => acc + e.items.reduce((a, i) => a + i.kcal, 0),
    0,
  );
  return (
    <Card tone={entries.length ? 'default' : 'sunken'}>
      <View style={styles.mealHead}>
        <Text style={styles.mealEmoji}>{SLOT_EMOJI[slot]}</Text>
        <View style={{ flex: 1 }}>
          <Text style={styles.mealSlot}>{capitalize(slot)}</Text>
          <Text style={styles.mealMeta}>
            {entries.length === 0
              ? 'Nothing logged'
              : `${entries.length} entr${entries.length === 1 ? 'y' : 'ies'} · ${Math.round(kcal)} kcal`}
          </Text>
        </View>
      </View>
      {entries.length > 0 && (
        <View style={styles.mealItems}>
          {entries.flatMap((e) =>
            e.items.map((it, i) => (
              <View key={`${e.entry_id}-${i}`} style={styles.item}>
                <Text style={styles.itemName}>{it.name}</Text>
                <Text style={styles.itemKcal}>{Math.round(it.kcal)} kcal</Text>
              </View>
            )),
          )}
        </View>
      )}
    </Card>
  );
}

function StatusPill({ status }: { status: DailySummary['status'] }) {
  if (status === 'on_track') return <Badge label="On track" tone="accent" />;
  if (status === 'over') return <Badge label="Over" tone="danger" />;
  return <Badge label="Under" tone="neutral" />;
}

function ProgressBar({ pct, status }: { pct: number; status: DailySummary['status'] }) {
  const clamped = Math.max(0, Math.min(1, pct));
  const color =
    status === 'over' ? colors.danger : status === 'on_track' ? colors.accent : colors.highlight;
  return (
    <View style={styles.barTrack}>
      <View style={[styles.barFill, { width: `${clamped * 100}%`, backgroundColor: color }]} />
    </View>
  );
}

function Macro({
  label,
  grams,
  kcalPerG,
  totalKcal,
  tone,
}: {
  label: string;
  grams: number;
  kcalPerG: number;
  totalKcal: number;
  tone: 'accent' | 'highlight' | 'neutral';
}) {
  const share = totalKcal > 0 ? Math.round(((grams * kcalPerG) / totalKcal) * 100) : 0;
  const bg =
    tone === 'accent'
      ? colors.accentSoft
      : tone === 'highlight'
        ? colors.highlightSoft
        : colors.surfaceAlt;
  const fg =
    tone === 'accent'
      ? colors.accentDark
      : tone === 'highlight'
        ? colors.highlight
        : colors.textMuted;
  return (
    <View style={[styles.macro, { backgroundColor: bg }]}>
      <Text style={[styles.macroValue, { color: fg }]}>{Math.round(grams)}g</Text>
      <Text style={[styles.macroLabel, { color: fg }]}>
        {label} · {share}%
      </Text>
    </View>
  );
}

function groupByMeal(logs: FoodLogEntry[]): Record<MealSlot, FoodLogEntry[]> {
  const acc: Record<MealSlot, FoodLogEntry[]> = {
    breakfast: [],
    lunch: [],
    dinner: [],
    snack: [],
  };
  for (const l of logs) acc[l.meal].push(l);
  return acc;
}

function capitalize(s: string): string {
  return s.length ? s[0].toUpperCase() + s.slice(1) : s;
}

function prettyDate(iso: string): string {
  const d = new Date(`${iso}T00:00:00`);
  return d.toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  });
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingVertical: spacing['2xl'] },
  intro: { gap: spacing.sm },
  title: { ...typography.title, color: colors.text },
  help: { ...typography.body, color: colors.textMuted },

  kcalHead: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.sm },
  kcalEyebrow: { ...typography.eyebrow, color: colors.muted },
  kcalBig: {
    fontSize: 32,
    fontWeight: '800',
    color: colors.text,
    marginTop: 2,
  },
  kcalTarget: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.muted,
  },

  barTrack: {
    height: 10,
    borderRadius: radii.pill,
    backgroundColor: colors.surfaceAlt,
    overflow: 'hidden',
    marginTop: spacing.xs,
  },
  barFill: {
    height: '100%',
    borderRadius: radii.pill,
  },
  remaining: {
    ...typography.caption,
    color: colors.textMuted,
  },

  macroRow: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.sm },
  macro: {
    flex: 1,
    borderRadius: radii.md,
    paddingVertical: spacing.md,
    alignItems: 'center',
    gap: 2,
  },
  macroValue: { fontSize: 18, fontWeight: '700' },
  macroLabel: { fontSize: 11, fontWeight: '600', letterSpacing: 0.3, textTransform: 'uppercase' },

  mealList: { gap: spacing.md },
  mealHead: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  mealEmoji: { fontSize: 26 },
  mealSlot: { ...typography.heading, color: colors.text },
  mealMeta: { ...typography.caption, color: colors.muted },
  mealItems: { gap: spacing.xs, marginTop: spacing.xs },
  item: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  itemName: { color: colors.text, fontSize: 14, flex: 1 },
  itemKcal: { color: colors.accentDark, fontSize: 14, fontWeight: '700' },
});
