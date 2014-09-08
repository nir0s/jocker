jocker
=======

[![Build Status](https://travis-ci.org/nir0s/jocker.svg?branch=master)](https://travis-ci.org/nir0s/jocker)

[![Gitter chat](https://badges.gitter.im/nir0s/jocker.png)](https://gitter.im/nir0s/jocker)

[![PyPI](http://img.shields.io/pypi/dm/jocker.svg)](http://img.shields.io/pypi/dm/jocker.svg)

[![PypI](http://img.shields.io/pypi/v/jocker.svg)](http://img.shields.io/pypi/v/jocker.svg)

`jocker` generates [Dockerfiles](https://docs.docker.com/reference/builder/) (and optionally, Docker images) from [Jinja2](http://jinja.pocoo.org/docs/dev/) based template files.

### Requirements

- must be run sudo-ically due to Docker's sudo requirement!
- Python 2.6/2.7
- [Docker](https://www.docker.com/)

### Installation

```shell
pip install jocker
```

### Usage

```shell
jocker -h

Script to run Jokcer via command line

Usage:
    jocker [--varsfile=<path> --templatefile=<path> --outputfile=<path> --build --dryrun -v]
    jocker --version

Options:
    -h --help                   Show this screen.
    -f --varsfile=<path>        Path to varsfile (if omitted, will assume "vars.py")
    -t --templatefile=<path>    Path to Dockerfile template
    -o --outputfile=<path>      Path to output Dockerfile (if omitted, will assume "Dockerfile")
    -b --build                  Whether to build an image from the generated file or not
    -d --dryrun                 Whether to actually generate.. or just dryrun
    -v --verbose                a LOT of output (Note: should be used carefully..)
    --version                   Display current version of jocker and exit
```

More info soon...