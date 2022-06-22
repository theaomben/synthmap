# Theaomai Synthmap Project

**TL,DR: Makes & merges 3d maps from pictures. EARLY DEVELOPMENT: Here be dragons. Works On My Machine(tm). Updates Soon(tm²).**

This repository demonstrates the Synthmap toolkit which facilitates an open, portable & shardable photogrammetric mapping workflow. It is a python package providing a backend application on top of SQLite for working with images and geo-data through command-line and HTTP interfaces. A separate project (linkme) provides an HTML5/cljs frontend GUI for visual elements and input.
The goal of the application is to index:

- Images (local, HTTP or IPFS) from which to create 3d point clouds or meshes through Structure from Motion (*SfM*).
- Entities (anything that can have static-ish coordinates or an address) to georeference or reproject the associated data.
We can then merge/shard/share the data and reuse or extend prior computations.


## Getting Started

Requires Python 3.10 (for importlib?)

```
python3 -m venv venv
source venv/bin/activate OR (on windows) venv\Scripts\activate
python3 -m pip install synthmap
# You can use the --help option on every (sub)command
cli --help
cli setup # Run this first, see --help

cli register projects --root-folder /your/sfm/projects/
cli list projects
cli list images

cli run-server   # Then point your browser to localhost:8000
```

## What does it do?

This system orchestrates the extraction of similarity and 3d information from collections of overlapping images. It keeps track of these `Images` and their data to run photogrammetric `Projects` on, via one of several backends (Colmap, AliceVision, commercial offerings...).
These backends differ slightly in the methods and formats of intermediary data but output broadly the same types of information: `Cameras`, `Images`, `Keypoints`, `Descriptors` and 3d information as various formats of point clouds or surfaces.

If a user registers an image to some known physical `Entity` (bridges, buildings, mountains, ..., anything that could have an address or coordinates), the system facilitates the propagation of this annotation to all images that have been determined to overlap the first one.

Ultimately, we end up connecting and translating the backends' output into a common representation of our `Images`, `Entities`, `Features` & `Landmarks` that constitutes a graph. We use this to subdivide and recombine our data arbitrarily, to facilitate interop and to limit redundant further calculations.

Through standardisation of these items' format, we can re-use them across projects and thus share them in order to constitute a collaborative repository of physical entities with their 2d & 3d likeness. The system ought to handle import/export in a configurable handful of common formats, and optionally use a local IPFS gateway to publish or fetch content.

This software is licensed under BSD 4-clause, see the terms in `LICENSE.md`

## Run a local dev instance

```
# Get the backend (this repo)
git clone https://github.com/theaomben/synthmap.git
cd synthmap
python3 -m venv venv
source venv/bin/activate OR (on windows) venv\Scripts\activate
(venv) pip install -r requirements-3_10_4.txt
(venv) uvicorn app.main:app --reload
...

# Optional: Format, test and check the code for possible improvements
(venv) black synthmap/
(venv) python -m pytest -v --pyargs synthmap > pytest_report.txt
(venv) python -m pylint -d C0114 -d C0115 -d C0116 -d E0401 -d E0611 -d R0903 -d C0103 -d W1203 synthmap > pylint_report.txt

# Get the frontend
git clone <frontmap repo>
apt-get install leiningen-clojure OR pacman -S leiningen OR ...
cd frontmap
lein zreload
...

```

You should now be able to point your browser to `http://localhost:8000/docs` to interact with the backend's API and `http://localhost:8000/index.html` to actually use the frontend. Edit and save any source file and the changes will be compiled and available after reloading the browser page, for the clojurescript frontend.

Looking at `synthmap.app.routers.api` or the clojurescript sort-of-html from `frontmap/src/frontmap/core.cljs` should be enough to rapidly affect simple modifications to page layout (thanks Bootstrap[0], Reagent[1]/Hiccup[2]) or the application (FastAPI[3]).

You should start by registering some local session or reconstruction folders (see `synthmap.test.sample_data`) to bootstrap your system. The CLI (`synthmap.app.cli:cli`) should present a feature complete interface for filesystem operations soon.

- [0] https://getbootstrap.com/docs/5.1/customize/overview/
- [1] https://github.com/reagent-project/reagent/
- [2] https://github.com/weavejester/hiccup/wiki/Syntax
- [3] https://fastapi.tiangolo.com/

## Support this Project

This is 80% scratch-my-own-itch and 20% portfolio-project. In any case I'd be delighted if others found use for it as well, and would love to hear about it. As a one man team I don't have the will or capacity to gatekeep an easily reproducible paid product, but would appreciate contributions if this is useful to you. The license allows you to make (commercial) use of this software provided (see `LICENSE`) that `All advertising materials mentioning features or use of this software must display the following acknowledgement: This product includes software developed by Benoît Drumain & Contributors for the Theaomai Synthmap Project.`

Input in the form of requests, comments, issues, test cases or pull requests is very welcome! In later stages:
- Configuring a local IPFS node would be a great way to contribute directly to the distribution/bandwidth/latency of the system at little cost to the user.
- Sharing pictures of user-local famous places and landmarks.
- Manually validating and extending the EntityTree.

As for pecuniary support I do not seek donations but would be happy to talk about emitting an invoice and a timeframe for feature requests, bugfixes, integrations... against this project. I'm also available for contract-work on your own projects.
Check the issue tracker (https://github.com/theaomben/synthmap/issues) or get in touch!

♡ to supporters, dependencies, prior work and research big & small. That goes double for the people around me who make this possible.

![Dependency](https://imgs.xkcd.com/comics/dependency.png)