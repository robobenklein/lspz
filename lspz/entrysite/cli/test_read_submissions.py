import argparse
import json
from collections import defaultdict

import numpy as np
from bidict import bidict

from ... import log
from ..api import data_output_dir as submissions_dir


submission_files = list(submissions_dir.glob("**/submissions.jsonl"))
# TODO filter these files

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("which_input", type=str, choices=["energy", "synthetic"])
    parser.add_argument("-v", action="store_true")
    args = parser.parse_args()
    if args.v:
        log.setLevel(log.DEBUG)
        log.info("verbose mode")

    mbid_to_idx = bidict()
    compared_with = defaultdict(lambda: defaultdict(lambda: 0))

    def iterate_submissions():
        for filepath in submission_files:
            # log.debug(f"open {filepath}")
            with filepath.open("rt") as f:
                for line in f:
                    yield json.loads(line)

    for s in iterate_submissions():
        id_a = s["a"]
        id_b = s["b"]

        for i in [id_a, id_b]:
            if i not in mbid_to_idx:
                # assign new idx to id
                mbid_to_idx[i] = len(mbid_to_idx)

        compared_with[id_a][id_b] += 1
        compared_with[id_b][id_a] += 1

    n_mbids = len(mbid_to_idx)

    # print(compared_with)

    matrix_comparisons = np.empty((n_mbids, n_mbids))
    matrix_comparisons[:] = np.nan

    for s in iterate_submissions():
        mbids = (s["a"], s["b"])
        indexes = (mbid_to_idx[mbids[0]], mbid_to_idx[mbids[1]])
        log.debug(f"update matrix [{indexes}]")

        a_vs_b = float(s[f"input_{args.which_input}"])
        pairwise = (a_vs_b, -a_vs_b)

        for mbid, idx, vs in [
                (mbids, indexes, a_vs_b),
                (mbids[::-1], indexes[::-1], -a_vs_b),
            ]:
            log.debug(f"{mbid} {idx} {vs}")
            i_a = idx[0]
            i_b = idx[1]
            if np.isnan(matrix_comparisons[i_a,i_b]):
                matrix_comparisons[i_a,i_b] = 0
            matrix_comparisons[i_a,i_b] += (vs / compared_with[mbid[0]][mbid[1]])

    print(matrix_comparisons)
