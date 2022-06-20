# Theaomai Synthmap Project

    θεάομαι:
        gaze at, behold, mostly with a sense of wonder
        voir, regarder attentivement, contempler

*This is a personal project which I intend to develop in the open for my own usage, and hopefully for anyone else who may find it useful. It is in very early stages and important elements are yet missing or might change. See "Support this Project" towards the end of this document.*

**TL,DR: Makes & merges 3d maps from pictures. PRE-ALPHA RELEASE: Here be dragons. Works On My Machine(tm). Updates Soon(tm²).**

This package is a backend python application for working with images and geo-data through command-line and HTTP interfaces. A separate project (linkme) provides an HTML5/cljs frontend GUI for visual elements and input.
The goal of the application is to index

- Images (local, HTTP or IPFS) from which to create 3d point clouds or meshes through Structure from Motion (*SfM*).
- Entities (anything that can have static-ish coordinates or an address) to georeference or reproject the associated data.
We can then merge/shard/share the data and reuse or extend prior computations.


## Getting Started

```
python3 -m pip install synthmap
synthmap setup  # You can use the --help option on synthmap and every subcommand

synthmap register projects --root-folder /your/sfm/projects/
synthmap list projects
synthmap list images

synthmap start-server   # Point your browser to localhost:8000
```


## Support this Project

This is 80% scratch-my-own-itch and 20% portfolio-project. In any case I'd be delighted if others found use for it as well (I want to talk with you!). Ergo distribution under the terms of BSD 4-clause, see LICENSE. As a one man team I don't have the will or capacity to gatekeep an easily reproducible paid product, but would appreciate contributions if this is useful to you.

Input in the form of requests, comments, issues, test cases or pull requests is very welcome! In later stages:
- Configuring a local IPFS node would be a great way to contribute directly to the distribution/bandwidth/latency of the system at little cost to the user.
- Sharing pictures of user-local famous places and landmarks.
- Manually validating and extending the EntityTree.

As for pecuniary support I do not seek donations but would be happy to talk about emitting an invoice and a timeframe for feature requests, bugfixes, integrations... against this project. I'm also available for contract-work on your own projects.
Check the issue tracker (linkme) or get in touch!

♡ to supporters, dependencies or prior work/research big and small. That goes double for the people around me who make this possible.

![Dependency](https://imgs.xkcd.com/comics/dependency.png)