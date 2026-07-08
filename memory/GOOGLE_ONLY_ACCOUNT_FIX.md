# Permanent Fix: Google-only accounts can't use password login (cross-platform)

## Root cause
Users who sign up with "Continue with Google" get a Firebase account with
`providers=['google.com']` and **no password**. When they later try email+password
login (website OR app), Firebase rejects it. Firebase's **Email Enumeration
Protection** (default-ON since 15 Sep 2023) hides which providers an email uses,
so `fetchSignInMethodsForEmail()` returns `[]` and the client **cannot detect**
this before login. Failed logins only return the generic `auth/invalid-credential`.

## Website side (DONE — this repo)
`frontend/src/pages/Auth.jsx` → `loginErr()` now shows, on `auth/invalid-credential`:
"If you signed up with Google, use Continue with Google. Otherwise reset via Forgot password."
Website has Google button + password reset, so Google-only users have a working path.

## App side (for the mobile/DO team) — see prompt below.

## Why permanent
- Guidance covers the un-detectable case gracefully on both platforms.
- Email OTP (already on DO backend `/auth/send-otp` + `/auth/verify-otp`) is a
  provider-agnostic login that works for Google-only accounts too.
- `sendPasswordResetEmail` lets a Google-only user ADD a password permanently.
- Optional (recommended): a server-side `/auth/providers?email=` endpoint using the
  Firebase Admin SDK bypasses enumeration protection and gives exact provider info.
