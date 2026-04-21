import { Link } from 'expo-router';
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { Button } from '../src/components/Button';
import { Screen } from '../src/components/Screen';
import { colors } from '../src/theme/colors';

export default function Home() {
  return (
    <Screen>
      <View style={styles.hero}>
        <Text style={styles.eyebrow}>Welcome to NutriWise</Text>
        <Text style={styles.title}>Your nutrition, guided.</Text>
        <Text style={styles.body}>
          Connect with certified nutritionists in the US and India, track meals with a single photo,
          and hit your goals faster with AI-assisted insights.
        </Text>
      </View>

      <View style={styles.cta}>
        <Link href="/profile" asChild>
          <Button label="Set up your profile" onPress={() => {}} />
        </Link>
        <Link href="/log" asChild>
          <Button label="Log a meal" variant="secondary" onPress={() => {}} />
        </Link>
        <Link href="/find" asChild>
          <Button label="Find a nutritionist" variant="secondary" onPress={() => {}} />
        </Link>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  hero: { gap: 8, paddingVertical: 20 },
  eyebrow: { color: colors.accent, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 1 },
  title: { fontSize: 28, fontWeight: '800', color: colors.text },
  body: { fontSize: 16, color: colors.muted, lineHeight: 22 },
  cta: { gap: 12, marginTop: 8 },
});
