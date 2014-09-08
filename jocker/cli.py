# flake8: NOQA
"""Script to run Jokcer via command line

Usage:
    jocker [--varsfile=<path> --templatefile=<path> --outputfile=<path> --build=<string> --dryrun dockerconfig=<path> -v]
    jocker --version

Options:
    -h --help                   Show this screen.
    -f --varsfile=<path>        Path to varsfile (if omitted, will assume "vars.py")
    -t --templatefile=<path>    Path to Dockerfile template
    -o --outputfile=<path>      Path to output Dockerfile (if omitted, will assume "Dockerfile")
    -b --build=<string>         Image Repository and Tag to build
    -d --dryrun                 Whether to actually generate.. or just dryrun
    -c --dockerconfig           Path to yaml file containing docker-py configuration
    -v --verbose                a LOT of output (Note: should be used carefully..)
    --version                   Display current version of jocker and exit

"""

from __future__ import absolute_import
from docopt import docopt
from jocker.jocker import init_jocker_logger
from jocker.jocker import _set_global_verbosity_level
from jocker.jocker import run

lgr = init_jocker_logger()


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
    run(
        o.get('--varsfile'),
        o.get('--templatefile'),
        o.get('--outputfile'),
        o.get('--build'),
        o.get('--dryrun'),
        o.get('--dockerconfig'),
        o.get('--verbose')
        )


def jocker(test_options=None):
    """Main entry point for script."""
    version = ver_check()
    options = test_options or docopt(__doc__, version=version)
    _set_global_verbosity_level(options.get('--verbose'))
    lgr.debug(options)
    jocker_run(options)


def main():
    jocker()


if __name__ == '__main__':
    main()
