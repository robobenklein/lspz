
from pathlib import Path
import functools

import mutagen
from tqdm import tqdm

from .. import log
from .data import TrackOnDisk


class MusicLibrary():
    """Interface to a local file-based music library.

    This library MUST be properly tagged with metadata, including required:
    - MusicBrainz (MB) track ID (the primary identifier)
    - Title

    We strongly recommend also having:
    - MusicBrainz release/album id
    - Artist name and MBID
    - Chromaprint / AcoustID
    - Track replay gain (so perceived volume is normalized across samples)
    """
    track_id_tag = "MUSICBRAINZ_TRACKID"

    def __init__(self, path: Path):
        if type(path) is not Path:
            path = Path(path)
        self._path = path

    def get_supported_file_paths(self) -> TrackOnDisk:
        log.info(f"Scanning music library...")
        for path in self._path.glob("**/*.flac"):
            mf = mutagen.File(path)
            if self.track_id_tag in mf.tags:
                trackids = mf.tags[self.track_id_tag]
                if len(trackids) != 1:
                    log.warn(f"Track has multiple MBIDs: {path}")
                    continue
                length = mf.info.length
                if length < 31 or length > 3600:
                    log.debug(f"Skip track due to length {path}")
                    continue
                yield TrackOnDisk(trackids[0], path)
            else:
                log.debug(f"File does not have a track MBID {path}")

    @functools.cache
    def scan_library(self):
        return list(self.get_supported_file_paths())

    def get_mutagen_file(self, mbid):
        return mutagen.File(self.get_trackondisk_by_mbid(mbid).path)

    @functools.cache
    def get_trackondisk_by_mbid(self, mbid):
        return {
            x.mbid: x for x in self.scan_library()
        }[mbid]
