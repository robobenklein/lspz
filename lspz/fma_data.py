
import os
import sys
import ast
import functools
from pathlib import Path
import collections

import pandas as pd
import numpy as np
import librosa

# from sklearn.preprocessing import LabelEncoder, StandardScaler
# from sklearn.model_selection import train_test_split


default_fma_data_folder = Path("data")
fma_metadata_dir = Path("fma_metadata")

# https://github.com/mdeff/fma/blob/607364e7d8263f890d23c838802f29637600611f/utils.py#L183
def load(filepath):

    filename = os.path.basename(filepath)

    if 'features' in filename:
        return pd.read_csv(filepath, index_col=0, header=[0, 1, 2])

    if 'echonest' in filename:
        return pd.read_csv(filepath, index_col=0, header=[0, 1, 2])

    if 'genres' in filename:
        return pd.read_csv(filepath, index_col=0)

    if 'tracks' in filename:
        tracks = pd.read_csv(filepath, index_col=0, header=[0, 1])

        COLUMNS = [('track', 'tags'), ('album', 'tags'), ('artist', 'tags'),
                   ('track', 'genres'), ('track', 'genres_all')]
        for column in COLUMNS:
            tracks[column] = tracks[column].map(ast.literal_eval)

        COLUMNS = [('track', 'date_created'), ('track', 'date_recorded'),
                   ('album', 'date_created'), ('album', 'date_released'),
                   ('artist', 'date_created'), ('artist', 'active_year_begin'),
                   ('artist', 'active_year_end')]
        for column in COLUMNS:
            tracks[column] = pd.to_datetime(tracks[column])

        SUBSETS = ('small', 'medium', 'large')
        try:
            tracks['set', 'subset'] = tracks['set', 'subset'].astype(
                    'category', categories=SUBSETS, ordered=True)
        except (ValueError, TypeError):
            # the categories and ordered arguments were removed in pandas 0.25
            tracks['set', 'subset'] = tracks['set', 'subset'].astype(
                     pd.CategoricalDtype(categories=SUBSETS, ordered=True))

        COLUMNS = [('track', 'genre_top'), ('track', 'license'),
                   ('album', 'type'), ('album', 'information'),
                   ('artist', 'bio')]
        for column in COLUMNS:
            tracks[column] = tracks[column].astype('category')

        return tracks

class FMAData():
    def __init__(self, base_path: Path = default_fma_data_folder):
        self.base_path = base_path

    @functools.cached_property
    def tracks(self):
        return load(self.base_path / fma_metadata_dir / "tracks.csv")

    @functools.cached_property
    def genres(self):
        return load(self.base_path / fma_metadata_dir / "genres.csv")

    @functools.cached_property
    def tracks_with_genre_top(d):
        return d.tracks[d.tracks['track']['genre_top'].notna()]

    @functools.cached_property
    def tracks_with_genres(d):
        return d.tracks[d.tracks['track']['genres'].notna()]

    @functools.cached_property
    def classes_top(d):
        return self.tracks_with_genre_top['track']['genre_top'].unique()

    @functools.cached_property
    def track_genres_labels(d):
        def f_g(k):
            nd = {}
            for gid, _ in k.items():
                nd[d.genre_name_from_id(gid)] = 1
            return nd
        cc = d.tracks_with_genres['track']['genres'].apply(collections.Counter)
        tg = cc.apply(f_g)
        return tg.apply(pd.Series).fillna(0)

    def genres_for_track(self, track_id: int):
        genres = self.tracks.loc[20]['track']['genres']
        return map(self.genre_name_from_id, genres)

    @functools.cache
    def files_in(self, subset: str):
        """List files in a data subset: small, medium, large, full

        Returns List[Path] in numerically sorted order
        """
        subset_path = self.base_path / f"fma_{subset}"
        if not subset_path.is_dir():
            raise ValueError(f"FMA data subset was not found: {subset_path}")
        files = list(subset_path.glob("*/*"))
        files.sort()
        return files

    def genre_id_from_name(d, name: str):
        return d.genres.index[d.genres['title'] == name].item()

    @functools.cache
    def genre_name_from_id(self, id: int):
        return self.genres.loc[id]['title']

data = FMAData(Path(os.environ.get("LSPZ_FMA_DATA_DIR", default_fma_data_folder)))

if __name__ == '__main__':
    base_path = Path(sys.argv[1] if len(sys.argv) > 1 else default_fma_data_folder)

    metadata = data

    print(f"Genres:")
    print(metadata.genres)
    print(f"Tracks:")
    print(metadata.tracks)
    print(f"Tracks with Genres:")
    print(metadata.track_genres_labels)
