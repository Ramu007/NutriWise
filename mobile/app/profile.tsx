import React, { useState } from 'react';
import { Alert, StyleSheet, Text, TextInput, View } from 'react-native';

import { Button } from '../src/components/Button';
import { Screen } from '../src/components/Screen';
import { api, type HealthProfileOut } from '../src/services/api';
import { currentUserId } from '../src/services/auth';
import { colors } from '../src/theme/colors';

type Form = {
  age: string;
  heightCm: string;
  weightKg: string;
  sex: 'male' | 'female';
  goal: 'lose' | 'maintain' | 'gain';
  country: 'US' | 'IN';
};

export default function Profile() {
  const [form, setForm] = useState<Form>({
    age: '30',
    heightCm: '175',
    weightKg: '75',
    sex: 'male',
    goal: 'maintain',
    country: 'US',
  });
  const [result, setResult] = useState<HealthProfileOut | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit() {
    setLoading(true);
    try {
      const out = await api.upsertHealthProfile(currentUserId(), {
        sex: form.sex,
        age_years: Number(form.age),
        height_cm: Number(form.heightCm),
        weight_kg: Number(form.weightKg),
        goal: form.goal,
        country: form.country,
      });
      setResult(out);
    } catch (e) {
      Alert.alert('Could not save profile', (e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Screen>
      <Text style={styles.help}>
        We use your stats with the Mifflin-St Jeor equation to estimate your daily calorie target.
      </Text>

      <Field label="Age (years)" value={form.age} onChange={(v) => setForm({ ...form, age: v })} />
      <Field label="Height (cm)" value={form.heightCm} onChange={(v) => setForm({ ...form, heightCm: v })} />
      <Field label="Weight (kg)" value={form.weightKg} onChange={(v) => setForm({ ...form, weightKg: v })} />

      <Segmented
        label="Sex"
        value={form.sex}
        options={[
          { value: 'male', label: 'Male' },
          { value: 'female', label: 'Female' },
        ]}
        onChange={(v) => setForm({ ...form, sex: v })}
      />

      <Segmented
        label="Goal"
        value={form.goal}
        options={[
          { value: 'lose', label: 'Lose' },
          { value: 'maintain', label: 'Maintain' },
          { value: 'gain', label: 'Gain' },
        ]}
        onChange={(v) => setForm({ ...form, goal: v })}
      />

      <Segmented
        label="Country"
        value={form.country}
        options={[
          { value: 'US', label: 'United States' },
          { value: 'IN', label: 'India' },
        ]}
        onChange={(v) => setForm({ ...form, country: v })}
      />

      <Button label={loading ? 'Saving…' : 'Calculate'} onPress={submit} disabled={loading} />

      {result && (
        <View style={styles.result}>
          <Text style={styles.resultTitle}>Your targets</Text>
          <Row k="BMI" v={`${result.bmi} (${result.bmi_category})`} />
          <Row k="BMR" v={`${result.bmr_kcal} kcal`} />
          <Row k="TDEE" v={`${result.tdee_kcal} kcal`} />
          <Row k="Daily target" v={`${result.daily_target_kcal} kcal`} />
        </View>
      )}
    </Screen>
  );
}

function Field({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        style={styles.input}
        value={value}
        onChangeText={onChange}
        keyboardType="numeric"
        inputMode="numeric"
      />
    </View>
  );
}

function Segmented<T extends string>({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (v: T) => void;
}) {
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      <View style={styles.segmented}>
        {options.map((o) => (
          <Button
            key={o.value}
            label={o.label}
            variant={o.value === value ? 'primary' : 'secondary'}
            onPress={() => onChange(o.value)}
            style={{ flex: 1 }}
          />
        ))}
      </View>
    </View>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <View style={styles.row}>
      <Text style={styles.rowK}>{k}</Text>
      <Text style={styles.rowV}>{v}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  help: { color: colors.muted, marginBottom: 4 },
  field: { gap: 6 },
  label: { fontSize: 14, fontWeight: '600', color: colors.text },
  input: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
    backgroundColor: colors.surface,
    color: colors.text,
  },
  segmented: { flexDirection: 'row', gap: 8 },
  result: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    gap: 6,
    marginTop: 12,
  },
  resultTitle: { fontSize: 18, fontWeight: '700', color: colors.text, marginBottom: 4 },
  row: { flexDirection: 'row', justifyContent: 'space-between' },
  rowK: { color: colors.muted },
  rowV: { color: colors.text, fontWeight: '600' },
});
