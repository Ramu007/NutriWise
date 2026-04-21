import * as ImagePicker from 'expo-image-picker';
import React, { useState } from 'react';
import { Alert, Image, StyleSheet, Text, View } from 'react-native';

import { Button } from '../src/components/Button';
import { Screen } from '../src/components/Screen';
import { api } from '../src/services/api';
import { colors } from '../src/theme/colors';

type Analysis = {
  items: { name: string; kcal: number; serving: string }[];
  total_kcal: number;
  notes?: string;
};

export default function Log() {
  const [uri, setUri] = useState<string | null>(null);
  const [result, setResult] = useState<Analysis | null>(null);
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
      const analysis = (await api.analyzeFoodPhoto('demo-user', uri)) as Analysis;
      setResult(analysis);
    } catch (e) {
      Alert.alert('Analysis failed', (e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Screen>
      <Text style={styles.help}>
        Snap or pick a meal photo. We'll estimate the items, calories, and macros, and you can log
        them to your day.
      </Text>

      <View style={styles.buttons}>
        <Button label="Take a photo" onPress={pick} style={{ flex: 1 }} />
        <Button label="Choose from library" variant="secondary" onPress={pickFromLibrary} style={{ flex: 1 }} />
      </View>

      {uri && (
        <View style={styles.previewWrap}>
          <Image source={{ uri }} style={styles.preview} />
        </View>
      )}

      <Button label={loading ? 'Analyzing…' : 'Analyze photo'} onPress={analyze} disabled={!uri || loading} />

      {result && (
        <View style={styles.result}>
          <Text style={styles.resultTitle}>
            {result.items.length} items · {result.total_kcal} kcal
          </Text>
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
        </View>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  help: { color: colors.muted, marginBottom: 4 },
  buttons: { flexDirection: 'row', gap: 8 },
  previewWrap: {
    borderRadius: 12,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: colors.border,
  },
  preview: { width: '100%', aspectRatio: 4 / 3 },
  result: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    gap: 10,
  },
  resultTitle: { fontSize: 18, fontWeight: '700', color: colors.text },
  item: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  itemName: { fontSize: 16, color: colors.text, fontWeight: '600' },
  itemMeta: { color: colors.muted, fontSize: 13 },
  itemKcal: { fontSize: 16, color: colors.accentDark, fontWeight: '700' },
  notes: { color: colors.muted, fontStyle: 'italic', marginTop: 8 },
});
