export const colors = {
  bg: '#FFFFFF',
  surface: '#F7F7F9',
  text: '#111418',
  muted: '#6B7280',
  accent: '#16A34A',
  accentDark: '#15803D',
  danger: '#DC2626',
  border: '#E5E7EB',
} as const;

export type ColorKey = keyof typeof colors;
