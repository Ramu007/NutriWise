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

### Auth

Until the Cognito hosted UI flow lands, the app runs in dev-bypass mode: every
request sends `X-User-Id`, and the API accepts it as long as `ENV=dev` and
`COGNITO_USER_POOL_ID` is unset. Override the user with
`EXPO_PUBLIC_DEV_USER_ID` if you want to demo more than one persona.

Once Cognito sign-in lands, call `signIn(jwt)` from `src/services/auth.ts`;
every subsequent request sends `Authorization: Bearer <jwt>` and `X-User-Id`
is ignored on the server side.

### Photo upload

The meal-log screen uses the presigned-upload flow: the app asks the API for a
short-lived S3 PUT URL, uploads the photo directly to S3, then calls
`/v1/food/analyze-key` with the resulting key. This keeps large image payloads
off the Lambda request path.

## Screens

- `app/index.tsx` — home / onboarding
- `app/profile.tsx` — health profile form (BMI/BMR/TDEE)
- `app/log.tsx` — meal photo capture + AI analysis
- `app/find.tsx` — nutritionist directory with US/India tabs

## Type checking

```bash
npm run typecheck
```
