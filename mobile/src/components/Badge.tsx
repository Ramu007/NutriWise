import React from 'react';
import { StyleSheet, Text, View, type ViewStyle } from 'react-native';

import { colors } from '../theme/colors';
import { radii, spacing } from '../theme/tokens';

type Tone = 'accent' | 'highlight' | 'neutral' | 'danger';

type Props = {
  label: string;
  tone?: Tone;
  style?: ViewStyle;
};

const tonePairs: Record<Tone, { bg: string; fg: string }> = {
  accent: { bg: colors.accentSoft, fg: colors.accentDark },
  highlight: { bg: colors.highlightSoft, fg: colors.highlight },
  neutral: { bg: colors.surfaceAlt, fg: colors.textMuted },
  danger: { bg: colors.dangerSoft, fg: colors.danger },
};

export function Badge({ label, tone = 'neutral', style }: Props) {
  const { bg, fg } = tonePairs[tone];
  return (
    <View style={[styles.base, { backgroundColor: bg }, style]}>
      <Text style={[styles.label, { color: fg }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  base: {
    paddingHorizontal: spacing.md,
    paddingVertical: 4,
    borderRadius: radii.pill,
    alignSelf: 'flex-start',
  },
  label: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.4,
  },
});
