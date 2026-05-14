---
name: geocode-count-check
description: When multiple results are returned by calling `gis_geocode`, confirm the unique location
compatibility: opencode
metadata:
  audience: users
  workflow: gis
---

## When to use me

After calling `gis_geocode`

## What I do

When the `gis_geocode` function returns a `count` greater than 1 and the two locations are far apart, ask the user to confirm the location further. 

If the distances of multiple results are relatively close, say within a few dozen meters, then the most suitable one can be chosen.

