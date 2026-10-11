## Beatify v4.7.2 — Songs everyone knows

A content and data release. No game-logic changes.

### 🎯 Greatest Hits of All Time: +100 songs everyone knows (236 → 336)

The playlist leaned heavily on 60s–90s rock. It now covers the universal
sing-along hits from **1954 to 2023**: Bill Haley, Elvis and the Beatles; ABBA-era
pop; Madonna, Michael Jackson, Tina Turner and Rick Astley; 90s eurodance such as
Macarena, Barbie Girl and Blue (Da Ba Dee); and the big chart hits of the 2000s to
2020s, from Hey Ya! and Umbrella to Happy, Despacito, Blinding Lights and Flowers.

- Every song is reused from an existing Beatify playlist, so its streaming links
  were already checked. All 100 Spotify links were checked again live.
- **9 release years corrected** where the source entry was off, e.g. Johnny B.
  Goode 1958, Shake It Off 2014, Uptown Funk 2014, Blinding Lights 2019.
- **51 fun facts rewritten** in EN/DE/ES/FR/NL/IT. They replace placeholders such as
  "A chart hit by …", texts written for another playlist, and a few that were
  simply wrong.

### 🍎 Apple Music in Germany: verified links across the whole catalogue

2,749 songs had no German-storefront Apple Music link. A German Apple Music game
fell back to the US track ID and timed out wherever that ID is missing from the
German catalogue. Three such timeouts in a row paused the game with a misleading
"re-authenticate your provider" banner.

- **8,285 of 8,532 songs** now carry a `de` link verified against the German
  catalogue (was 5,783).
- **67 songs** that had no Apple Music link at all gained one.
- **99 songs** that are not available in Germany are marked unavailable there, so
  the game skips them instead of waiting on a timeout.
- Greatest Hits of All Time has verified links in all seven storefronts (us, de,
  gb, fr, es, nl, it).
- Two cross-provider mismatches are fixed. *The Ketchup Song* now plays the same
  Spanglish version on Deezer as on Spotify. *Levitating* now plays the original
  on Spotify and YouTube Music instead of the DaBaby remix, matching Apple and
  Deezer.

### 🔧 Apple backfill no longer mistakes remixes for originals

`uri_gate.suffix_conflict` cut everything after a `feat.` credit, including a
remix marker such as `[Sebastian Perez Remix]`, so the backfill accepted remixes
as the original recording. It now removes only the credit itself, and ordinary
titles containing "with" are no longer truncated either. New regression tests
cover both cases.

---

**Verified:** playlist schema gate passing; pytest **2902** passed; JS **1451**
tests passing; ruff clean.

**Install / update** via HACS — manifest version is `4.7.2`.
