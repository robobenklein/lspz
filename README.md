
# la se porganzu zgike

> The music categorizer

## Why?

I want fine grain categorization in my huge library without needing to tag every Genre and sub-genre myself, and lots of other people are in the same situation.

## Goals

Given any music file, in any format that supports metadata tags, evaluate that music for a list of Genres and sub-genres and tag that music accordingly.

Key points:

- There's no single genre for most music
- The Genres and sub-genres describing a track should naturally be a list
- Sub-genres are necessary because "Electronic", "Metal", or "Classical" are far too broad to be truly useful

Thus, datasets like GTZAN (less than a dozen genres) aren't really in-scope, since they are very broad, and often a singular person's music collection will end up entirely within one of those categories.
