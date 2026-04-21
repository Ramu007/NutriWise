import React, { useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, StyleSheet, Text, View } from 'react-native';

import { Button } from '../src/components/Button';
import { Screen } from '../src/components/Screen';
import { api, type NutritionistOut } from '../src/services/api';
import { colors } from '../src/theme/colors';

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
    <Screen scroll={false}>
      <View style={styles.header}>
        <Text style={styles.heading}>Browse certified nutritionists</Text>
        <View style={styles.countryTabs}>
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

      {loading && <ActivityIndicator color={colors.accent} />}
      {error && <Text style={styles.error}>{error}</Text>}

      <FlatList
        data={items}
        keyExtractor={(n) => n.nutritionist_id}
        ListEmptyComponent={
          !loading ? (
            <Text style={styles.empty}>
              No nutritionists to show yet. Once verified nutritionists sign up, they'll appear here.
            </Text>
          ) : null
        }
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.name}>{item.name}</Text>
            <Text style={styles.meta}>
              {item.city} · ★ {item.rating_avg.toFixed(1)} ({item.rating_count})
            </Text>
            {item.specialties.length > 0 && (
              <Text style={styles.specs}>{item.specialties.join(' · ')}</Text>
            )}
            <Text style={styles.rate}>
              Virtual: {currency}
              {item.virtual_rate}
              {item.in_home_rate ? ` · In-home: ${currency}${item.in_home_rate}` : ''}
            </Text>
          </View>
        )}
        contentContainerStyle={{ paddingHorizontal: 20, gap: 12, paddingBottom: 24 }}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  header: { paddingHorizontal: 20, paddingTop: 16, gap: 12 },
  heading: { fontSize: 20, fontWeight: '700', color: colors.text },
  countryTabs: { flexDirection: 'row', gap: 8 },
  error: { color: colors.danger, paddingHorizontal: 20 },
  empty: { color: colors.muted, textAlign: 'center', marginTop: 40 },
  card: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    gap: 4,
  },
  name: { fontSize: 18, fontWeight: '700', color: colors.text },
  meta: { color: colors.muted },
  specs: { color: colors.text, marginTop: 4 },
  rate: { color: colors.accentDark, fontWeight: '600', marginTop: 4 },
});
