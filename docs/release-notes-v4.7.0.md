## Beatify v4.7.0 — "Second Wind"

Syncs **145 commits** from upstream `mholzi/beatify` main — up to and including
their `4.6.0-rc1` ("Second Wind") candidate, and past their `4.5.0` ("Your
Call"), `4.4.3` and `4.4.2` releases — onto the fork's 4.6.0 build. A large game
release: six selectable game modes with a real way in, a host control drawer,
Ghost League, Encore, rematch without re-scanning, per-guest language, five new
Latin/Spanish playlists and a run of engine hardening. The fork's own Race mode
(Title & Artist Live Race, 10/15s auto-advance) is carried forward unchanged.

> **Built on the fork's 4.6.0.** This release folds in everything upstream
> shipped since the last sync. The fork's Race-mode work — the live buzzer, the
> TV race panel and the 10/15-second auto-advance — is preserved on top of
> upstream's reworked game engine (`GameOptions`, the provider registry, the
> player-state allowlist).

### 🎮 Six game modes get a way in (#2692, #2759)

Six modes that shipped complete but unreachable — their only switches lived in a
CSS-hidden admin panel — are now selectable through a play style in the wizard.

### 👻 Ghost League (#2559)

A player knocked out in Sudden Death keeps guessing in a league of their own,
scored per ghost round, with its own block on the TV and a Best-Ghost award at
the end.

### ⏭️ Encore (#2503)

On the reveal before the last round, the game offers five more rounds without
touching a single score. Once the last round starts the offer is gone, so the
finale stays a finale.

### 🎛️ A host control drawer on the phone

- **Pause with a reason the whole room sees (#2645).**
- **Drop a round instead of scoring a broken song (#2646),** with a consequence
  preview and an optional reason.
- **Arm Sudden Death (#2723)** and **take the party lights back mid-game (#2649).**
- **Sit a guest out and bring them back (#2746);** the return lands at the next
  round so no one is scored on a song they did not hear.
- **Rematch with a different playlist — the end screen becomes the start screen
  (#2648)** — no twenty-phone rescan.

### 🌍 Reach & polish

- **Each guest's phone speaks the guest's language (#2585);** the lobby announces
  what game is coming as a generated sentence (#2647).
- **In-round reactions for players who have already answered (#2562).**
- **One favicon on all five pages (#2483, #2479).**

### 🐛 Fixes carried in

- **The speaker no longer plays on after the game ends (#2605);** the TV shows the
  pause screen instead of freezing (#2617); finale spectators are no longer scored
  or allowed to guess (#2612).
- **The setup wizard's picks reach the open lobby game it left running (#2769).**
- **`End` ends the game and a phone rematch keeps its own socket (#2726);** the
  podium survives the REST path (#2724).
- **Health-check asks the ISRC and the claimed storefronts, not the display title
  (#2787).**

### 🎵 The catalogue

Now **66 playlists and 8,432 songs** — five new Latin/Spanish lists (Deutschrap
Klassiker, Clásicos del Rock en Español, Rock Rioplatense, Vallenato Clásico,
Música Colombiana Alegre) plus Apple / YouTube / Deezer backfills and broken-URI
corrections across the catalogue.

### 🔧 Engine & tooling

- **One provider registry instead of fifteen hand-kept copies (#2713);** confetti
  and the dashboard stylesheets served from the box, not the internet (#2742).
- **`MediaPlayerService` split one module per platform (#2636);** shared
  constants get a single home (#2699, #2700); the CI matrix runs Python 3.14
  (#2581); the lockfile is committed, CI switched to `npm ci`, Dependabot added
  (#2788).

---

**Fork-integration notes.** Race mode was re-threaded through upstream's new
architecture: `title_artist_race_mode` is now a `GameOptions` field, a member of
the #2634 player-state allowlist, and part of the #2635 rematch capture; the
fork's 10s/15s auto-advance is kept by carrying those two values in the shared
`REVEAL_AUTO_ADVANCE_OPTIONS` list (const.py + the JS mirror). Upstream's unified
`provider_spec.plays_on()` check replaced the fork's per-provider capability
guards.

**Verified:** frontend build in sync (`npm run build:check` clean), JS **1445**
tests passing, Python **2896** passing / 2 skipped.

**Install / update** via HACS as a custom repository (Integration), or update
from HACS if already installed — manifest version is `4.7.0`.
