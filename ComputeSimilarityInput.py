# coding: utf-8

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from scipy.sparse import *
from scipy.sparse.linalg import svds

from recsys.preprocess import *
from recsys.utility import *
import sys
import os

RANDOM_STATE = 2342

np.random.seed(RANDOM_STATE)



print("Loading data")
train = pd.read_csv('data/train_final.csv', delimiter='\t')
playlists = pd.read_csv('data/playlists_final.csv', delimiter='\t')
target_playlists = pd.read_csv('data/target_playlists.csv', delimiter='\t')
target_tracks = pd.read_csv('data/target_tracks.csv', delimiter = '\t')
tracks = pd.read_csv('data/tracks_final.csv', delimiter='\t')

tracks.index = tracks['track_id']


def get_pot(train):
    pot = pd.DataFrame(train['track_id'].drop_duplicates())
    pot.index = train['track_id'].unique()
    pot['playlist_ids'] = train.groupby('track_id').apply(lambda x : x['playlist_id'].values)

    # #Take care of shitty track
    #
    # alsdkjfs = pd.DataFrame([[3626362, np.array([])]], columns=['track_id', 'playlist_ids'])
    # alsdkjfs.index = [3626362]
    # pot = pd.concat([pot, alsdkjfs], axis=0)

    return pot

def print_track(id, pot):
    t = tracks.loc[id]
    try:
        plsts = pot.loc[id]['playlist_ids']
    except KeyError:
        plsts = []

    res = []
    res.append(t['track_id'])

    album = t['album'][1:-1]
    if (album == '' or album == 'None' or album is None):
        res.append(-1)
    else:
        res.append(album)

    artist_id = t['artist_id']
    if artist_id == '':
        res.append(-1)
    else:
        res.append(artist_id)

    duration = t['duration']
    res.append(duration if duration > 0 else 0)

    playcount = t['playcount']
    try:
        res.append(int(playcount))
    except ValueError:
        res.append(0)

    tags = eval(t['tags'])
    res.append(len(tags))
    res.extend(tags)

    res.append(len(plsts))
    res.extend(plsts)
    return ' '.join(map(str, res))


def output_file(filename, pot):
    c = 0
    with open(filename, 'w') as out:
        out.write(str(len(tracks)) + '\n')
        for i in tracks.index:
            c+=1
            if c % 2000 == 0:
                print("Track {0} of {1}".format(c, len(tracks)))
            out.write(print_track(i, pot) + '\n')


def output_popular_tracks(filename):
    most_popular = get_most_popular_tracks(train)
    max_count = most_popular["count"].max()
    most_popular["count"] = most_popular["count"].apply(lambda n: n/max_count)
    most_popular_file = open(filename,"w")
    most_popular_file.write(str(len(most_popular)) + "\n")
    res = ""
    i = 0
    for _,row in most_popular.iterrows():
        i += 1
        if i % 10000 == 0:
            print(str(i) + " of " + str(len(most_popular)))
        res += str(row["track_id"]) + " " + str(row["count"]) + "\n"
    most_popular_file.write(res)
    most_popular_file.close()


def output_popular_tags(filename):
    tags = {}
    for _,row in tracks.iterrows():
        l = eval(row.tags)
        for t in l:
            if t in tags:
                tags[t] += 1
            else:
                tags[t] = 1
    sorted_tags = sorted([(k, v) for k, v in tags.items()], key=lambda tup: tup[1], reverse=True)
    max_tags = sorted_tags[0][1]
    sorted_tags = list(map(lambda tup: (tup[0], tup[1]/max_tags), sorted_tags))
    tags_popular_file = open(filename,"w")
    tags_popular_file.write(str(len(sorted_tags)) + "\n")
    res = ""
    i = 0
    for (tag, w) in sorted_tags:
        i += 1
        if i % 1000 == 0:
            print(str(i) + " of " + str(len(sorted_tags)))
        res += str(tag) + " " + str(w) + "\n"
    tags_popular_file.write(res)
    tags_popular_file.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage; {0} output_prefix [--split]")
        sys.exit(0)

    split = False
    base_name = sys.argv[1]
    if (len(sys.argv) >= 3 and sys.argv[2] == '--split'):
        split = True
        print("Splitting dataset")
        train, test, target_playlists, target_tracks = train_test_split(train, test_size=0.3, min_playlist_tracks=8)

    print("Getting pot")
    pot = get_pot(train)
    print("Printing file")
    output_file(os.path.join(base_name, "input.txt"), pot)

    print("Saving csv files")
    target_playlists.to_csv(os.path.join(base_name,  "target_playlists.csv"), index=False)
    target_tracks.to_csv(os.path.join(base_name, "target_tracks.csv"), index=False)
    train.to_csv(os.path.join(base_name, "train.csv"), index=False)
    if split:
        test.to_csv(os.path.join(base_name, "test.csv"), index=False)

    print("Getting popular tracks")
    output_popular_tracks(os.path.join(base_name, "popular_tracks.txt"))

    print("Getting popular tags")
    output_popular_tags(os.path.join(base_name, "popular_tags.txt"))

