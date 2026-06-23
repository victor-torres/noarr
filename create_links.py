import os
import re
import sys
import yaml

from pathlib import Path


class Media(object):

    DOWNLOADS_DIR = Path(os.environ["DOWNLOADS_DIR"])
    BASE_DIR = Path(os.environ["BASE_DIR"])
    SUBTITLE_EXTENSIONS = {".srt",}

    def __init__(self, title: str, path: Path, skip_subtitles=False, magnet=None):
        self.title = title
        self.path = path
        self.skip_subtitles = skip_subtitles
        self.magnet = magnet

    @property
    def search_path(self) -> Path:
        return self.DOWNLOADS_DIR / self.path

    @property
    def source_paths(self) -> list[Path]:
        if self.search_path.is_file():
            return [self.search_path]

        paths = []
        for current_dir, dirs, files in os.walk(self.search_path):
            for file in files:
                if file.startswith("."):
                    continue

                path = Path(current_dir) / file
                if self.skip_subtitles and path.suffix in self.SUBTITLE_EXTENSIONS:
                    continue

                paths.append(path)

        return paths

    def link_files(self, force=False, dry_run=False):
        for source in self.source_paths:
            self._link_source_path(source, force=force, dry_run=dry_run)

    def _destination_path(self, source: Path) -> Path:
        forced = ".forced" if "forced" in source.name.lower() else ""
        return self.BASE_DIR / self.title / f"{self.title}{forced}{source.suffix}"

    def _link_source_path(self, source: Path, force=False, dry_run=False):
        destination = self._destination_path(source)
        if not destination:
            return

        if destination.exists():
            if not force:
                print(f"Destination already exists: {destination}, skipping...")
                return

            if not dry_run:
                os.remove(destination)

        print(f"Linking {source} to {destination}")
        if not dry_run:
            os.makedirs(destination.parent, exist_ok=True)
            os.link(source, destination)


class Movie(Media):

    BASE_DIR = Media.BASE_DIR / Path("Movies/")


class TVShow(Media):

    BASE_DIR = Media.BASE_DIR / Path("TV Shows/")

    def _destination_path(self, source) -> Path:
        match = re.search(r'S(\d+)E(\d+)', source.name, re.IGNORECASE)
        if not match:
            print(f"Could not extract season/episode from filename: {source.name}")
            return

        season = match.group(1).zfill(2)
        episode = match.group(2).zfill(2)

        forced = ".forced" if "forced" in source.name.lower() else ""
        return self.BASE_DIR / self.title / f"Season {season}" / f"{self.title} S{season}E{episode}{forced}{source.suffix}"


def load_library(yaml_path: Path) -> list[Media]:
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    library = []
    for entry in data.get("movies", []):
        library.append(Movie(
            title=entry["title"],
            path=Path(entry["path"]),
            skip_subtitles=entry.get("skip_subtitles", False),
            magnet=entry.get("magnet"),
        ))
    for entry in data.get("tv_shows", []):
        library.append(TVShow(
            title=entry["title"],
            path=Path(entry["path"]),
            skip_subtitles=entry.get("skip_subtitles", False),
            magnet=entry.get("magnet"),
        ))
    return library


if __name__ == "__main__":
    yaml_path = Path(__file__).parent / "library.yaml"
    library = load_library(yaml_path)

    force = "--force" in sys.argv
    dry_run = "--dry-run" in sys.argv

    for media in library:
        media.link_files(force=force, dry_run=dry_run)
