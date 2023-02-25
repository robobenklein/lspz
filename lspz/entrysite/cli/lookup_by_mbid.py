
import argparse

from ..music_collection import MusicLibrary

library = MusicLibrary(f"/home/robo/Music/music")

default_tags_to_show = [
    "title", "artist", "album",
    "replaygain_track_gain", "replaygain_album_gain",
]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mbid", nargs="+")
    parser.add_argument("-j", "--json", action="store_true", help="Output json lines")

    args = parser.parse_args()

    for mbid in args.mbid:
        if args.json:
            raise NotImplementedError()
        else:
            track = library.get_trackondisk_by_mbid(mbid)
            mf = library.get_mutagen_file(mbid)
            print(f"Details for {mbid}:")
            print(f"  \"{track.path}\"")
            for tag in default_tags_to_show:
                tval = mf.tags.get(tag, None)
                print(f"  {tag}: {tval}")
