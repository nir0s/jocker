########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

__author__ = 'nir0s'

from jocker.jocker import _import_config
from jocker.logger import init
from jocker.jocker import _set_global_verbosity_level
from jocker.jocker import Jocker
from jocker.jocker import execute
from jocker.jocker import JockerError

import testtools
import os
from testfixtures import log_capture
import logging
import json


TEST_DIR = '{0}/test_dir'.format(os.path.expanduser("~"))
TEST_FILE_NAME = 'test_file'
TEST_FILE = TEST_DIR + '/' + TEST_FILE_NAME
TEST_RESOURCES_DIR = 'jocker/tests/resources'
MOCK_CONFIG_FILE = os.path.join(TEST_RESOURCES_DIR, 'mock_docker_config.yaml')
MOCK_VARS_FILE = os.path.join(TEST_RESOURCES_DIR, 'mock_varsfile.py')
MOCK_DOCKER_FILE = os.path.join(TEST_RESOURCES_DIR, 'mock_dockerfile')
BAD_CONFIG_FILE = os.path.join(TEST_RESOURCES_DIR, 'bad_config.py')
BAD_YAML_FILE = os.path.join(TEST_RESOURCES_DIR, 'bad_yaml.yaml')
TEST_OUTPUT_FILE = os.path.join(TEST_RESOURCES_DIR, 'test_outputfile')
TEST_JSON_STRING = \
    '{"status":"test one (len: 1)"}' \
    '{"status":"test two (len: 1)"}'


class TestBase(testtools.TestCase):

    @log_capture()
    def test_set_global_verbosity_level(self, capture):
        lgr = init(base_level=logging.INFO)

        _set_global_verbosity_level(is_verbose_output=False)
        lgr.debug('TEST_LOGGER_OUTPUT')
        capture.check()
        lgr.info('TEST_LOGGER_OUTPUT')
        capture.check(('user', 'INFO', 'TEST_LOGGER_OUTPUT'))

        _set_global_verbosity_level(is_verbose_output=True)
        lgr.debug('TEST_LOGGER_OUTPUT')
        capture.check(
            ('user', 'INFO', 'TEST_LOGGER_OUTPUT'),
            ('user', 'DEBUG', 'TEST_LOGGER_OUTPUT'))

    def test_import_config_file(self):
        outcome = _import_config(MOCK_CONFIG_FILE)
        self.assertEquals(type(outcome), dict)
        self.assertIn('client', outcome.keys())
        self.assertIn('build', outcome.keys())

    def test_fail_import_config_file(self):
        ex = self.assertRaises(RuntimeError, _import_config, '')
        self.assertEquals(str(ex), 'cannot access config file')

    def test_import_bad_config_file_mapping(self):
        ex = self.assertRaises(Exception, _import_config, BAD_CONFIG_FILE)
        self.assertIn('mapping values are not allowed here', str(ex))

    def test_import_bad_yaml_file(self):
        ex = self.assertRaises(RuntimeError, _import_config,
                               BAD_YAML_FILE)
        self.assertEquals('invalid yaml file', str(ex))

    def test_generate_dockerfile(self):
        execute(MOCK_VARS_FILE, MOCK_DOCKER_FILE, TEST_OUTPUT_FILE)
        with open(TEST_OUTPUT_FILE, 'r') as f:
            self.assertIn('git make curl', f.read())
        os.remove(TEST_OUTPUT_FILE)

    def test_dryrun(self):
        output = execute(MOCK_VARS_FILE, MOCK_DOCKER_FILE,
                         TEST_OUTPUT_FILE, dryrun=True)
        self.assertIn('git make curl', output)
        if os.path.isfile(TEST_OUTPUT_FILE):
            raise RuntimeError('test file created in dryrun...')

    def test_missing_template_file_verbose_mode(self):
        ex = self.assertRaises(
            JockerError, execute, MOCK_VARS_FILE, '', verbose=True)
        self.assertIn('template file missing', str(ex))

    def test_missing_template_file(self):
        ex = self.assertRaises(
            SystemExit, execute, MOCK_VARS_FILE, '', verbose=False)
        self.assertIn('508', str(ex))

    def test_dumb_json_output_parser(self):
        j = Jocker(MOCK_VARS_FILE, MOCK_DOCKER_FILE)
        # verify that the initial string isn't already json
        ex = self.assertRaises(ValueError, json.loads, TEST_JSON_STRING)
        self.assertTrue('Extra data', str(ex))
        output = j._parse_dumb_push_output(TEST_JSON_STRING)
        # only now test that it's been converted
        for json_obj in output:
            json.loads(json_obj)

    def test_build_or_dryrun(self):
        ex = self.assertRaises(SystemExit, execute, MOCK_VARS_FILE,
                               MOCK_DOCKER_FILE, build=True, dryrun=True)
        self.assertEquals(str(ex), str(100))

    def test_push_or_dryrun(self):
        ex = self.assertRaises(SystemExit, execute, MOCK_VARS_FILE,
                               MOCK_DOCKER_FILE, push=True, dryrun=True)
        self.assertEquals(str(ex), str(100))
