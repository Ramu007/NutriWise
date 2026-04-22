/**
 * Design tokens shared across the app — spacing, radii, typography, shadows.
 * Kept in one place so screens read consistently and tweaks stay cheap.
 */
import { Platform, type TextStyle, type ViewStyle } from 'react-native';

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  '2xl': 32,
  '3xl': 48,
} as const;

export const radii = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  pill: 999,
} as const;

export const typography = {
  display: {
    fontSize: 32,
    fontWeight: '800',
    letterSpacing: -0.4,
    lineHeight: 38,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    letterSpacing: -0.2,
    lineHeight: 30,
  },
  heading: {
    fontSize: 18,
    fontWeight: '700',
    lineHeight: 24,
  },
  subheading: {
    fontSize: 15,
    fontWeight: '600',
    lineHeight: 20,
  },
  body: {
    fontSize: 16,
    fontWeight: '400',
    lineHeight: 24,
  },
  caption: {
    fontSize: 13,
    fontWeight: '500',
    lineHeight: 18,
  },
  eyebrow: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1.4,
    textTransform: 'uppercase',
    lineHeight: 16,
  },
} satisfies Record<string, TextStyle>;

function iosShadow(offsetY: number, radius: number, opacity: number): ViewStyle {
  return {
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: offsetY },
    shadowOpacity: opacity,
    shadowRadius: radius,
  };
}

export const shadows = {
  sm: Platform.select<ViewStyle>({
    ios: iosShadow(2, 6, 0.06),
    android: { elevation: 2 },
    default: { boxShadow: '0 2px 6px rgba(15, 23, 42, 0.06)' } as ViewStyle,
  })!,
  md: Platform.select<ViewStyle>({
    ios: iosShadow(6, 16, 0.08),
    android: { elevation: 4 },
    default: { boxShadow: '0 6px 16px rgba(15, 23, 42, 0.08)' } as ViewStyle,
  })!,
  lg: Platform.select<ViewStyle>({
    ios: iosShadow(12, 28, 0.1),
    android: { elevation: 8 },
    default: { boxShadow: '0 12px 28px rgba(15, 23, 42, 0.1)' } as ViewStyle,
  })!,
};
