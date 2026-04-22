import React from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { colors } from '../theme/colors';
import { spacing } from '../theme/tokens';

type Props = {
  children: React.ReactNode;
  scroll?: boolean;
  /** Skip the default horizontal padding so a child (e.g. FlatList) can bleed to the edges. */
  edgeToEdge?: boolean;
};

export function Screen({ children, scroll = true, edgeToEdge = false }: Props) {
  const inner = (
    <View style={[styles.inner, edgeToEdge && styles.innerEdge]}>
      <View style={styles.contentWrap}>{children}</View>
    </View>
  );
  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      {scroll ? (
        <ScrollView
          contentContainerStyle={styles.scroll}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {inner}
        </ScrollView>
      ) : (
        inner
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  scroll: { flexGrow: 1 },
  inner: {
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.lg,
    gap: spacing.lg,
    flex: 1,
  },
  innerEdge: {
    paddingHorizontal: 0,
  },
  contentWrap: {
    width: '100%',
    maxWidth: 640,
    alignSelf: 'center',
    gap: spacing.lg,
    flex: 1,
  },
});
