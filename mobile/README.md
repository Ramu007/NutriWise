# NutriWise Mobile

React Native + Expo app. Runs on iOS, Android, and the web.

## Setup

```bash
npm install
npx expo start
```

Press `i` for iOS simulator, `a` for Android emulator, `w` for web.

## Backend

The app talks to the FastAPI backend in `../api`. By default it expects
`http://localhost:8000`; override with `EXPO_PUBLIC_API_URL` (e.g. the deployed
API Gateway endpoint from the CDK `ApiStack`).

## Screens

- `app/index.tsx` — home / onboarding
- `app/profile.tsx` — health profile form (BMI/BMR/TDEE)
- `app/log.tsx` — meal photo capture + AI analysis
- `app/find.tsx` — nutritionist directory with US/India tabs

## Type checking

```bash
npm run typecheck
```
