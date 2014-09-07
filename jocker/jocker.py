
import jocker_config
import logging
import logging.config
import os
import sys
from jingen.jingen import Jingen
import docker
import json
import re

DEFAULT_BASE_LOGGING_LEVEL = logging.INFO
DEFAULT_VERBOSE_LOGGING_LEVEL = logging.DEBUG

DEFAULT_DOCKERFILE = "Dockerfile.template"
DEFAULT_VARSFILE = 'varsfile.py'
DEFAULT_OUTPUT_PATH = 'Dockerfile'

DOCKER_API_VERSION = '1.14'


def init_jocker_logger(base_level=DEFAULT_BASE_LOGGING_LEVEL,
                       verbose_level=DEFAULT_VERBOSE_LOGGING_LEVEL,
                       logging_config=None):
    """initializes a base logger

    you can use this to init a logger in any of your files.
    this will use config.py's LOGGER param and logging.dictConfig to configure
    the logger for you.

    :param int|logging.LEVEL base_level: desired base logging level
    :param int|logging.LEVEL verbose_level: desired verbose logging level
    :param dict logging_dict: dictConfig based configuration.
     used to override the default configuration from config.py
    :rtype: `python logger`
    """
    if logging_config is None:
        logging_config = {}
    logging_config = logging_config or jocker_config.LOGGER
    # TODO: (IMPRV) only perform file related actions if file handler is
    # TODO: (IMPRV) defined.

    log_dir = os.path.expanduser(
        os.path.dirname(
            jocker_config.LOGGER['handlers']['file']['filename']))
    if os.path.isfile(log_dir):
        sys.exit('file {0} exists - log directory cannot be created '
                 'there. please remove the file and try again.'
                 .format(log_dir))
    try:
        logfile = jocker_config.LOGGER['handlers']['file']['filename']
        d = os.path.expanduser(os.path.dirname(logfile))
        if not os.path.exists(d) and not len(d) == 0:
            os.makedirs(d)
        logging.config.dictConfig(logging_config)
        jocker_lgr = logging.getLogger('user')
        # jocker_lgr.setLevel(base_level) if not jocker_config.VERBOSE \
        jocker_lgr.setLevel(base_level)
        return jocker_lgr
    except ValueError as e:
        sys.exit('could not initialize logger.'
                 ' verify your logger config'
                 ' and permissions to write to {0} ({1})'
                 .format(logfile, e))

jocker_lgr = init_jocker_logger()


def _set_global_verbosity_level(is_verbose_output=False):
    """sets the global verbosity level for console and the jocker_lgr logger.

    :param bool is_verbose_output: should be output be verbose
    """
    global verbose_output
    # TODO: (IMPRV) only raise exceptions in verbose mode
    verbose_output = is_verbose_output
    if verbose_output:
        jocker_lgr.setLevel(logging.DEBUG)
    else:
        jocker_lgr.setLevel(logging.INFO)
    # print 'level is: ' + str(jocker_lgr.getEffectiveLevel())


def _import_config(file_path, default=DEFAULT_VARSFILE):
    """returns an imported file object

    :param string file_path: path to file
    :param string default: default file basename (e.g. file.py)
    """
    # get file path
    file_path = file_path or os.path.join(os.getcwd(), default)
    jocker_lgr.debug('file path is: {}'.format(file_path))
    # append to path for importing
    sys.path.append(os.path.dirname(file_path))
    try:
        jocker_lgr.debug('importing file...')
        return __import__(os.path.basename(os.path.splitext(
            file_path)[0]))
    # TODO: (IMPRV) remove from path after importing
    except ImportError:
        jocker_lgr.warning('config file not found: {}.'.format(file_path))
        raise JockerError('missing config file')
    except SyntaxError:
        jocker_lgr.error('config file syntax is malformatted. please fix '
                         'any syntax errors you might have and try again.')
        raise JockerError('bad config file')


def run(varsfile=None, dockerfile=None, output_file=None, build=False,
        dryrun=False, verbose=False):

    template_file = dockerfile if dockerfile else DEFAULT_DOCKERFILE
    vars_source = varsfile if varsfile else DEFAULT_VARSFILE
    output_file = output_file if output_file else DEFAULT_OUTPUT_PATH
    templates_dir = os.path.dirname(template_file)
    template_file = os.path.basename(template_file)

    jocker_lgr.debug('template_file: {0}'.format(template_file))
    jocker_lgr.debug('vars_source: {0}'.format(vars_source))
    jocker_lgr.debug('output_file: {0}'.format(output_file))
    jocker_lgr.debug('templates_dir: {0}'.format(templates_dir))

    i = Jingen(
        template_file=template_file,
        vars_source=vars_source,
        output_file=output_file,
        templates_dir=templates_dir,
        make_file=not dryrun,
        verbose=verbose)
    output = i.generate()

    if dryrun and build:
        jocker_lgr.error('dryrun requested, cannot build.')
        raise JockerError('dryrun requested, cannot build')
    if dryrun:
        jocker_lgr.info('Potential Dockerfile Output is: \n{0}'.format(output))
        return
    if build:
        c = docker.Client(base_url='unix://var/run/docker.sock',
                          version=DOCKER_API_VERSION, timeout=10)
        build_file = os.path.dirname(os.path.abspath(output_file))
        jocker_lgr.info('building image')
        jocker_lgr.debug('building docker image from file: {0}'.format(
            build_file))
        x = c.build(path=build_file, tag='nir0s/jocker:test', quiet=False,
                    fileobj=None, nocache=False, rm=True, stream=False,
                    timeout=None, custom_context=False, encoding=None)
        # parse output. Um.. this makes 'build' work.. err.. wtf?
        jocker_lgr.info('pending build process, please hold...')
        lines = [line for line in x]
        try:
            parsed_lines = [json.loads(e).get('stream', '') for e in lines]
        except ValueError:
            # sometimes all the data is sent in a single line ????
            #
            # ValueError: Extra data: line 1 column 87 - line 1 column
            # 33268 (char 86 - 33267)
            line = lines[0]
            # This ONLY works because every line is formatted as
            # {"stream": STRING}
            parsed_lines = [
                json.loads(obj).get('stream', '') for obj in
                re.findall('{\s*"stream"\s*:\s*"[^"]*"\s*}', line)
            ]
        for line in parsed_lines:
            jocker_lgr.debug(line)
    jocker_lgr.info('Done')
    # if commit:
    #     container_id = c.create_container(**c)['Id']
    #     jocker_lgr.debug('container created with id: {0}'.format(
    #         container_id))
    #     image_id = c.commit(c['cId'], repository=c['repository'],
    #                         tag=c.get('tag', None))['Id']
    #     jocker_lgr.info('image created with id: {0}'.format(image_id))


class JockerError(Exception):
    pass
