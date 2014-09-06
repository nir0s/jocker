# flake8: NOQA
"""Script to run Jokcer via command line

Usage:
    jocker [--varsfile=<path> --templatefile=<string> --outputfile=<string> --build --dryrun -v]
    jocker --version

Arguments:
    generate            Generates a Dockerfile from a Jinja2 Template File
    build               Builds a Docker image from a Dockerfile

Options:
    -h --help                   Show this screen.
    -f --varsfile=<path>        Path to varsfile
    -t --templatefile=<string>  Path to Dockerfile template
    -o --outputfile=<string>    Path to output Dockerfile
    -b --build                  Whether to build or not
    -d --dryrun                 Whether to actually generate.. or just dryrun
    -v --verbose                a LOT of output
    --version                   Display current version of jocker and exit

"""

from __future__ import absolute_import
from docopt import docopt
from jocker.jocker import init_logger
from jocker.jocker import _set_global_verbosity_level
from jocker.jocker import run

lgr = init_logger()


def ver_check():
    import pkg_resources
    version = None
    try:
        version = pkg_resources.get_distribution('jocker').version
    except Exception as e:
        print(e)
    finally:
        del pkg_resources
    return version


def jocker_run(o):
    if o['generate']:
        generate(
            o['varsfile'],
            o['templatefile'],
            o['outputfile'],
            o['build'],
            o['dryrun'],
            o['verbose']
            )


def jocker(test_options=None):
    """Main entry point for script."""
    version = ver_check()
    options = test_options or docopt(__doc__, version=version)
    _set_global_verbosity_level(options.get('--verbose'))
    lgr.debug(options)
    fjocker_run(options)


def main():
    jocker()


if __name__ == '__main__':
    main()
