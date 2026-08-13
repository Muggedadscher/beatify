"""Crate Digger — playlist generation from the user's own library.

The generator decides WHICH songs a library game contains. Everything here is
pure (an injected `rng` makes it deterministic), and each test corresponds to a
behaviour that was wrong at some point on real hardware:

* famous-only windows must never be padded with unranked songs
* a genre filter that cannot fill a game degrades along MUSICAL neighbours
  before it degrades down the popularity ranking
* the trust gate keeps unverified years out of games entirely
"""

from __future__ import annotations

import random

import pytest

from custom_components.beatify.library import generator as gen
from custom_components.beatify.library.year_resolver import YearConfidence


def make_song(i, *, genre="Rock", pctl=0.98, score=None, year=1985, conf=None):
    """A pool entry as `pool.py` would have written it."""
    return {
        "title": f"T{i}",
        "artist": f"A{i}",
        "album": "Album",
        "uri_ma_library": f"library://track/{i}",
        "genres": [genre] if genre else [],
        "year": year,
        "year_confidence": int(
            conf if conf is not None else YearConfidence.EXTERNAL_PRIMARY
        ),
        "popularity_percentile": pctl,
        "global_score": score if score is not None else (pctl or 0) * 100,
    }


class TestTrustGate:
    def test_songs_without_a_verified_year_are_excluded(self):
        pool = [make_song(i, conf=YearConfidence.TAG_COMPILATION) for i in range(50)]
        out = gen.generate_playlist(
            pool, size=10, balance_decades=False, rng=random.Random(1)
        )
        assert out["songs"] == []

    def test_relaxing_the_gate_admits_tag_years(self):
        pool = [make_song(i, conf=YearConfidence.TAG_STUDIO) for i in range(50)]
        out = gen.generate_playlist(
            pool,
            size=10,
            min_confidence=int(YearConfidence.TAG_STUDIO),
            balance_decades=False,
            rng=random.Random(1),
        )
        assert len(out["songs"]) == 10

    def test_songs_without_a_library_uri_are_excluded(self):
        pool = [make_song(i) for i in range(20)]
        for song in pool:
            song["uri_ma_library"] = ""
        out = gen.generate_playlist(
            pool, size=5, balance_decades=False, rng=random.Random(1)
        )
        assert out["songs"] == []


class TestPopularityWindow:
    def test_top_percent_selects_only_the_window(self):
        pool = [make_song(i, pctl=i / 100) for i in range(100)]
        out = gen.generate_playlist(
            pool,
            size=5,
            popularity_min_percentile=0.95,
            balance_decades=False,
            rng=random.Random(2),
        )
        assert len(out["songs"]) == 5
        assert out["_eligible_count"] >= 5

    def test_unranked_songs_never_reach_a_famous_window(self):
        """Regression: a "Top 1%" game served a French Disney dub.

        The unknown-popularity fill was gated on `hi >= 0.66`, but a
        "Top P%" window is [1-P/100, 1.0] — `hi` is ALWAYS 1.0, so the guard
        passed for every window and unranked songs padded games that had
        explicitly asked for the most famous tracks in the library.
        """
        unranked = [
            {
                **make_song(9000 + i, pctl=None),
                "popularity_percentile": None,
                "global_score": None,
            }
            for i in range(200)
        ]
        pool = [make_song(i, pctl=0.995) for i in range(3)] + unranked
        out = gen.generate_playlist(
            pool,
            size=30,
            popularity_min_percentile=0.99,
            balance_decades=False,
            rng=random.Random(3),
        )
        # Output entries carry the debug-prefixed key (see _to_song_entry).
        assert all(s.get("_popularity_percentile") is not None for s in out["songs"])
        assert len(out["songs"]) == 3, "a short window returns fewer, not wrong, songs"

    def test_obscure_windows_may_still_use_unranked_songs(self):
        unranked = [
            {
                **make_song(9000 + i),
                "popularity_percentile": None,
                "global_score": None,
            }
            for i in range(50)
        ]
        pool = [make_song(i, pctl=0.2 + i / 1000) for i in range(5)] + unranked
        out = gen.generate_playlist(
            pool,
            size=20,
            popularity_min_percentile=0.05,
            balance_decades=False,
            rng=random.Random(4),
        )
        assert len(out["songs"]) > 5


class TestGenreAdjacency:
    def test_related_genres_are_symmetric_where_expected(self):
        assert {"house", "dance"} <= gen.related_genres({"Trance"})
        assert "trance" in gen.related_genres({"House"})

    def test_related_genres_excludes_the_original(self):
        assert "trance" not in gen.related_genres({"Trance"})

    def test_unknown_genre_maps_to_nothing(self):
        assert gen.related_genres({"Yodelcore"}) == set()

    def test_short_genre_window_fills_from_adjacent_genres_not_deep_cuts(self):
        """Regression: "Top 5% Trance" served Michael Jackson.

        With only 18 eligible tracks, the old order widened DOWN the Trance
        tag — where label pollution puts famous mis-tagged pop at the top.
        Adjacent genres inside the SAME window are what a trance fan expects.
        """
        pool = (
            [make_song(i, genre="Trance", pctl=0.96) for i in range(5)]
            + [make_song(100 + i, genre="House", pctl=0.96) for i in range(200)]
            + [make_song(400 + i, genre="Trance", pctl=0.30) for i in range(100)]
        )
        out = gen.generate_playlist(
            pool,
            size=30,
            popularity_min_percentile=0.95,
            genres={"Trance"},
            balance_decades=False,
            rng=random.Random(5),
        )
        ids = {int(s["uri_ma_library"].rsplit("/", 1)[1]) for s in out["songs"]}
        assert len(out["songs"]) == 30
        assert all(i < 400 for i in ids), "must not dip into the deep Trance tail"
        assert out["_genres_expanded"] == ["House"]

    def test_no_expansion_when_the_genre_can_fill_the_game(self):
        pool = [make_song(i, genre="Rock", pctl=0.96) for i in range(100)]
        out = gen.generate_playlist(
            pool,
            size=30,
            popularity_min_percentile=0.95,
            genres={"Rock"},
            balance_decades=False,
            rng=random.Random(6),
        )
        assert out["_genres_expanded"] == []
        assert out["_window_widened"] is False


class TestRepeatAvoidance:
    def test_recently_played_songs_are_excluded(self):
        pool = [make_song(i) for i in range(100)]
        exclude = {f"library://track/{i}" for i in range(50)}
        out = gen.generate_playlist(
            pool,
            size=10,
            exclude_uris=exclude,
            balance_decades=False,
            rng=random.Random(7),
        )
        assert not ({s["uri_ma_library"] for s in out["songs"]} & exclude)

    def test_exclusion_never_makes_a_game_impossible(self):
        """Repeat-avoidance must yield rather than starve the game."""
        pool = [make_song(i) for i in range(12)]
        exclude = {f"library://track/{i}" for i in range(12)}
        out = gen.generate_playlist(
            pool,
            size=10,
            exclude_uris=exclude,
            balance_decades=False,
            rng=random.Random(8),
        )
        assert len(out["songs"]) == 10


class TestDedupe:
    def test_same_song_on_several_albums_appears_once(self):
        pool = []
        for i in range(5):
            song = make_song(i)
            song["title"] = "Same Title"
            song["artist"] = "Same Artist"
            pool.append(song)
        out = gen.generate_playlist(
            pool, size=5, balance_decades=False, rng=random.Random(9)
        )
        assert len(out["songs"]) == 1


@pytest.mark.parametrize("size", [5, 30, 100])
def test_never_returns_more_than_requested(size):
    pool = [make_song(i, pctl=i / 200) for i in range(200)]
    out = gen.generate_playlist(
        pool, size=size, balance_decades=False, rng=random.Random(10)
    )
    assert len(out["songs"]) <= size
