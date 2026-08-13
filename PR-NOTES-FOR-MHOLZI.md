# Notes for upstream



---

## Proposal: start the round clock when the song starts, not when the round is created

**Problem.** The round deadline is stamped in `initialize_round`, but the
round-start announcements (`announce_round_start`, `announce_countdown`) play
*after* that point. Players therefore lose the announcement duration from
their guessing time. Measured on Music Assistant voice satellites: a spoken
round number plus "3, 2, 1, go" costs 7-11 s, and the device then needs 1-3 s
to resume the interrupted song.

The cost is proportional, so short rounds suffer most:

| Round duration | Music actually heard |
|---|---|
| 60 s | ~49 s |
| 30 s | ~20 s |
| 15 s | **under 7 s** |

It is worse in languages whose phrases are longer than English, and worse
again with the countdown announcement enabled.

**Existing mitigation and why it is not enough.** #1211 added a manual "Timer
delay" the host sets by hand. That asks the user to measure something the
server can know, and one fixed number cannot fit every round length, language
and device. Estimating the announcement duration in code (we shipped this
first) helps but stays a guess.

**Proposed fix — reuse the intro-splash pattern.** Beatify already solves
exactly this problem elsewhere: for intro splashes (#1699), `initialize_round`
stamps a *placeholder* deadline, `is_deadline_passed()` reports False while
`_intro_splash_pending`, and `confirm_intro_splash()` recomputes the deadline
from the moment the deferred song plays.

Applying the same three steps to announcements:

1. `RoundManager.defer_deadline()` sets `_deadline_deferred` when TTS is
   configured, so the stamped deadline is understood to be a placeholder.
2. `is_deadline_passed()` returns False while deferred — a round whose song is
   not audible yet cannot time out.
3. `RoundManager.start_timer_at_playback()` re-stamps `deadline` from the
   current moment and re-arms the countdown, once playback is confirmed after
   the announcement chain. It is idempotent, so providers that never announce
   are untouched.

Clients are notified so their counters restart from the corrected deadline.

**Result:** every round gives the configured duration of *music*, whatever the
language, phrase set or device, and the manual Timer delay becomes unnecessary
(it can stay as an override for device chimes we cannot observe).

A working implementation is in this branch — see `game/round_manager.py`
(`defer_deadline`, `start_timer_at_playback`) and the call sites in
`game/state_lifecycle.py`. Happy to split it into a standalone PR.

---

## Bug: announcement duck/restore can ratchet the volume upward

On a ShieldTV feeding an AV receiver, Music Assistant raises the volume for
each announcement and restores it afterwards — but the restored level came
back slightly higher each round, so the music became painfully loud within a
few rounds. Beatify does not change volume around announcements, but it is the
component positioned to notice.

Mitigation in this branch: snapshot `volume_level` before the announcement
chain and, if it has risen by more than 0.05 during the announcement window,
set it back once. Bounded to the first ~10 s of the round so the host's own
volume buttons keep working for the rest of it.

---

## Five translation keys missing from every locale

`admin.ttsPreRoundDelay`, `admin.ttsPreRoundDelayHelp`,
`onboarding.startAnywayTitle`, `onboarding.startAnywayConfirm` and
`playlistHub.topTabs.label` are referenced in code/markup but exist in no
locale file, so non-English hosts silently see English (visible as console
warnings when switching language). Added and translated for en/de/es/fr/nl in
this branch; trivial to cherry-pick.
