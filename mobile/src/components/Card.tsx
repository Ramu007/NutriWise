import React from 'react';
import { StyleSheet, View, type ViewStyle } from 'react-native';

import { colors } from '../theme/colors';
import { radii, shadows, spacing } from '../theme/tokens';

type Props = {
  children: React.ReactNode;
  tone?: 'default' | 'sunken' | 'accent';
  style?: ViewStyle;
};

export function Card({ children, tone = 'default', style }: Props) {
  return <View style={[styles.base, styles[tone], style]}>{children}</View>;
}

const styles = StyleSheet.create({
  base: {
    borderRadius: radii.lg,
    padding: spacing.lg,
    gap: spacing.sm,
    borderWidth: 1,
  },
  default: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    ...shadows.sm,
  },
  sunken: {
    backgroundColor: colors.surfaceSunken,
    borderColor: colors.border,
  },
  accent: {
    backgroundColor: colors.accentSoft,
    borderColor: colors.accent,
  },
});
