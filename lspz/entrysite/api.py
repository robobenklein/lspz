
import re
import random
import json
from pathlib import Path

import magic
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for,
    abort, send_file, jsonify, Response
)
from bidict import bidict
import networkx as nx

from .. import log
# from .app import app
from .music_collection import MusicLibrary
from .utils import get_file_chunk

bp = Blueprint('apiv1', __name__, url_prefix='/api/v1')

re_range_header = r'(?P<unit>\w+)=(?P<start>\d+)-(?P<end>\d*)'

library = MusicLibrary(f"/home/robo/Music/music")
data_output_dir = Path("data/lspz_site_submissions")
data_output_dir.mkdir(parents=True, exist_ok=True)


def force_nocache_response(response):
    response.cache_control.max_age = 0
    response.cache_control.no_cache = True
    response.cache_control.no_store = True
    response.cache_control.must_revalidate = True

@bp.after_request
def add_cache_control_header(response):
    if 'Cache-Control' not in response.headers:
        force_nocache_response(response)
    return response

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
    log.info(f"Recording submission from {participant} ...")

    user_path = data_output_dir / participant
    user_path.mkdir(exist_ok=True)

    flat = request.form.to_dict()
    submission_dir = user_path / flat['a'] / flat['b']
    submission_dir.mkdir(parents=True, exist_ok=True)

    file = submission_dir / "submissions.jsonl"
    with file.open('ta+') as f:
        f.write(json.dumps(flat))
        f.write("\n")

    # store the data we get from humans
    return {"status": "recorded"}

### track routes:

@bp.route("/track/<mbid>.html")
def track_details_template(mbid: str):
    mf = library.get_mutagen_file(mbid)
    try:
        return render_template('trackdetails.html', data={**mf.tags})
    except Exception as e:
        log.warn({**mf.tags})
        raise e

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

@bp.route("/random/connecting_v1")
def get_connecting_tracks_v1():
    submission_files = list(data_output_dir.glob("**/submissions.jsonl"))
    def iterate_submissions():
        for file in submission_files:
            with file.open("rt") as f:
                for line in f:
                    yield json.loads(line)

    G = nx.Graph()
    for s in iterate_submissions():
        id_a = s["a"]
        id_b = s["b"]

        G.add_edge(id_a, id_b)

    comps = list(nx.connected_components(G))
    if len(comps) == 1:
        # choose a new track outside the component to compare with one in it
        in_comp = set(G.nodes)
        out_of_comp = set([x.mbid for x in library.scan_library()]) - in_comp
        if len(out_of_comp) == 0:
            # no uncompared tracks, choose some that are far apart
            # or would have low comparison confidence:
            start = random.choice(list(in_comp))
            layers = list(nx.bfs_layers(G, start))
            other = random.choice(layers[-1]) # get any node far away from start
            return [start, other]
        return [
            random.choice(list(in_comp)),
            random.choise(list(out_of_comp))
        ]
    else:
        # choose two comps at random:
        c1, c2 = random.sample(comps, 2)
        return [
            random.choice(list(c1)),
            random.choice(list(c2))
        ]

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
            trackfile, byte1, byte2, maxchunksize=2**23 # ~8MiB
        )
        file_mime = magic.from_buffer(trackfile.read(2048), mime=True)

    resp = Response(
        chunk, 206, direct_passthrough=True,
        mimetype=file_mime, content_type=file_mime,
    )
    resp.headers.add('Content-Range', f"bytes {start}-{start+length-1}/{total_size}")
    return resp
