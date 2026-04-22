import React, { useRef } from 'react';
import {
  Animated,
  Pressable,
  StyleSheet,
  Text,
  type PressableProps,
  type ViewStyle,
} from 'react-native';

import { colors } from '../theme/colors';
import { radii, shadows, spacing } from '../theme/tokens';

type Variant = 'primary' | 'secondary' | 'ghost';
type Size = 'md' | 'lg';

type Props = {
  label: string;
  onPress: () => void;
  variant?: Variant;
  size?: Size;
  disabled?: boolean;
  style?: ViewStyle;
  accessibilityHint?: PressableProps['accessibilityHint'];
};

export function Button({
  label,
  onPress,
  variant = 'primary',
  size = 'md',
  disabled,
  style,
  accessibilityHint,
}: Props) {
  const scale = useRef(new Animated.Value(1)).current;

  const onPressIn = () => {
    Animated.spring(scale, {
      toValue: 0.97,
      useNativeDriver: true,
      speed: 40,
      bounciness: 0,
    }).start();
  };
  const onPressOut = () => {
    Animated.spring(scale, {
      toValue: 1,
      useNativeDriver: true,
      speed: 30,
      bounciness: 6,
    }).start();
  };

  return (
    <Animated.View style={[{ transform: [{ scale }] }, style]}>
      <Pressable
        accessibilityRole="button"
        accessibilityState={{ disabled: !!disabled }}
        accessibilityHint={accessibilityHint}
        onPress={onPress}
        onPressIn={onPressIn}
        onPressOut={onPressOut}
        disabled={disabled}
        style={({ pressed }) => [
          styles.base,
          size === 'lg' ? styles.sizeLg : styles.sizeMd,
          variantStyles[variant].container,
          pressed && !disabled && variantStyles[variant].pressed,
          disabled && styles.disabled,
        ]}
      >
        <Text style={[styles.label, size === 'lg' && styles.labelLg, variantStyles[variant].label]}>
          {label}
        </Text>
      </Pressable>
    </Animated.View>
  );
}

const variantStyles = {
  primary: StyleSheet.create({
    container: {
      backgroundColor: colors.accent,
      borderWidth: 1,
      borderColor: colors.accentDark,
      ...shadows.sm,
    },
    pressed: { backgroundColor: colors.accentDark },
    label: { color: '#FFFFFF' },
  }),
  secondary: StyleSheet.create({
    container: {
      backgroundColor: colors.surface,
      borderWidth: 1,
      borderColor: colors.border,
    },
    pressed: { backgroundColor: colors.surfaceAlt },
    label: { color: colors.text },
  }),
  ghost: StyleSheet.create({
    container: {
      backgroundColor: 'transparent',
      borderWidth: 1,
      borderColor: 'transparent',
    },
    pressed: { backgroundColor: colors.surfaceAlt },
    label: { color: colors.accentDark },
  }),
};

const styles = StyleSheet.create({
  base: {
    borderRadius: radii.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sizeMd: {
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
    minHeight: 46,
  },
  sizeLg: {
    paddingVertical: spacing.lg - 2,
    paddingHorizontal: spacing.xl,
    minHeight: 54,
    borderRadius: radii.lg,
  },
  disabled: { opacity: 0.5 },
  label: {
    fontSize: 16,
    fontWeight: '600',
    letterSpacing: 0.1,
  },
  labelLg: {
    fontSize: 17,
    fontWeight: '700',
  },
});
