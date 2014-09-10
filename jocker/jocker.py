import logger
import logging
import os
import sys
from jingen.jingen import Jingen
import docker
import json
import re
import yaml
import socket


DEFAULT_CONFIG_FILE = os.path.expanduser('~/.jocker/config.yml')
DEFAULT_TEMPLATEFILE = 'Dockerfile.template'
DEFAULT_VARSFILE = 'varsfile.py'
DEFAULT_OUTPUTFILE = 'Dockerfile'

DEFAULT_DOCKER_CONFIG = {
    'client': {
        'base_url': 'unix://var/run/docker.sock',
        'version': '1.14',
        'timeout': 10
    },
    'build': {
        'quiet': False,
        'fileobj': None,
        'nocache': False,
        'rm': True,
        'stream': False,
        'timeout': None,
        'custom_context': False,
        'encoding': None
    }
}

jocker_lgr = logger.init()
verbose_output = False


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


def _import_config(config_file):
    """returns a configuration object

    :param string config_file: path to config file
    """
    # get config file path
    config_file = config_file or os.path.join(os.getcwd(), DEFAULT_CONFIG_FILE)
    jocker_lgr.debug('config file is: {}'.format(config_file))
    # append to path for importing
    try:
        jocker_lgr.debug('importing config...')
        with open(config_file, 'r') as c:
            return yaml.safe_load(c.read())
    except IOError as ex:
        jocker_lgr.error(str(ex))
        raise RuntimeError('cannot access config file')
    except ImportError:
        jocker_lgr.warning('config file not found: {}.'.format(config_file))
        raise RuntimeError('missing config file')
    except SyntaxError:
        jocker_lgr.error('config file syntax is malformatted. please fix '
                         'any syntax errors you might have and try again.')
        raise RuntimeError('bad config file')


def run(varsfile, templatefile, outputfile, configfile=None,
        dryrun=False, build=False, push=False, verbose=False):
    """generates a Dockerfile, builds an image and pushes it to Dockerhub

    A `Dockerfile` will be generated by Jinja2 according to the `varsfile`
    imported. If build is not false, an image will be generated from the
    `outputfile` which is the generated Dockerfile and committed to the
    image:tag string supplied to `build`.

    :param string varsfile: path to file with variables.
    :param string templatefile: path to template file to use.
    :param string outputfile: path to output Dockerfile.
    :param string configfile: path to yaml file with docker-py config.
    :param bool dryrun: mock run.
    :param build: False or the image:tag to build to.
    :param push: False or the image:tag to build to. (triggers build)
    :param bool verbose: verbose output.
    """
    if dryrun and (build or push):
        jocker_lgr.error('dryrun requested, cannot build.')
        sys.exit(100)

    _set_global_verbosity_level(verbose)
    j = Jocker(varsfile, templatefile, outputfile, configfile, dryrun,
               build, push)
    formatted_text = j.generate_dockerfile()
    if dryrun:
        return j.handle_dryrun(formatted_text)
    if build or push:
        j.handle_build()
    if push:
        j.handle_push()


class Jocker():

    def __init__(self, varsfile, templatefile, outputfile, configfile=None,
                 dryrun=False, build=False, push=False):
        self.varsfile = varsfile if varsfile else DEFAULT_VARSFILE
        self.templatefile = templatefile if templatefile \
            else DEFAULT_TEMPLATEFILE
        self.outputfile = outputfile if outputfile else DEFAULT_OUTPUTFILE
        self.configfile = configfile
        self.dryrun = dryrun
        self.build = build
        self.push = push

        docker_config = _import_config(configfile) if configfile \
            else DEFAULT_DOCKER_CONFIG
        self.client_config = docker_config.get(
            'client', DEFAULT_DOCKER_CONFIG['client'])
        self.build_config = docker_config.get(
            'build', DEFAULT_DOCKER_CONFIG['build'])

        if not os.path.exists(self.templatefile):
            jocker_lgr.error('template file does not exist in {0}'.format(
                self.templatefile))
            if verbose_output:
                raise JockerError('template file missing')
            sys.exit(508)
        self.template_dir = os.path.dirname(self.templatefile)
        self.template_file = os.path.basename(self.templatefile)

    def _parse_dumb_push_output(self, string):
        """since the push process outputs a single unicode string consisting of
        multiple JSON formatted "status" lines, we need to parse it so that it
        can be read as multiple strings.

        This will receive the string as an input, count curly braces and ignore
        any newlines. When the curly braces stack is 0, it will append the
        entire string it has read up until then to a list and so forth.

        :param string: the string to parse
        :rtype: list of JSON's
        """
        stack = 0
        json_list = []
        tmp_json = ''
        for char in string:
            if not char == '\r' and not char == '\n':
                tmp_json += char
            if char == '{':
                stack += 1
            elif char == '}':
                stack -= 1
            if stack == 0:
                if not len(tmp_json) == 0:
                    json_list.append(tmp_json)
                tmp_json = ''
        return json_list

    def generate_dockerfile(self):

        if not self.dryrun:
            jocker_lgr.info('generating Dockerfile: {0}'.format(
                os.path.abspath(self.outputfile)))
        jocker_lgr.debug('template file: {0}'.format(self.template_file))
        jocker_lgr.debug('vars source: {0}'.format(self.varsfile))
        jocker_lgr.debug('template dir: {0}'.format(self.template_dir))

        i = Jingen(
            template_file=self.template_file,
            vars_source=self.varsfile,
            output_file=self.outputfile,
            template_dir=self.template_dir,
            make_file=not self.dryrun)
        formatted_text = i.generate()
        jocker_lgr.debug('Output content: \n{0}'.format(formatted_text))
        if not self.dryrun:
            jocker_lgr.info('Dockerfile generated')
        return formatted_text

    def handle_dryrun(self, text):
        jocker_lgr.info(
            'dryrun requested, potential Dockerfile content is: \n{0}'.format(
                text))

    def handle_build(self):
        try:
            # define repository and tag for image
            self.repository, self.tag = self.build.split(':') if self.build \
                else self.push.split(':')
        except ValueError:
            # maybe tag wasn't supplied...
            self.repository = self.build if self.build else self.push
            self.tag = None
        jocker_lgr.debug('initializing docker client with config: {0}'.format(
            self.client_config))
        self.c = docker.Client(**self.client_config)
        build_path = os.path.dirname(os.path.abspath(self.outputfile))
        jocker_lgr.info('Creating Image: {0}:{1}'.format(
            self.repository, self.tag))
        jocker_lgr.debug('building docker image from file: {0}'.format(
            os.path.join(build_path, self.outputfile)))
        jocker_lgr.debug('Docker build config is: {0}'.format(
            self.build_config))
        try:
            build_results = self.c.build(
                path=build_path, tag=self.build or self.push,
                **self.build_config)
        except Exception as e:
            jocker_lgr.error('failed to generate image ({0})'.format(e))

        # parse output. Um.. this parser makes 'build' work.. err.. wtf?
        jocker_lgr.info('waiting for build process to finish, please hold...')
        lines = [line for line in build_results]
        try:
            parsed_lines = [json.loads(i).get('stream', '') for i in lines]
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
        # TODO: (IMPRV) verify image exists
        jocker_lgr.info('image generation complete')

    def handle_push(self):
        jocker_lgr.info('pushing {0}:{1}'.format(self.repository, self.tag))
        try:
            push_results = self._parse_dumb_push_output(
                self.c.push(self.repository, tag=self.tag, stream=False))
        except docker.errors.APIError as e:
            jocker_lgr.error(e)
            if verbose_output:
                raise JockerError(e)
            sys.exit(500)
        except socket.timeout as e:
            jocker_lgr.error(e)
            if verbose_output:
                raise JockerError(e)
            sys.exit(408)
        for line in push_results:
            jocker_lgr.debug(json.loads(line))
        jocker_lgr.info('push complete')
        # TODO: (IMPRV) handle additional errors - see errorslog file


class JockerError(Exception):
    pass
