jocker
======

|Build Status|

|Gitter chat|

|PyPI|

|PypI|

``jocker`` generates Dockerfiles (and optionally, Docker images) from
Jinja2 based template files.

Usage
~~~~~

.. code:: shell

    jocker -h

    Script to run Jokcer via command line

    Usage:
        jocker [--varsfile=<path> --templatefile=<path> --outputfile=<path> --build --dryrun -v]
        jocker --version

    Options:
        -h --help                   Show this screen.
        -f --varsfile=<path>        Path to varsfile
        -t --templatefile=<path>    Path to Dockerfile template
        -o --outputfile=<path>      Path to output Dockerfile
        -b --build                  Whether to build or not
        -d --dryrun                 Whether to actually generate.. or just dryrun
        -v --verbose                a LOT of output
        --version                   Display current version of jocker and exit

More info soon...

.. |Build Status| image:: https://travis-ci.org/nir0s/jocker.svg?branch=develop
   :target: https://travis-ci.org/nir0s/jocker
.. |Gitter chat| image:: https://badges.gitter.im/nir0s/jocker.png
   :target: https://gitter.im/nir0s/jocker
.. |PyPI| image:: http://img.shields.io/pypi/dm/jocker.svg
   :target: http://img.shields.io/pypi/dm/jocker.svg
.. |PypI| image:: http://img.shields.io/pypi/v/jocker.svg
   :target: http://img.shields.io/pypi/v/jocker.svg
