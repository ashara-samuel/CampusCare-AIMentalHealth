# CampusCare on Android & iOS

The mobile apps are the **same web frontend** wrapped in a native shell with
[Capacitor](https://capacitorjs.com), talking to the deployed API. No rewrite —
one codebase, both stores.

- Web UI: `frontend/` (served by the backend at `/ui/`)
- Mobile app: Capacitor wraps `frontend/` into native Android + iOS projects
- Backend: unchanged, running on Render; the app calls it over the network
  (`frontend/config.js` points at the deployed API; CORS allows the app origins)

## What you need

| | Android | iOS |
|---|---|---|
| Build machine | Windows / Mac / Linux | **Mac only** (Xcode) |
| Tooling | Android Studio + JDK 17 | Xcode 15+ |
| Store account | Google Play Console — **$25 once** | Apple Developer — **$99/year** |
| Output | `.aab` (App Bundle) | `.ipa` |

iOS genuinely cannot be built without a Mac. If you don't have one: use a Mac in
the cloud (e.g. MacStadium, or a CI service like Codemagic/EAS that provides
macOS build runners).

## One-time setup

```bash
# from the repo root
npm install
npx cap add android      # creates ./android
npx cap add ios          # creates ./ios   (Mac only)

# generate app icons + splash from assets/icon.png & assets/splash.png
npx capacitor-assets generate --iconBackgroundColor '#3a8f7f' --splashBackgroundColor '#f4f7f8'
```

Whenever you change anything in `frontend/`:

```bash
npx cap sync            # copies the web assets into the native projects
```

## Android build

```bash
npx cap open android          # opens Android Studio
# In Android Studio: Build > Generate Signed Bundle / APK > Android App Bundle
#   - create/choose a signing key (keep it safe — you need the SAME key forever)
#   - build the release .aab
```
Upload the `.aab` in the **Google Play Console** (Create app → Production →
Create release → upload).

## iOS build (Mac)

```bash
npx cap open ios              # opens Xcode
# In Xcode:
#   - set the Bundle Identifier to com.asharasamuel.campuscare
#   - Signing & Capabilities: select your Apple Developer team
#   - Product > Archive, then Distribute App > App Store Connect
```
Submit from **App Store Connect**.

## Config notes

- **App ID:** `com.asharasamuel.campuscare` (in `capacitor.config.json`). Change
  it if you want a different identifier — but do it *before* first store upload;
  it can't change afterward.
- **API URL:** `frontend/config.js` has `API_BASE`. If you move the backend off
  the current Render URL, update it there and run `npx cap sync`.
- **CORS:** `app/config.py` already allows the Capacitor origins
  (`capacitor://localhost`, `https://localhost`). If a build uses a different
  origin, add it and redeploy the backend.

## Store review — read before submitting

A **mental-health** app gets extra scrutiny on both stores. Prepare:

- **Privacy policy** (required by both) — a public URL explaining what you collect
  (account email, conversation history) and how it's protected. You don't have one
  yet; write it before submitting.
- **Crisis resources** — present in-app (already built). Apple's guidelines expect
  medical/health apps to be responsible and not replace professional care; the app
  already states this.
- **"Not a medical device / not a therapist"** framing — already in the UI
  disclaimer; keep it.
- **Age rating** — answer the questionnaire honestly; a wellbeing app aimed at
  students will likely be 12+/17+ depending on content answers.
- **Data safety form** (Play) / **App Privacy** labels (Apple) — declare that you
  collect email + chat history, used for app functionality, not shared.
- **Account deletion** — both stores require apps with accounts to let users delete
  their account/data. ✅ Built: `DELETE /auth/me` removes the account and all its
  data, reachable in-app via the "Delete account" button.

## Before a real launch (production hardening)

Same list as `DEPLOY.md`, plus: encrypt conversation history at rest and a real
privacy policy (account deletion is done). This app handles sensitive data about
potentially vulnerable users — treat the store review as a floor, not the bar.
