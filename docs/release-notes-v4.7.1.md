## Beatify v4.7.1 — Race-mode hotfix

A single fix for a regression the 4.7.0 upstream sync introduced.

### 🐛 Race mode stays Race mode (was: fell back to year guessing)

After 4.7.0, upstream's new **play-style cards** (#2692) lead the wizard's
game-mode step. Applying a play style drives its bonus toggles through the shared
precedence that turns **Title & Artist** off whenever a year-round bonus (`artist`,
`closest`) turns on — and the **Classic** style names `artist`. The result: a host
who picked **Race mode** and then tapped a play style was silently thrown back to
**guessing years** the moment the round started.

**The fix:** a play style flavours only the year-round bonus layer; it is not a
core-mode choice. `applyPlayStyle` now snapshots and restores the core game mode
(Year vs Title & Artist, and the fork's Race variant under it). The bonuses stay
suppressed under Title & Artist at payload-build time as before, so nothing is
lost — Race mode simply survives a play-style tap now.

Guarded by a new regression test, `play-style-preserves-race-mode.test.js`, plus
a mechanism test that pins exactly why it broke.

---

**Verified:** frontend build in sync (`npm run build:check` clean), JS **1451**
tests passing.

**Install / update** via HACS — manifest version is `4.7.1`.
