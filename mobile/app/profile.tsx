import React, { useState } from 'react';
import { Alert, StyleSheet, Text, TextInput, View } from 'react-native';

import { Badge } from '../src/components/Badge';
import { Button } from '../src/components/Button';
import { Card } from '../src/components/Card';
import { Screen } from '../src/components/Screen';
import { api, type HealthProfileOut } from '../src/services/api';
import { currentUserId } from '../src/services/auth';
import { colors } from '../src/theme/colors';
import { radii, spacing, typography } from '../src/theme/tokens';

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
      <View style={styles.intro}>
        <Badge label="Health profile" tone="accent" />
        <Text style={styles.title}>Tell us about you</Text>
        <Text style={styles.help}>
          We use the Mifflin–St Jeor equation to estimate your BMR and daily calorie target.
        </Text>
      </View>

      <Card>
        <View style={styles.row}>
          <Field
            label="Age"
            unit="yrs"
            value={form.age}
            onChange={(v) => setForm({ ...form, age: v })}
            style={{ flex: 1 }}
          />
          <Field
            label="Height"
            unit="cm"
            value={form.heightCm}
            onChange={(v) => setForm({ ...form, heightCm: v })}
            style={{ flex: 1 }}
          />
          <Field
            label="Weight"
            unit="kg"
            value={form.weightKg}
            onChange={(v) => setForm({ ...form, weightKg: v })}
            style={{ flex: 1 }}
          />
        </View>

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

        <Button
          label={loading ? 'Calculating…' : 'Calculate my targets'}
          size="lg"
          onPress={submit}
          disabled={loading}
        />
      </Card>

      {result && (
        <Card tone="accent" style={styles.result}>
          <View style={styles.resultHeader}>
            <Badge label={result.bmi_category} tone="highlight" />
            <Text style={styles.resultTitle}>Your daily targets</Text>
          </View>

          <View style={styles.statGrid}>
            <Stat k="BMI" v={`${result.bmi}`} sub={result.bmi_category} />
            <Stat k="BMR" v={`${result.bmr_kcal}`} sub="kcal / day" />
            <Stat k="TDEE" v={`${result.tdee_kcal}`} sub="kcal / day" />
            <Stat
              k="Target"
              v={`${result.daily_target_kcal}`}
              sub="kcal / day"
              emphasis
            />
          </View>
        </Card>
      )}
    </Screen>
  );
}

function Field({
  label,
  unit,
  value,
  onChange,
  style,
}: {
  label: string;
  unit?: string;
  value: string;
  onChange: (v: string) => void;
  style?: object;
}) {
  return (
    <View style={[styles.field, style]}>
      <Text style={styles.label}>
        {label}
        {unit ? <Text style={styles.unit}> · {unit}</Text> : null}
      </Text>
      <TextInput
        style={styles.input}
        value={value}
        onChangeText={onChange}
        keyboardType="numeric"
        inputMode="numeric"
        placeholderTextColor={colors.muted}
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

function Stat({
  k,
  v,
  sub,
  emphasis,
}: {
  k: string;
  v: string;
  sub?: string;
  emphasis?: boolean;
}) {
  return (
    <View style={[styles.statCell, emphasis && styles.statCellEmphasis]}>
      <Text style={styles.statLabel}>{k}</Text>
      <Text style={[styles.statValue, emphasis && styles.statValueEmphasis]}>{v}</Text>
      {sub ? <Text style={[styles.statSub, emphasis && styles.statSubEmphasis]}>{sub}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  intro: { gap: spacing.sm },
  title: { ...typography.title, color: colors.text },
  help: { ...typography.body, color: colors.textMuted },

  row: { flexDirection: 'row', gap: spacing.md },
  field: { gap: 6 },
  label: { fontSize: 13, fontWeight: '600', color: colors.textMuted, letterSpacing: 0.2 },
  unit: { color: colors.muted, fontWeight: '400' },
  input: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    fontSize: 16,
    backgroundColor: colors.surface,
    color: colors.text,
  },
  segmented: { flexDirection: 'row', gap: spacing.sm },

  result: { gap: spacing.md },
  resultHeader: { gap: spacing.xs },
  resultTitle: { ...typography.heading, color: colors.text },

  statGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  statCell: {
    flexBasis: '48%',
    flexGrow: 1,
    backgroundColor: colors.surface,
    borderRadius: radii.md,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  statCellEmphasis: {
    backgroundColor: colors.accentDark,
    borderColor: colors.accentDark,
  },
  statLabel: {
    ...typography.eyebrow,
    color: colors.muted,
  },
  statValue: {
    fontSize: 22,
    fontWeight: '800',
    color: colors.text,
    marginTop: 2,
  },
  statValueEmphasis: { color: '#FFFFFF' },
  statSub: {
    ...typography.caption,
    color: colors.muted,
  },
  statSubEmphasis: { color: '#E7F8EE' },
});
