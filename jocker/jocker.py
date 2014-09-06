
import jocker_config
import logging
import logging.config
import os
import sys
import datetime
from jingen.jingen import TemplateHandler
import docker

DEFAULT_BASE_LOGGING_LEVEL = logging.INFO
DEFAULT_VERBOSE_LOGGING_LEVEL = logging.DEBUG

DEFAULT_DOCKERFILE = "Dockerfile.template"
DEFAULT_VARSFILE = 'varsfile.py'
DEFAULT_OUTPUT_PATH = 'Dockerfile'


def init_logger(base_level=DEFAULT_BASE_LOGGING_LEVEL,
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
        d = os.path.dirname(logfile)
        if not os.path.exists(d) and not len(d) == 0:
            os.makedirs(d)
        logging.config.dictConfig(logging_config)
        lgr = logging.getLogger('user')
        # lgr.setLevel(base_level) if not jocker_config.VERBOSE \
        lgr.setLevel(base_level)
        return lgr
    except ValueError as e:
        sys.exit('could not initialize logger.'
                 ' verify your logger config'
                 ' and permissions to write to {0} ({1})'
                 .format(logfile, e))

lgr = init_logger()


def _set_global_verbosity_level(is_verbose_output=False):
    """sets the global verbosity level for console and the lgr logger.

    :param bool is_verbose_output: should be output be verbose
    """
    global verbose_output
    # TODO: (IMPRV) only raise exceptions in verbose mode
    verbose_output = is_verbose_output
    if verbose_output:
        lgr.setLevel(logging.DEBUG)
    else:
        lgr.setLevel(logging.INFO)
    # print 'level is: ' + str(lgr.getEffectiveLevel())


def _import_config(config_file):
    """returns a Jocker configuration object

    :param string config_file: path to config file
    """
    # get config file path
    config_file = config_file or os.path.join(os.getcwd(), DEFAULT_VARSFILE)
    lgr.debug('config file is: {}'.format(config_file))
    # append to path for importing
    sys.path.append(os.path.dirname(config_file))
    try:
        lgr.debug('importing generator dict...')
        return __import__(os.path.basename(os.path.splitext(
            config_file)[0])).VARS
    # TODO: (IMPRV) remove from path after importing
    except ImportError:
        lgr.warning('config file not found: {}.'.format(config_file))
        raise JockerError('missing config file')
    except SyntaxError:
        lgr.error('config file syntax is malformatted. please fix '
                  'any syntax errors you might have and try again.')
        raise JockerError('bad config file')


def get_current_time():
    """returns the current time (no microseconds tho)"""
    return datetime.datetime.now().replace(microsecond=0)


def run(varsfile=None, dockerfile=None, output_file=None, build=False,
        dryrun=False, verbose=False):

    template_file = dockerfile if dockerfile else DEFAULT_DOCKERFILE
    vars_source = varsfile if varsfile else DEFAULT_VARSFILE
    output_file = output_file if output_file else DEFAULT_OUTPUT_PATH
    templates_dir = os.path.dirname(template_file)
    template_file = os.path.basename(template_file)

    print '****************'
    print template_file
    print vars_source
    print output_file
    print templates_dir
    print '****************'
    i = TemplateHandler(
        template_file=template_file,
        vars_source=vars_source,
        output_file=output_file,
        templates_dir=templates_dir,
        make_file=not dryrun,
        verbose=verbose)
    output = i.generate()

    if dryrun and build:
        lgr.error('dryrun is on. cannot build.')
        raise JockerError('dryrun is on. cannot build')
    if dryrun:
        lgr.info('Potential Dockerfile Output is: \n{0}'.format(output))
        return
    if build:
        c = docker.Client(base_url='unix://var/run/docker.sock',
                          version='1.12', timeout=10)
        build_file = os.path.dirname(os.path.abspath(output_file))
        lgr.debug('building docker image from file: {0}'.format(build_file))
        x = c.build(path=build_file, tag='nir0s/jocker:test', quiet=False,
                    fileobj=None, nocache=False, rm=False, stream=True,
                    timeout=None, custom_context=False, encoding=None)
        print '*****************'
        print dir(x)
        print '*****************'

    # _verify_docker_context(ctx['context'])
    #         client = docker.Client(base_url='unix://var/run/docker.sock',
    #                                version='1.12', timeout=10)
    #         ctx['client'] = client
    #         img_repository, img_tag = ctx['context']['image'].split(':')
    #         lgr.info('pulling container from repository: {0} '
    #                  'with tag: {1}'.format(img_repository, img_tag))
    #         client.pull(img_repository, tag=img_tag, stream=False)
    #         lgr.info('creating container...')
    #         ctx['cId'] = client.create_container(**ctx['context'])['Id']
    #         print '*** container id: {0}'.format(ctx['cId'])
    #         # inspection_output = client.inspect_container(
    #         #     ctx['context']['name'])
    #         ctx['iId'] = client.commit(
    #             ctx['cId'], repository=ctx['repository'],
    #             tag=ctx.get('tag', None))['Id']
    #         print '*** image id: {0}'.format(ctx['iId'])
    #         client.remove_container(ctx['cId'])
    #         # append container to docker context dict


class JockerError(Exception):
    pass
