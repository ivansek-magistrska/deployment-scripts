import os
import urllib
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time
from cloudscale.deployment_scripts.scripts.helpers import GoogleHelpers
import json
import logging
import subprocess


class GoogleCreateSQLInstance(GoogleHelpers):

    def __init__(self, config, logger):
        GoogleHelpers.__init__(self, config, logger)
        credentials = self.login()
        self.connection = build('sqladmin', 'v1beta4', credentials=credentials)

    def create(self):
        body = {
            'name': self.config.db_instance_name,
#            'region': self.config.region,
            'settings': [
                {
                    'activationPolicy': 'ALWAYS',
                    'tier': self.config.db_tier,

                    'ipConfiguration':
                        {
                            'ipv4Enabled': True,
                            'authorizedNetworks': [
                                {
                                    'value': '0.0.0.0/0',
                                    'name': 'All'
                                }
                            ]
                        }
                }
            ]
        }
        try:
            operation = self.connection.instances().insert(project=self.config.project, body=body).execute()
            self._wait_for_operation_global(self.connection, self.config.project, operation['name'])
            self._create_user()
            self._create_database()
            self._import_database()
        except HttpError as e:
            if int(e.resp['status']) == 409:
                data = json.loads(e.content)
                self.logger.log(data['error']['message'], level=logging.ERROR)
                self.logger.log('Updating SQL instances')
                instance = self.connection.instances().get(project=self.config.project, instance=self.config.db_instance_name).execute()
                body['settings'][0]['settingsVersion'] = instance['settings']['settingsVersion']
                operation = self.connection.instances().update(
                    project=self.config.project,
                    instance=self.config.db_instance_name,
                    body=body
                ).execute()
                self._wait_for_operation_global(self.connection, self.config.project, operation['name'])
            else:
                raise e
        operation = self.connection.instances().get(project=self.config.project, instance=self.config.db_instance_name).execute()

        return operation['ipAddresses'][0]['ipAddress']

    def _import_database(self):
        try:
            body = {
                'importContext':
                    {
                    'uri': 'gs://magistrska/sql-dump',
                    'database': 'tpcw',
                    'fileType': 'SQL'
                }
            }
            operation = self.connection.instances().import_(instance=self.config.db_instance_name, project=self.config.project, body=body).execute()
            self._wait_for_operation_global(self.connection, self.config.project, operation['name'])
        except Exception as e:
            raise e

    def _create_database(self):
        body = {
            'name': 'tpcw'
        }
        try:
            operation = self.connection.databases().insert(instance=self.config.db_instance_name,
                                                       project=self.config.project,
                                                       body=body
            ).execute()
            self._wait_for_operation_global(self.connection, self.config.project, operation['name'])
        except HttpError as e:
            if int(e.resp['status']) == 409:
                data = json.loads(e.content)
                self.logger.log(data['error']['message'], level=logging.ERROR)
            else:
                raise Exception(e)

    def _create_user(self):
        body = {
            'password': self.config.db_password,
            'host': '',
            'name': self.config.db_username
        }

        try:
            time.sleep(30) # wait for instance to become available
            operation = self.connection.users().insert(project=self.config.project, instance=self.config.db_instance_name, body=body).execute()
            self._wait_for_operation_global(self.connection, self.config.project, operation['name'])
        except HttpError as e:
            if int(e.resp['status']) == 409:
                data = json.loads(e.content)
                self.logger.log(data['error']['message'], level=logging.ERROR)
            else:
                raise Exception(e)

    def import_data(self, host, username, password, db_name, dump_url):
        dump_file = "/tmp/cloudscale-dump.sql"
        if not os.path.isfile(dump_file):
            urllib.urlretrieve(dump_url, dump_file)

        cmd = [os.path.dirname(__file__) + "/../common/dump.sh", host, username, password, db_name, dump_file]
        subprocess.check_output(cmd)
        os.remove(dump_file)

    def _wait_for_operation_global(self, compute, project, operation):
        self.logger.log('Waiting for operation to finish')
        while True:
            result = compute.operations().get(
                    project=project,
                    operation=operation).execute()
            r = self._wait_for_operation(result)
            if not r is None:
                return r