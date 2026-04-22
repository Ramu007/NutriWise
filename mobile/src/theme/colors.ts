/**
 * NutriWise palette.
 *
 * Warm off-white background pairs with a deep forest-green accent for the
 * "nutrition" feel, and a muted coral for secondary highlights (macros,
 * ratings). Neutrals are cool-grey so the greens don't start reading swampy.
 */
export const colors = {
  bg: '#FAF8F5',
  surface: '#FFFFFF',
  surfaceAlt: '#F1EFE9',
  surfaceSunken: '#F6F4EE',

  text: '#111418',
  textMuted: '#4B5563',
  muted: '#6B7280',

  accent: '#16A34A',
  accentDark: '#15803D',
  accentSoft: '#DCFCE7',

  highlight: '#F97316',
  highlightSoft: '#FFEDD5',

  danger: '#DC2626',
  dangerSoft: '#FEE2E2',

  border: '#E7E3DA',
  borderStrong: '#CFC8B8',

  overlay: 'rgba(17, 20, 24, 0.5)',
} as const;

export type ColorKey = keyof typeof colors;
