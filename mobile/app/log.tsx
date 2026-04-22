import * as ImagePicker from 'expo-image-picker';
import React, { useState } from 'react';
import { Alert, Image, StyleSheet, Text, View } from 'react-native';

import { Badge } from '../src/components/Badge';
import { Button } from '../src/components/Button';
import { Card } from '../src/components/Card';
import { Screen } from '../src/components/Screen';
import { api, type FoodPhotoAnalysis } from '../src/services/api';
import { currentUserId } from '../src/services/auth';
import { colors } from '../src/theme/colors';
import { radii, shadows, spacing, typography } from '../src/theme/tokens';

export default function Log() {
  const [uri, setUri] = useState<string | null>(null);
  const [result, setResult] = useState<FoodPhotoAnalysis | null>(null);
  const [loading, setLoading] = useState(false);

  async function pick() {
    const perm = await ImagePicker.requestCameraPermissionsAsync();
    if (!perm.granted) {
      Alert.alert('Camera permission denied', 'Enable camera access in Settings to log meals.');
      return;
    }
    const res = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.85,
    });
    if (!res.canceled && res.assets.length > 0) {
      setUri(res.assets[0].uri);
      setResult(null);
    }
  }

  async function pickFromLibrary() {
    const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!perm.granted) return;
    const res = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.85,
    });
    if (!res.canceled && res.assets.length > 0) {
      setUri(res.assets[0].uri);
      setResult(null);
    }
  }

  async function analyze() {
    if (!uri) return;
    setLoading(true);
    try {
      const analysis = await api.analyzeFoodPhotoByKey(currentUserId(), uri);
      setResult(analysis);
    } catch (e) {
      Alert.alert('Analysis failed', (e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Screen>
      <View style={styles.intro}>
        <Badge label="Meal log" tone="highlight" />
        <Text style={styles.title}>Snap it. Log it.</Text>
        <Text style={styles.help}>
          Take or upload a meal photo. We'll estimate items, calories, and macros in seconds.
        </Text>
      </View>

      <View style={styles.buttons}>
        <Button label="Take photo" size="lg" onPress={pick} style={{ flex: 1 }} />
        <Button
          label="From library"
          variant="secondary"
          size="lg"
          onPress={pickFromLibrary}
          style={{ flex: 1 }}
        />
      </View>

      {uri ? (
        <View style={styles.previewWrap}>
          <Image source={{ uri }} style={styles.preview} />
          {!result && (
            <View style={styles.previewOverlay}>
              <Text style={styles.previewHint}>Ready to analyze</Text>
            </View>
          )}
        </View>
      ) : (
        <Card tone="sunken" style={styles.placeholder}>
          <Text style={styles.placeholderEmoji}>🥗</Text>
          <Text style={styles.placeholderText}>
            Your photo preview will appear here. Start by taking a picture or choosing one.
          </Text>
        </Card>
      )}

      <Button
        label={loading ? 'Analyzing…' : 'Analyze photo'}
        size="lg"
        onPress={analyze}
        disabled={!uri || loading}
      />

      {result && (
        <Card style={styles.result}>
          <View style={styles.resultHead}>
            <View style={{ flex: 1 }}>
              <Text style={styles.resultEyebrow}>Estimated · {result.items.length} items</Text>
              <Text style={styles.resultKcal}>{Math.round(result.total_kcal)} kcal</Text>
            </View>
            <Badge label={result.model_used} tone="neutral" />
          </View>

          <View style={styles.macroRow}>
            <Macro label="Protein" value={`${Math.round(result.total_protein_g)}g`} tone="accent" />
            <Macro label="Carbs" value={`${Math.round(result.total_carbs_g)}g`} tone="highlight" />
            <Macro label="Fat" value={`${Math.round(result.total_fat_g)}g`} tone="neutral" />
          </View>

          <View style={styles.divider} />

          {result.items.map((it, i) => (
            <View key={`${it.name}-${i}`} style={styles.item}>
              <View style={{ flex: 1 }}>
                <Text style={styles.itemName}>{it.name}</Text>
                <Text style={styles.itemMeta}>{it.serving}</Text>
              </View>
              <Text style={styles.itemKcal}>{Math.round(it.kcal)} kcal</Text>
            </View>
          ))}

          {result.notes ? <Text style={styles.notes}>{result.notes}</Text> : null}
        </Card>
      )}
    </Screen>
  );
}

function Macro({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: 'accent' | 'highlight' | 'neutral';
}) {
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
      <Text style={[styles.macroValue, { color: fg }]}>{value}</Text>
      <Text style={[styles.macroLabel, { color: fg }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  intro: { gap: spacing.sm },
  title: { ...typography.title, color: colors.text },
  help: { ...typography.body, color: colors.textMuted },

  buttons: { flexDirection: 'row', gap: spacing.md },

  previewWrap: {
    borderRadius: radii.lg,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    ...shadows.md,
  },
  preview: { width: '100%', aspectRatio: 4 / 3 },
  previewOverlay: {
    position: 'absolute',
    bottom: spacing.md,
    left: spacing.md,
    paddingHorizontal: spacing.md,
    paddingVertical: 6,
    borderRadius: radii.pill,
    backgroundColor: 'rgba(17,20,24,0.75)',
  },
  previewHint: { color: '#FFFFFF', fontWeight: '600', fontSize: 12, letterSpacing: 0.4 },

  placeholder: {
    alignItems: 'center',
    paddingVertical: spacing['2xl'],
  },
  placeholderEmoji: { fontSize: 44 },
  placeholderText: {
    ...typography.body,
    color: colors.textMuted,
    textAlign: 'center',
    maxWidth: 280,
  },

  result: { gap: spacing.md },
  resultHead: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.sm },
  resultEyebrow: {
    ...typography.eyebrow,
    color: colors.muted,
  },
  resultKcal: {
    fontSize: 32,
    fontWeight: '800',
    color: colors.text,
    marginTop: 2,
  },

  macroRow: { flexDirection: 'row', gap: spacing.sm },
  macro: {
    flex: 1,
    borderRadius: radii.md,
    paddingVertical: spacing.md,
    alignItems: 'center',
    gap: 2,
  },
  macroValue: { fontSize: 18, fontWeight: '700' },
  macroLabel: { fontSize: 12, fontWeight: '600', letterSpacing: 0.4, textTransform: 'uppercase' },

  divider: { height: 1, backgroundColor: colors.border, marginVertical: 2 },

  item: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 6,
  },
  itemName: { fontSize: 15, color: colors.text, fontWeight: '600' },
  itemMeta: { color: colors.muted, fontSize: 13, marginTop: 2 },
  itemKcal: { fontSize: 15, color: colors.accentDark, fontWeight: '700' },

  notes: {
    color: colors.textMuted,
    fontStyle: 'italic',
    marginTop: spacing.sm,
    fontSize: 13,
  },
});
