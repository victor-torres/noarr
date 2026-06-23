import os
import pytest
import yaml
from pathlib import Path

# Must be set before importing the module (class attrs evaluated at import time)
os.environ.setdefault("DOWNLOADS_DIR", "/tmp")
os.environ.setdefault("BASE_DIR", "/tmp")

from create_links import Media, Movie, TVShow, load_library


@pytest.fixture
def dirs(tmp_path, monkeypatch):
    downloads = tmp_path / "Downloads"
    base = tmp_path / "Media"
    downloads.mkdir()
    base.mkdir()
    monkeypatch.setattr(Media, "DOWNLOADS_DIR", downloads)
    monkeypatch.setattr(Movie, "BASE_DIR", base / "Movies")
    monkeypatch.setattr(TVShow, "BASE_DIR", base / "TV Shows")
    return downloads, base


class TestLoadLibrary:
    def test_loads_movies(self, tmp_path):
        yaml_path = tmp_path / "library.yaml"
        yaml_path.write_text(yaml.dump({
            "movies": [{"title": "Foo (2020)", "path": "Foo.2020.1080p"}],
            "tv_shows": [],
        }))
        library = load_library(yaml_path)
        assert len(library) == 1
        assert isinstance(library[0], Movie)
        assert library[0].title == "Foo (2020)"
        assert library[0].path == Path("Foo.2020.1080p")

    def test_loads_tv_shows(self, tmp_path):
        yaml_path = tmp_path / "library.yaml"
        yaml_path.write_text(yaml.dump({
            "movies": [],
            "tv_shows": [{"title": "Bar (2021)", "path": "Bar.S01.COMPLETE"}],
        }))
        library = load_library(yaml_path)
        assert len(library) == 1
        assert isinstance(library[0], TVShow)
        assert library[0].title == "Bar (2021)"

    def test_skip_subtitles_defaults_to_false(self, tmp_path):
        yaml_path = tmp_path / "library.yaml"
        yaml_path.write_text(yaml.dump({
            "movies": [],
            "tv_shows": [{"title": "Bar (2021)", "path": "Bar.S01.COMPLETE"}],
        }))
        library = load_library(yaml_path)
        assert library[0].skip_subtitles is False

    def test_skip_subtitles_can_be_set(self, tmp_path):
        yaml_path = tmp_path / "library.yaml"
        yaml_path.write_text(yaml.dump({
            "movies": [],
            "tv_shows": [{"title": "Bar (2021)", "path": "Bar.S01.COMPLETE", "skip_subtitles": True}],
        }))
        library = load_library(yaml_path)
        assert library[0].skip_subtitles is True

    def test_magnet_is_loaded(self, tmp_path):
        magnet = "magnet:?xt=urn:btih:abc123"
        yaml_path = tmp_path / "library.yaml"
        yaml_path.write_text(yaml.dump({
            "movies": [{"title": "Foo (2020)", "path": "Foo.2020.1080p", "magnet": magnet}],
            "tv_shows": [],
        }))
        library = load_library(yaml_path)
        assert library[0].magnet == magnet

    def test_magnet_defaults_to_none(self, tmp_path):
        yaml_path = tmp_path / "library.yaml"
        yaml_path.write_text(yaml.dump({
            "movies": [{"title": "Foo (2020)", "path": "Foo.2020.1080p"}],
            "tv_shows": [],
        }))
        library = load_library(yaml_path)
        assert library[0].magnet is None

    def test_movies_come_before_tv_shows(self, tmp_path):
        yaml_path = tmp_path / "library.yaml"
        yaml_path.write_text(yaml.dump({
            "movies": [{"title": "Foo (2020)", "path": "Foo"}],
            "tv_shows": [{"title": "Bar (2021)", "path": "Bar.S01"}],
        }))
        library = load_library(yaml_path)
        assert isinstance(library[0], Movie)
        assert isinstance(library[1], TVShow)

    def test_example_yaml_is_valid(self):
        yaml_path = Path(__file__).parent / "library.example.yaml"
        library = load_library(yaml_path)
        assert len(library) > 0
        assert all(isinstance(m, (Movie, TVShow)) for m in library)


class TestMovie:
    def test_links_mkv_from_directory(self, dirs):
        downloads, base = dirs
        torrent = downloads / "Cool.Movie.2020.1080p"
        torrent.mkdir()
        (torrent / "Cool.Movie.2020.1080p.mkv").touch()

        Movie(title="Cool Movie (2020)", path=Path("Cool.Movie.2020.1080p")).link_files()

        assert (base / "Movies/Cool Movie (2020)/Cool Movie (2020).mkv").is_file()

    def test_links_multiple_files(self, dirs):
        downloads, base = dirs
        torrent = downloads / "Cool.Movie.2020.1080p"
        torrent.mkdir()
        (torrent / "Cool.Movie.2020.1080p.mkv").touch()
        (torrent / "Cool.Movie.2020.1080p.srt").touch()

        Movie(title="Cool Movie (2020)", path=Path("Cool.Movie.2020.1080p")).link_files()

        assert (base / "Movies/Cool Movie (2020)/Cool Movie (2020).mkv").is_file()
        assert (base / "Movies/Cool Movie (2020)/Cool Movie (2020).srt").is_file()

    def test_single_file_torrent(self, dirs):
        downloads, base = dirs
        (downloads / "Cool.Movie.2020.1080p.mkv").touch()

        Movie(title="Cool Movie (2020)", path=Path("Cool.Movie.2020.1080p.mkv")).link_files()

        assert (base / "Movies/Cool Movie (2020)/Cool Movie (2020).mkv").is_file()

    def test_forced_subtitle_naming(self, dirs):
        downloads, base = dirs
        torrent = downloads / "Cool.Movie.2020.1080p"
        torrent.mkdir()
        (torrent / "Cool.Movie.2020.Forced.srt").touch()

        Movie(title="Cool Movie (2020)", path=Path("Cool.Movie.2020.1080p")).link_files()

        assert (base / "Movies/Cool Movie (2020)/Cool Movie (2020).forced.srt").is_file()

    def test_skips_hidden_files(self, dirs):
        downloads, base = dirs
        torrent = downloads / "Cool.Movie.2020.1080p"
        torrent.mkdir()
        (torrent / ".DS_Store").touch()
        (torrent / "Cool.Movie.2020.1080p.mkv").touch()

        Movie(title="Cool Movie (2020)", path=Path("Cool.Movie.2020.1080p")).link_files()

        dest = base / "Movies/Cool Movie (2020)"
        assert (dest / "Cool Movie (2020).mkv").is_file()
        assert not (dest / ".DS_Store").exists()

    def test_skips_existing_destination(self, dirs, capsys):
        downloads, base = dirs
        torrent = downloads / "Cool.Movie.2020.1080p"
        torrent.mkdir()
        (torrent / "Cool.Movie.2020.1080p.mkv").touch()

        movie = Movie(title="Cool Movie (2020)", path=Path("Cool.Movie.2020.1080p"))
        movie.link_files()
        movie.link_files()

        assert "skipping" in capsys.readouterr().out

    def test_force_overwrites_existing(self, dirs):
        downloads, base = dirs
        torrent = downloads / "Cool.Movie.2020.1080p"
        torrent.mkdir()
        (torrent / "Cool.Movie.2020.1080p.mkv").write_text("data")

        movie = Movie(title="Cool Movie (2020)", path=Path("Cool.Movie.2020.1080p"))
        movie.link_files()
        movie.link_files(force=True)

        assert (base / "Movies/Cool Movie (2020)/Cool Movie (2020).mkv").is_file()

    def test_dry_run_creates_no_files(self, dirs):
        downloads, base = dirs
        torrent = downloads / "Cool.Movie.2020.1080p"
        torrent.mkdir()
        (torrent / "Cool.Movie.2020.1080p.mkv").touch()

        Movie(title="Cool Movie (2020)", path=Path("Cool.Movie.2020.1080p")).link_files(dry_run=True)

        assert not (base / "Movies/Cool Movie (2020)").exists()

    def test_creates_hard_link_not_copy(self, dirs):
        downloads, base = dirs
        torrent = downloads / "Cool.Movie.2020.1080p"
        torrent.mkdir()
        source = torrent / "Cool.Movie.2020.1080p.mkv"
        source.write_text("data")

        Movie(title="Cool Movie (2020)", path=Path("Cool.Movie.2020.1080p")).link_files()

        dest = base / "Movies/Cool Movie (2020)/Cool Movie (2020).mkv"
        assert source.stat().st_ino == dest.stat().st_ino


class TestTVShow:
    def test_links_episode_to_correct_path(self, dirs):
        downloads, base = dirs
        torrent = downloads / "Cool.Show.S01.COMPLETE"
        torrent.mkdir()
        (torrent / "Cool.Show.S01E01.1080p.mkv").touch()

        TVShow(title="Cool Show (2020)", path=Path("Cool.Show.S01.COMPLETE")).link_files()

        assert (base / "TV Shows/Cool Show (2020)/Season 01/Cool Show (2020) S01E01.mkv").is_file()

    def test_season_and_episode_zero_padded(self, dirs):
        downloads, base = dirs
        torrent = downloads / "Cool.Show.S02.COMPLETE"
        torrent.mkdir()
        (torrent / "Cool.Show.S02E10.mkv").touch()

        TVShow(title="Cool Show (2020)", path=Path("Cool.Show.S02.COMPLETE")).link_files()

        assert (base / "TV Shows/Cool Show (2020)/Season 02/Cool Show (2020) S02E10.mkv").is_file()

    def test_case_insensitive_episode_pattern(self, dirs):
        downloads, base = dirs
        torrent = downloads / "Cool.Show.S01.COMPLETE"
        torrent.mkdir()
        (torrent / "Cool.Show.s01e03.mkv").touch()

        TVShow(title="Cool Show (2020)", path=Path("Cool.Show.S01.COMPLETE")).link_files()

        assert (base / "TV Shows/Cool Show (2020)/Season 01/Cool Show (2020) S01E03.mkv").is_file()

    def test_skips_file_without_episode_pattern(self, dirs, capsys):
        downloads, base = dirs
        torrent = downloads / "Cool.Show.S01.COMPLETE"
        torrent.mkdir()
        (torrent / "extras.mkv").touch()

        TVShow(title="Cool Show (2020)", path=Path("Cool.Show.S01.COMPLETE")).link_files()

        assert "Could not extract" in capsys.readouterr().out
        assert not (base / "TV Shows/Cool Show (2020)").exists()

    def test_forced_subtitle_in_episode(self, dirs):
        downloads, base = dirs
        torrent = downloads / "Cool.Show.S01.COMPLETE"
        torrent.mkdir()
        (torrent / "Cool.Show.S01E01.Forced.srt").touch()

        TVShow(title="Cool Show (2020)", path=Path("Cool.Show.S01.COMPLETE")).link_files()

        assert (base / "TV Shows/Cool Show (2020)/Season 01/Cool Show (2020) S01E01.forced.srt").is_file()

    def test_skip_subtitles(self, dirs):
        downloads, base = dirs
        torrent = downloads / "Cool.Show.S01.COMPLETE"
        torrent.mkdir()
        (torrent / "Cool.Show.S01E01.mkv").touch()
        (torrent / "Cool.Show.S01E01.srt").touch()

        TVShow(title="Cool Show (2020)", path=Path("Cool.Show.S01.COMPLETE"), skip_subtitles=True).link_files()

        season = base / "TV Shows/Cool Show (2020)/Season 01"
        assert (season / "Cool Show (2020) S01E01.mkv").is_file()
        assert not (season / "Cool Show (2020) S01E01.srt").exists()

    def test_multiple_episodes_in_season(self, dirs):
        downloads, base = dirs
        torrent = downloads / "Cool.Show.S01.COMPLETE"
        torrent.mkdir()
        for ep in range(1, 4):
            (torrent / f"Cool.Show.S01E0{ep}.mkv").touch()

        TVShow(title="Cool Show (2020)", path=Path("Cool.Show.S01.COMPLETE")).link_files()

        season = base / "TV Shows/Cool Show (2020)/Season 01"
        for ep in range(1, 4):
            assert (season / f"Cool Show (2020) S01E0{ep}.mkv").is_file()

    def test_creates_hard_link_not_copy(self, dirs):
        downloads, base = dirs
        torrent = downloads / "Cool.Show.S01.COMPLETE"
        torrent.mkdir()
        source = torrent / "Cool.Show.S01E01.mkv"
        source.write_text("data")

        TVShow(title="Cool Show (2020)", path=Path("Cool.Show.S01.COMPLETE")).link_files()

        dest = base / "TV Shows/Cool Show (2020)/Season 01/Cool Show (2020) S01E01.mkv"
        assert source.stat().st_ino == dest.stat().st_ino
