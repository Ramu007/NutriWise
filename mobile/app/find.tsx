import React, { useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, StyleSheet, Text, View } from 'react-native';

import { Badge } from '../src/components/Badge';
import { Button } from '../src/components/Button';
import { Screen } from '../src/components/Screen';
import { api, type NutritionistOut } from '../src/services/api';
import { colors } from '../src/theme/colors';
import { radii, shadows, spacing, typography } from '../src/theme/tokens';

export default function Find() {
  const [country, setCountry] = useState<'US' | 'IN'>('US');
  const [items, setItems] = useState<NutritionistOut[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api
      .searchNutritionists({ country })
      .then((res) => {
        if (!cancelled) setItems(res);
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
  }, [country]);

  const currency = country === 'IN' ? '₹' : '$';

  return (
    <Screen scroll={false} edgeToEdge>
      <View style={styles.header}>
        <Badge label="Certified nutritionists" tone="accent" />
        <Text style={styles.heading}>Find your match</Text>
        <Text style={styles.sub}>
          Browse verified experts — filter by country, book virtual or in-home sessions.
        </Text>

        <View style={styles.tabs}>
          <Button
            label="United States"
            variant={country === 'US' ? 'primary' : 'secondary'}
            onPress={() => setCountry('US')}
            style={{ flex: 1 }}
          />
          <Button
            label="India"
            variant={country === 'IN' ? 'primary' : 'secondary'}
            onPress={() => setCountry('IN')}
            style={{ flex: 1 }}
          />
        </View>
      </View>

      {loading && (
        <View style={styles.center}>
          <ActivityIndicator color={colors.accent} />
        </View>
      )}
      {error && (
        <View style={styles.errorWrap}>
          <Text style={styles.error}>{error}</Text>
        </View>
      )}

      <FlatList
        data={items}
        keyExtractor={(n) => n.nutritionist_id}
        ListEmptyComponent={
          !loading && !error ? (
            <View style={styles.emptyCard}>
              <Text style={styles.emptyEmoji}>🧑‍⚕️</Text>
              <Text style={styles.emptyTitle}>No nutritionists yet</Text>
              <Text style={styles.empty}>
                Verified nutritionists will appear here as they join. Check back soon.
              </Text>
            </View>
          ) : null
        }
        renderItem={({ item }) => (
          <View style={styles.card}>
            <View style={styles.cardHead}>
              <View style={styles.avatar}>
                <Text style={styles.avatarText}>{initials(item.name)}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.name}>{item.name}</Text>
                <Text style={styles.meta}>
                  {item.city}, {item.country} · ★ {item.rating_avg.toFixed(1)}
                  <Text style={styles.metaFaint}> ({item.rating_count})</Text>
                </Text>
              </View>
              {item.verification_status === 'approved' && (
                <Badge label="Verified" tone="accent" />
              )}
            </View>

            {item.specialties.length > 0 && (
              <View style={styles.chipRow}>
                {item.specialties.slice(0, 4).map((s) => (
                  <View key={s} style={styles.chip}>
                    <Text style={styles.chipText}>{s}</Text>
                  </View>
                ))}
              </View>
            )}

            <View style={styles.rateRow}>
              <View style={styles.rateCell}>
                <Text style={styles.rateLabel}>Virtual</Text>
                <Text style={styles.rateValue}>
                  {currency}
                  {item.virtual_rate}
                </Text>
              </View>
              {item.in_home_rate != null && (
                <View style={styles.rateCell}>
                  <Text style={styles.rateLabel}>In-home</Text>
                  <Text style={styles.rateValue}>
                    {currency}
                    {item.in_home_rate}
                  </Text>
                </View>
              )}
              {item.languages.length > 0 && (
                <View style={[styles.rateCell, { alignItems: 'flex-end' }]}>
                  <Text style={styles.rateLabel}>Speaks</Text>
                  <Text style={styles.rateValueMuted}>
                    {item.languages.slice(0, 2).join(', ')}
                  </Text>
                </View>
              )}
            </View>
          </View>
        )}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
      />
    </Screen>
  );
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
  header: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.lg,
    gap: spacing.sm,
  },
  heading: { ...typography.title, color: colors.text },
  sub: { ...typography.body, color: colors.textMuted },
  tabs: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.sm },

  center: { paddingVertical: spacing['2xl'], alignItems: 'center' },
  errorWrap: { paddingHorizontal: spacing.lg, paddingVertical: spacing.md },
  error: { color: colors.danger },

  listContent: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.lg,
    paddingBottom: spacing['2xl'],
    gap: spacing.md,
  },

  emptyCard: {
    alignItems: 'center',
    gap: spacing.sm,
    padding: spacing['2xl'],
    backgroundColor: colors.surfaceSunken,
    borderRadius: radii.lg,
    borderWidth: 1,
    borderColor: colors.border,
    marginTop: spacing.md,
  },
  emptyEmoji: { fontSize: 44 },
  emptyTitle: { ...typography.heading, color: colors.text },
  empty: {
    color: colors.textMuted,
    textAlign: 'center',
    maxWidth: 280,
  },

  card: {
    backgroundColor: colors.surface,
    borderRadius: radii.lg,
    padding: spacing.lg,
    gap: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    ...shadows.sm,
  },
  cardHead: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  avatar: {
    width: 46,
    height: 46,
    borderRadius: radii.pill,
    backgroundColor: colors.accentSoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    color: colors.accentDark,
    fontWeight: '700',
    fontSize: 16,
    letterSpacing: 0.5,
  },
  name: { fontSize: 17, fontWeight: '700', color: colors.text },
  meta: { color: colors.textMuted, fontSize: 13, marginTop: 2 },
  metaFaint: { color: colors.muted },

  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  chip: {
    backgroundColor: colors.surfaceAlt,
    paddingHorizontal: spacing.md,
    paddingVertical: 4,
    borderRadius: radii.pill,
  },
  chipText: { fontSize: 12, color: colors.textMuted, fontWeight: '600' },

  rateRow: {
    flexDirection: 'row',
    gap: spacing.lg,
    paddingTop: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  rateCell: { flex: 1 },
  rateLabel: {
    ...typography.eyebrow,
    color: colors.muted,
  },
  rateValue: { fontSize: 17, fontWeight: '700', color: colors.accentDark, marginTop: 2 },
  rateValueMuted: { fontSize: 14, fontWeight: '600', color: colors.text, marginTop: 2 },
});
