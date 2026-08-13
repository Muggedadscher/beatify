"""Crate Digger — host corrections to the pool.

A library game is played against the host's own metadata, so a wrong year is
theirs to fix rather than to report upstream. These are the guarantees that
make that safe: a correction outranks every automatic source, survives
rescans, and an identity fix invalidates the metadata that was derived from
the wrong identity.
"""

from __future__ import annotations

import pytest

from custom_components.beatify.library import corrections
from custom_components.beatify.library.year_resolver import YearConfidence


def entry(**over):
    base = {
        "title": "She's Like the Wind",
        "artist": "Patrick Swayze feat. Wendy Fraser",
        "album": "Guilty Pleasures",
        "uri_ma_library": "library://track/207524",
        "year": 2024,
        "year_confidence": int(YearConfidence.EXTERNAL_PRIMARY),
        "year_source": "musicbrainz",
        "genres": ["Films/Games"],
        "genres_checked": 2,
        "popularity_verified": True,
    }
    base.update(over)
    return base


class TestCorrectionOutranksAutomation:
    def test_a_correction_uses_the_user_tier(self):
        out = corrections.apply_correction(entry(), year=1987)
        assert out["year"] == 1987
        assert out["year_confidence"] == int(YearConfidence.USER_VERIFIED)
        assert out["year_source"] == corrections.CORRECTION_SOURCE

    def test_the_user_tier_passes_the_strictest_gate(self):
        """A song the host personally confirmed must never be filtered out."""
        assert int(YearConfidence.USER_VERIFIED) >= int(YearConfidence.EXTERNAL_PRIMARY)

    def test_a_corrected_entry_is_locked(self):
        assert corrections.is_locked(corrections.apply_correction(entry(), year=1987))

    def test_an_untouched_entry_is_not_locked(self):
        assert corrections.is_locked(entry()) is False


class TestIdentityCorrection:
    def test_original_tags_are_preserved(self):
        """The file on disk still has the old tags; a later scan must be able
        to recognise the same track."""
        out = corrections.apply_correction(
            entry(), title="She's Like the Wind", artist="Patrick Swayze"
        )
        assert out["artist"] == "Patrick Swayze"
        assert out["original_artist"] == "Patrick Swayze feat. Wendy Fraser"

    def test_derived_metadata_is_invalidated(self):
        """Genres and popularity matched to the WRONG song are also wrong."""
        out = corrections.apply_correction(entry(), artist="Patrick Swayze")
        assert out["genres"] == []
        assert out["genres_checked"] == 0
        assert out["popularity_verified"] is False

    def test_an_unchanged_identity_leaves_metadata_alone(self):
        out = corrections.apply_correction(
            entry(), year=1987, title="She's Like the Wind"
        )
        assert out["genres"] == ["Films/Games"]
        assert out["genres_checked"] == 2

    def test_case_and_space_differences_are_not_identity_changes(self):
        out = corrections.apply_correction(
            entry(), artist="  patrick swayze FEAT. wendy fraser "
        )
        assert "original_artist" not in out


class TestYearValidation:
    @pytest.mark.parametrize("value", ["1987", 1987])
    def test_plausible_years_are_accepted(self, value):
        year, err = corrections.validate_year(value)
        assert year == 1987 and err is None

    @pytest.mark.parametrize("value", ["not a year", 1200, 3000])
    def test_implausible_years_are_refused(self, value):
        year, err = corrections.validate_year(value)
        assert year is None and err

    def test_empty_means_no_year_change(self):
        assert corrections.validate_year("") == (None, None)


class TestCandidateRanking:
    @staticmethod
    def cand(title, artist, year, score=80):
        return {"title": title, "artist": artist, "year": year, "score": score}

    def test_exact_matches_rank_above_fuzzy_ones(self):
        ranked = corrections.rank_candidates(
            [
                self.cand("Other Song", "Other Artist", 1990),
                self.cand("Wind", "Swayze", 1987),
            ],
            artist="Swayze",
            title="Wind",
        )
        assert ranked[0]["title"] == "Wind"

    def test_candidates_without_a_year_rank_last(self):
        ranked = corrections.rank_candidates(
            [self.cand("Wind", "Swayze", None), self.cand("Wind B", "Other", 1987)],
            artist="Swayze",
            title="Wind",
        )
        assert ranked[-1]["year"] is None

    def test_duplicate_pressings_are_collapsed(self):
        ranked = corrections.rank_candidates(
            [self.cand("Wind", "Swayze", 1987)] * 5, artist="Swayze", title="Wind"
        )
        assert len(ranked) == 1

    def test_the_list_stays_short_enough_to_choose_from(self):
        many = [self.cand(f"T{i}", f"A{i}", 1980 + i) for i in range(30)]
        assert len(corrections.rank_candidates(many, artist="A", title="T")) <= 8


class TestCorrectionsSurviveAutomation:
    def test_refresh_skips_locked_entries(self):
        """A correction exists because the automatic answer was wrong;
        re-resolving it would undo the fix on the next refresh."""
        from pathlib import Path

        pool_src = (
            Path(__file__).resolve().parents[2]
            / "custom_components/beatify/library/pool.py"
        ).read_text()
        assert "not corrections.is_locked(e)" in pool_src

    def test_enrichment_does_not_overwrite_a_locked_year(self):
        from pathlib import Path

        pool_src = (
            Path(__file__).resolve().parents[2]
            / "custom_components/beatify/library/pool.py"
        ).read_text()
        assert "if y is not None and not corrections.is_locked(e):" in pool_src


class TestRevealEntryPoint:
    """The reveal screen must be able to correct without receiving a URI.

    Upstream's reveal payload deliberately withholds playable URIs from
    clients, so the host's screen identifies the song by name and the server
    resolves the pool entry — disambiguated by what was actually just played.
    """

    def _src(self, rel):
        from pathlib import Path

        return (
            Path(__file__).resolve().parents[2] / "custom_components/beatify" / rel
        ).read_text()

    def test_reveal_payload_flags_library_songs_without_a_uri(self):
        code = self._src("game/serializers.py")
        assert '"is_library": bool(gs.current_song.get("uri_ma_library"))' in code

    def test_the_reveal_payload_still_withholds_uris(self):
        """Adding the flag must not smuggle the URI back into the player
        payload — that rule is upstream's, and it still holds."""
        code = self._src("game/serializers.py")
        reveal = code[code.index("Filtered song info during REVEAL") :]
        reveal = (
            reveal[: reveal.index('state["finale_playoff_active"]')]
            if "finale_playoff_active" in reveal
            else reveal[:2000]
        )
        assert '"uri_ma_library": gs.current_song' not in reveal

    def test_corrections_can_be_resolved_by_name(self):
        code = self._src("server/library_views.py")
        assert "def _resolve_pool_entry" in code
        assert "library_recent_songs" in code

    def test_the_host_gets_the_fix_dialog_instead_of_a_report(self):
        code = self._src("www/js/player-reveal.js")
        assert "ctx.song.is_library && state.isAdmin" in code

    def test_the_dialog_ships_in_the_player_bundle(self):
        """The reveal screen lives in the player bundle, so the dialog must
        be there — not only in the admin one."""
        assert "library-pool/correct" in self._src("www/js/player.bundle.min.js")


class TestPlayerFlags:
    """Players notice wrong years first, but must not rewrite the pool.

    A guest's phone reporting a library song used to append to the shared
    data-quality file AND open a GitHub issue about a track the maintainer
    has never seen. Now it flags the song for the host, who can fix it.
    """

    def _src(self, rel):
        from pathlib import Path

        return (
            Path(__file__).resolve().parents[2] / "custom_components/beatify" / rel
        ).read_text()

    def test_library_songs_never_reach_the_public_report_path(self):
        code = self._src("server/ws_handlers/__init__.py")
        branch = code[code.index('if song.get("uri_ma_library"):') :]
        # the branch must return BEFORE the report/GitHub machinery below it
        assert branch.index("return") < branch.index("_create_gh_issue")

    def test_a_flag_records_who_and_how_many(self):
        code = self._src("server/ws_handlers/__init__.py")
        assert "def _flag_library_song" in code
        assert '"count"' in code and '"reporters"' in code

    def test_flags_cannot_grow_without_bound(self):
        """A long party must not accumulate flags indefinitely."""
        code = self._src("server/ws_handlers/__init__.py")
        assert "len(flags) > 200" in code

    def test_the_host_sees_flagged_songs_first(self):
        code = self._src("server/library_views.py")
        assert '"flagged"' in code and "out.sort(" in code

    def test_players_get_an_honest_button_label(self):
        code = self._src("www/js/player-reveal.js")
        assert "reveal.flagYearBtn" in code and "reveal.flaggedForHost" in code

    def test_only_the_host_gets_the_correction_dialog(self):
        code = self._src("www/js/player-reveal.js")
        assert "ctx.song.is_library && !state.isAdmin" in code


class TestSummary:
    def test_summary_reports_what_the_ui_needs(self):
        out = corrections.apply_correction(
            entry(), year=1987, artist="Patrick Swayze", note="fixed by hand"
        )
        summary = corrections.correction_summary(out)
        assert summary["corrected"] is True
        assert summary["original_artist"] == "Patrick Swayze feat. Wendy Fraser"
        assert summary["note"] == "fixed by hand"
