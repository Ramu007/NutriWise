import { Link } from 'expo-router';
import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Badge } from '../src/components/Badge';
import { Button } from '../src/components/Button';
import { Screen } from '../src/components/Screen';
import { colors } from '../src/theme/colors';
import { radii, shadows, spacing, typography } from '../src/theme/tokens';

export default function Home() {
  return (
    <Screen>
      <View style={styles.hero}>
        <Badge label="Nutrition, guided" tone="accent" />
        <Text style={styles.title}>Eat smarter.{'\n'}Feel better.</Text>
        <Text style={styles.body}>
          Connect with certified nutritionists in the US and India, snap a photo to log your meals,
          and hit your goals with AI-assisted insights.
        </Text>

        <View style={styles.ctaRow}>
          <Link href="/profile" asChild>
            <Button label="Get started" size="lg" onPress={() => {}} style={{ flex: 1 }} />
          </Link>
          <Link href="/find" asChild>
            <Button
              label="Browse experts"
              variant="secondary"
              size="lg"
              onPress={() => {}}
              style={{ flex: 1 }}
            />
          </Link>
        </View>
      </View>

      <View style={styles.statsRow}>
        <Stat value="2" label="countries" />
        <Stat value="30s" label="meal log" />
        <Stat value="AI" label="insights" />
      </View>

      <View style={styles.featureGrid}>
        <FeatureCard
          href="/profile"
          eyebrow="Step 1"
          title="Your health profile"
          description="Tell us your goals. We'll compute BMI, BMR, and a daily calorie target."
          accent={colors.accent}
        />
        <FeatureCard
          href="/log"
          eyebrow="Step 2"
          title="Snap a meal"
          description="Point your camera. We'll estimate items, calories, and macros in seconds."
          accent={colors.highlight}
        />
        <FeatureCard
          href="/today"
          eyebrow="Step 3"
          title="Track your day"
          description="See calories + macros vs your target. Know exactly what's left to eat."
          accent={colors.accent}
        />
        <FeatureCard
          href="/find"
          eyebrow="Step 4"
          title="Find a nutritionist"
          description="Book a virtual or in-home session with verified experts near you."
          accent={colors.accentDark}
        />
      </View>
    </Screen>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <View style={styles.stat}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

function FeatureCard({
  href,
  eyebrow,
  title,
  description,
  accent,
}: {
  href: '/profile' | '/log' | '/today' | '/find';
  eyebrow: string;
  title: string;
  description: string;
  accent: string;
}) {
  return (
    <Link href={href} asChild>
      <Pressable
        accessibilityRole="link"
        style={({ pressed }) => [styles.feature, pressed && styles.featurePressed]}
      >
        <View style={[styles.featureBar, { backgroundColor: accent }]} />
        <View style={styles.featureBody}>
          <Text style={[styles.featureEyebrow, { color: accent }]}>{eyebrow}</Text>
          <Text style={styles.featureTitle}>{title}</Text>
          <Text style={styles.featureDescription}>{description}</Text>
        </View>
        <Text style={[styles.featureArrow, { color: accent }]}>→</Text>
      </Pressable>
    </Link>
  );
}

const styles = StyleSheet.create({
  hero: {
    gap: spacing.md,
    paddingTop: spacing.md,
  },
  title: {
    ...typography.display,
    color: colors.text,
  },
  body: {
    ...typography.body,
    color: colors.textMuted,
    maxWidth: 520,
  },
  ctaRow: {
    flexDirection: 'row',
    gap: spacing.md,
    marginTop: spacing.sm,
  },
  statsRow: {
    flexDirection: 'row',
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.lg,
    padding: spacing.lg,
    ...shadows.sm,
  },
  stat: {
    flex: 1,
    alignItems: 'center',
    gap: 4,
  },
  statValue: {
    fontSize: 22,
    fontWeight: '800',
    color: colors.text,
  },
  statLabel: {
    ...typography.caption,
    color: colors.muted,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
  },
  featureGrid: {
    gap: spacing.md,
  },
  feature: {
    flexDirection: 'row',
    alignItems: 'stretch',
    backgroundColor: colors.surface,
    borderRadius: radii.lg,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: 'hidden',
    ...shadows.sm,
  },
  featurePressed: {
    backgroundColor: colors.surfaceSunken,
  },
  featureBar: {
    width: 6,
  },
  featureBody: {
    flex: 1,
    padding: spacing.lg,
    gap: 4,
  },
  featureEyebrow: {
    ...typography.eyebrow,
  },
  featureTitle: {
    ...typography.heading,
    color: colors.text,
  },
  featureDescription: {
    ...typography.caption,
    color: colors.textMuted,
    fontSize: 14,
    lineHeight: 20,
  },
  featureArrow: {
    fontSize: 22,
    fontWeight: '800',
    alignSelf: 'center',
    paddingHorizontal: spacing.lg,
  },
});
