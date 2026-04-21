import React from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors } from '../theme/colors';

type Props = {
  children: React.ReactNode;
  scroll?: boolean;
};

export function Screen({ children, scroll = true }: Props) {
  const content = (
    <View style={styles.inner}>
      {children}
    </View>
  );
  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      {scroll ? <ScrollView contentContainerStyle={styles.scroll}>{content}</ScrollView> : content}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  scroll: { flexGrow: 1 },
  inner: { paddingHorizontal: 20, paddingVertical: 16, gap: 16 },
});
