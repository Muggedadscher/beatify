## Beatify v4.5.0 — "Keep what you placed"

Syncs **48 commits** from upstream `mholzi/beatify` main (the `4.3.1-rc1`/`rc2`
line) onto the fork's 4.4.1 build. One new game feature, a run of
server/client robustness fixes, and a large batch of catalogue corrections.
The fork's own Race mode (Title & Artist Live Race, 10/15s auto-advance) is
untouched.

> **Built on the fork's 4.4.1.** This release only folds in what upstream
> shipped since the last sync; nothing in the 4.4 line changed.

### ✨ Collected row — keep every song you placed close enough (#2324)

In closest-wins mode, the songs you land near enough now stay in a personal
collection that's shown on the reveal screen, right beside the score row.

### 🎧 Fill a Tidal track by name when no URI works (#2364)

A missing `uri_tidal` can now be resolved by a name lookup — running strictly
*behind* the stored URIs, with an edition check that rejects a remix, live take
or karaoke version standing in for the recording asked for.

### 🎚️ A year slider that aims at the songs

- **Decade marks under the slider (#2358).** Seventy-odd years of blank rail now
  carry labelled ticks, so the first drag lands near the target.
- **The slider ends where the playlist ends (#2347).** Bounds follow the songs
  actually shipped in the selected playlist, not a fixed range.

### 🛡️ Rounds that hold together

- **Only a genuinely lost session sends a player back to the join screen
  (#2353)** — a brief network wobble no longer forces a mid-round rejoin.
- **The submit button re-enables when an answer doesn't get through (#2354)**,
  and **after a reload the client trusts the server about its own submission
  (#2355).**
- **The round deadline applies to steal and sabotage (#2352).** Power-ups were
  slipping through after the clock ran out.
- **The current answer is no longer readable from the status endpoint before the
  reveal (#2348).**
- **Playback confirmation waits for the speaker to actually change tracks
  (#2349).** A round could otherwise run against a song nobody heard.
- **A handler that crashes is treated as a server error, not a client that sent
  bad JSON (#2351).**
- **The start-failure banner docks above the footer instead of inside it
  (#2365, #2366).**

### 🎵 The catalogue, corrected

Broken-URI, year and backfill fixes across `quebecois-1990-2020`,
`deutschrock-best-of`, `best-canadian-hits`, `100-greatest-rock-songs`,
`90er-hits` and others (#2383, #2381, #2378, #2362, #2357, #2345, #2346, #2347,
#2361, #2359, #2320, #2321, #2322).

---

**Verified:** frontend build in sync (`npm run build:check` clean), JS **659**
tests passing, Python **2132** passing / 2 skipped.

**Install / update** via HACS as a custom repository (Integration), or update
from HACS if already installed — manifest version is `4.5.0`.
