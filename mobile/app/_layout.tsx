import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <StatusBar style="dark" />
      <Stack screenOptions={{ headerTitleStyle: { fontWeight: '700' } }}>
        <Stack.Screen name="index" options={{ title: 'NutriWise' }} />
        <Stack.Screen name="profile" options={{ title: 'Your health profile' }} />
        <Stack.Screen name="log" options={{ title: 'Log a meal' }} />
        <Stack.Screen name="find" options={{ title: 'Find a nutritionist' }} />
      </Stack>
    </SafeAreaProvider>
  );
}
