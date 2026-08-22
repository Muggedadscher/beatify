## Beatify v4.4.1 — "Upstream, folded in"

A maintenance release: 15 commits from upstream `mholzi/beatify` main, folded onto the fork's 4.4.0 line (Race mode and auto-advance). Most of it is catalogue housekeeping — links that pointed at the wrong recording, years that were a year off — with a few fixes where the server and the backfill tooling were quietly losing information.

> **Built on the fork's 4.4.0.** The Title & Artist Race mode and the 10/15s auto-advance options that define the 4.4 line are untouched here; this release only brings in what upstream shipped since the last sync.

### 🧩 Failures that say what went wrong

- **The three start failures each carry their own code now (#2309).** A start that can't proceed used to come back as one generic error; the recoverable cases are distinguished so the screen can point at the thing to fix rather than shrug.
- **A failed mix keeps the server's reason (#2302).** The client stopped replacing the real cause with a generic "mix failed" — whatever the server knew, the host now sees.
- **Every error response leaves a log line (#2298).** A failure now leaves a trace behind it instead of vanishing, which is the difference between diagnosing a bad start and guessing at it.

### 🎯 Backfill stops wasting the window

- **`--youtube-first` skips ground the cursor already covered (#2310).** The resume cursor is honoured, so a youtube-first pass no longer re-walks playlists it already finished.
- **A free lookup no longer costs the whole quota window (#2317).** The tooling stopped paying full price for a lookup that should have been free.

### 🎧 The catalogue, corrected

Apple / YouTube / Deezer backfills and year and ISRC fixes across the catalogue:

- **Two dead Apple tracks repointed at a release that actually exists everywhere (#2318).**
- **Three `80er-hits` YouTube links that did not play the record, replaced (#2315).**
- **November Rain is 1991, not 1992 (#2312)**, plus 16 of the outstanding one-year conflicts settled (#2313).
- New Apple, Deezer and YouTube ids across `tomorrowland-top-1000`, `musica-italiana` and others (#2299, #2300, #2316).

### 📖 A README that leads with the room

The README was rewritten to open on what the game is in the room, not the stack it runs on, to use the word people actually search for, and to stop implying a paid subscription is required (#2303, #2305, #2307).
