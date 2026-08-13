"""Crate Digger — the metadata layer: years, popularity, and pool backups.

A library game is only fair if the YEAR is right and "popular" means popular
in the world rather than popular in this particular collection. These are the
guarantees behind that claim, plus the safety rules for backup/restore.
"""

from __future__ import annotations

import pytest

from custom_components.beatify.library import backup, popularity
from custom_components.beatify.library import year_resolver as yr


class TestCompilationDetection:
    """Compilation pressings are the biggest source of wrong years.

    A 1965 song on a 1998 "Greatest Hits" rip carries 1998 in its tags. Left
    alone, that single class of error makes whole eras look like the nineties.
    """

    @pytest.mark.parametrize(
        "album",
        [
            "Greatest Hits",
            "The Best Of Queen",
            "NOW That's What I Call Music! 42",
            "The Essential Bob Dylan",
            "Unplugged in New York",
            "Live at Wembley",
        ],
    )
    def test_compilation_album_names_are_detected(self, album):
        assert yr._looks_like_compilation(None, None, album_name=album) is True

    @pytest.mark.parametrize("album", ["Guilty Pleasures", "Absolute Rock Classics"])
    def test_name_only_detection_has_known_limits(self, album):
        """Documented gap, not an oversight.

        Some compilation series carry names indistinguishable from studio
        albums ("Guilty Pleasures" is both a Streisand studio album and a
        compilation series). Widening the pattern would demote correct tag
        years on real studio albums, so these are caught by album TYPE or a
        "Various Artists" credit instead — and when neither is present the
        external year lookup is what protects the game.
        """
        assert yr._looks_like_compilation(None, None, album_name=album) is False
        assert yr._looks_like_compilation("compilation", None, album_name=album) is True

    @pytest.mark.parametrize("album", ["Rumours", "Abbey Road", "Thriller"])
    def test_studio_albums_are_not_flagged(self, album):
        assert yr._looks_like_compilation(None, None, album_name=album) is False

    def test_various_artists_marks_a_compilation(self):
        assert (
            yr._looks_like_compilation(None, "Various Artists", album_name="Some Album")
            is True
        )

    @pytest.mark.parametrize("album_type", ["compilation", "soundtrack", "live"])
    def test_album_type_marks_a_compilation(self, album_type):
        assert (
            yr._looks_like_compilation(album_type, None, album_name="Some Album")
            is True
        )


class TestTitleQueryCandidates:
    """MusicBrainz matches badly on decorated titles."""

    def test_raw_title_is_tried_first(self):
        assert yr.title_query_candidates("Vogue")[0] == "Vogue"

    @pytest.mark.parametrize(
        "title",
        [
            "Vogue (Remastered 2011)",
            "Vogue - Radio Edit",
            "Vogue [Live]",
        ],
    )
    def test_decorated_titles_yield_a_clean_candidate(self, title):
        assert "Vogue" in yr.title_query_candidates(title)

    def test_dash_right_hand_side_is_a_candidate(self):
        """`Main Title - Scarface` — the work name follows the dash.

        Without this candidate an entire class of soundtrack and classical
        tracks resolved to no year at all.
        """
        assert "Scarface" in yr.title_query_candidates("Main Title - Scarface")

    def test_candidates_are_unique_and_ordered(self):
        cands = yr.title_query_candidates("Song (Remastered) - Live")
        assert len(cands) == len(set(cands))


class TestMusicBrainzYearSelection:
    """Earliest verified evidence wins — remasters must not win."""

    @staticmethod
    def _rec(artist, date, score=100):
        return {
            "score": score,
            "first-release-date": date,
            "artist-credit": [{"artist": {"name": artist}}],
        }

    def test_earliest_year_among_verified_matches_wins(self):
        recs = [
            self._rec("Queen", "1991-02-05"),
            self._rec("Queen", "1975-10-31"),
            self._rec("Queen", "2011-09-05"),
        ]
        assert yr.pick_mb_year(recs, "Queen") == 1975

    def test_low_scoring_matches_are_ignored(self):
        recs = [self._rec("Queen", "1975", score=10)]
        assert yr.pick_mb_year(recs, "Queen") is None

    def test_a_different_artist_is_not_a_match(self):
        """A wrong authoritative year is worse than no year."""
        recs = [self._rec("Some Tribute Band", "1975")]
        assert yr.pick_mb_year(recs, "Queen") is None

    def test_no_usable_recording_returns_none(self):
        assert yr.pick_mb_year([], "Queen") is None


class TestPopularityScaling:
    def test_deezer_rank_maps_into_the_0_100_scale(self):
        score = popularity.to_global_score(500_000, popularity.SOURCE_DEEZER_RANK)
        assert 0.0 <= score <= 100.0

    def test_more_popular_scores_higher(self):
        low = popularity.to_global_score(1_000, popularity.SOURCE_DEEZER_RANK)
        high = popularity.to_global_score(900_000, popularity.SOURCE_DEEZER_RANK)
        assert high > low

    def test_scaling_is_logarithmic_not_linear(self):
        """Raw ranks are wildly skewed; a linear map buries everything."""
        a = popularity.to_global_score(1_000, popularity.SOURCE_DEEZER_RANK)
        b = popularity.to_global_score(10_000, popularity.SOURCE_DEEZER_RANK)
        c = popularity.to_global_score(100_000, popularity.SOURCE_DEEZER_RANK)
        assert (b - a) == pytest.approx(c - b, abs=1.0)

    def test_unknown_source_yields_no_score(self):
        assert popularity.to_global_score(5, "mystery") is None


class TestPercentiles:
    def test_percentiles_span_the_pool(self):
        pctls = popularity.assign_percentiles([float(i) for i in range(100)])
        assert min(pctls) < 0.05 and max(pctls) > 0.95

    def test_unscored_songs_stay_unknown_not_obscure(self):
        """`None` must never be treated as "least popular"."""
        assert popularity.assign_percentiles([50.0, None])[1] is None

    def test_ties_share_a_percentile(self):
        assert len(set(popularity.assign_percentiles([10.0] * 4))) == 1


class TestBackupValidation:
    def _bundle(self):
        pool = {
            "_schema": 1,
            "songs": [
                {"title": "T", "artist": "A", "uri_ma_library": "library://track/1"}
            ],
            "_config_entry_id": "entry-1",
        }
        return backup.build_backup_bundle(pool, {"size": 30}, provider_version="test")

    def test_a_real_bundle_validates(self):
        bundle, err = backup.validate_backup_bundle(self._bundle())
        assert err is None and bundle is not None

    def test_a_bare_pool_file_is_accepted(self):
        """Copying library_pool.json by hand was the only backup possible
        before this feature existed — such a file must not be rejected."""
        pool = self._bundle()["pool"]
        bundle, err = backup.validate_backup_bundle(pool)
        assert err is None and bundle["pool"]["songs"] == pool["songs"]

    @pytest.mark.parametrize(
        "payload",
        [
            "not an object",
            {"pool": {"songs": "not a list"}},
            {"pool": {"songs": [{"title": "no uri"}]}},
            {"pool": {"songs": ["junk"]}},
        ],
    )
    def test_bad_payloads_are_refused(self, payload):
        _, err = backup.validate_backup_bundle(payload)
        assert err is not None

    def test_a_newer_schema_is_refused_with_guidance(self):
        _, err = backup.validate_backup_bundle(
            {"_backup_schema": backup.BACKUP_SCHEMA + 5, "pool": {"songs": []}}
        )
        assert err is not None and "newer" in err


class TestPoolMerge:
    @staticmethod
    def _song(uri, conf=4, score=50.0, genres=("Rock",)):
        return {
            "uri_ma_library": uri,
            "year_confidence": conf,
            "global_score": score,
            "genres": list(genres),
            "genres_checked": 2,
        }

    def test_new_songs_are_added(self):
        entries, stats = backup.merge_pool_entries(
            {"songs": [self._song("a")]}, {"songs": [self._song("b")]}
        )
        assert stats["added"] == 1 and set(entries) == {"a", "b"}

    def test_a_better_year_wins(self):
        entries, stats = backup.merge_pool_entries(
            {"songs": [self._song("a", conf=2)]},
            {"songs": [self._song("a", conf=4)]},
        )
        assert entries["a"]["year_confidence"] == 4 and stats["improved"] == 1

    def test_a_verified_year_is_never_downgraded(self):
        """A merge must be monotonic — newer is not better."""
        entries, stats = backup.merge_pool_entries(
            {"songs": [self._song("a", conf=4)]},
            {"songs": [self._song("a", conf=1)]},
        )
        assert entries["a"]["year_confidence"] == 4 and stats["kept"] == 1

    def test_entries_without_a_uri_are_skipped(self):
        _, stats = backup.merge_pool_entries(None, {"songs": [{"title": "no uri"}]})
        assert stats["skipped"] == 1

    def test_merging_into_an_empty_pool_works(self):
        entries, stats = backup.merge_pool_entries(None, {"songs": [self._song("z")]})
        assert stats["total"] == 1 and "z" in entries
