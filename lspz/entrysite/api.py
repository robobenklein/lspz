
import re
import random

import magic
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for,
    abort, send_file, jsonify, Response
)

from .. import log
# from .app import app
from .music_collection import MusicLibrary
from .utils import get_file_chunk

bp = Blueprint('apiv1', __name__, url_prefix='/api/v1')

re_range_header = r'(?P<unit>\w+)=(?P<start>\d+)-(?P<end>\d*)'

library = MusicLibrary(f"/home/robo/Music/music")


### dataset routes:

@bp.route("/data/tracks")
def list_tracks():
    return {
        x.mbid: str(x.path) for x in library.scan_library()
    }

@bp.route("/data/submit-comparison", methods=['POST'])
def post_new_comparison():
    with log.verbose_logger():
        log.debug(request.headers)
        log.debug(request.form)

    participant = request.headers.get('X-Authentik-Username', 'LSPZ_NOT_AN_AUTHENTIK_USER')
    log.info(f"Submission from {participant}")
    # store the data we get from humans
    return {"status": "recorded"}

### track routes:

@bp.route("/track/<mbid>.html")
def track_details_template(mbid: str):
    mf = library.get_mutagen_file(mbid)
    return render_template('trackdetails.html', data={**mf.tags})

@bp.route("/track/<mbid>/gain")
def get_track_gain(mbid: str):
    mf = library.get_mutagen_file(mbid)
    return {
        "track": float(mf.tags['replaygain_track_gain'][0].split()[0]),
        "reference": float(mf.tags['replaygain_reference_loudness'][0].split()[0]),
    }

@bp.route("/random/tracks/<num>")
def random_track_id(num: int):
    num = int(num)
    return random.sample(
        [x.mbid for x in library.scan_library()],
        num
    )

@bp.route("/track/<mbid>/file", methods=['GET'])
def get_track_by_mbid(mbid: str):
    """Segments a file for HTTP partial-content"""

    track = library.get_trackondisk_by_mbid(mbid)

    range_header = request.headers.get('Range', None)
    byte1, byte2 = 0, None

    if range_header:
        m = re.search(re_range_header, range_header)
        # groups = match.groups()
        log.debug(f"range_header: {range_header}")

        if m.group('unit') != 'bytes':
            raise CodeChronicleError(f"cannot use Range unit {m.group('unit')}", 416)
        if m.group('start'):
            byte1 = int(m.group('start'))
        if m.group('end'):
            byte2 = int(m.group('end'))

    with track.path.open('rb') as trackfile:
        chunk, start, length, total_size = get_file_chunk(
            trackfile, byte1, byte2, maxchunksize=2**21 # ~2MiB
        )
        file_mime = magic.from_buffer(trackfile.read(2048), mime=True)

    resp = Response(
        chunk, 206, direct_passthrough=True,
        mimetype=file_mime, content_type=file_mime,
    )
    resp.headers.add('Content-Range', f"bytes {start}-{start+length-1}/{total_size}")
    return resp
