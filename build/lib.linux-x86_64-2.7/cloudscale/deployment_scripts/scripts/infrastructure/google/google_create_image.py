
from cloudscale.deployment_scripts.scripts.helpers import GoogleHelpers

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauth2client.client import SignedJwtAssertionCredentials
import time
import logging
import json
import traceback
from cloudscale.deployment_scripts.config import GoogleConfig
from cloudscale.deployment_scripts.scripts.helpers import GoogleHelpers

class GoogleCreateImage(GoogleHelpers):

    def __init__(self, config, logger):
        GoogleHelpers.__init__(self, config, logger)

        credentials = self.login()
        self.compute = build('compute', 'v1', credentials=credentials)

    def create(self, instance, i=0):
        self.logger.log('Creating image for autoscaling')
        name = 'cloudscale-autoscaling'
        try:
            body = {
                'name' : name,
                'sourceDisk' : instance['disks'][0]['source']
            }

            operation = self.compute.images().insert(project=self.config.project, body=body).execute()
            self._wait_for_operation_global(self.compute, self.config.project, operation['name'])
        except HttpError as e:
            if int(e.resp['status']) == 409:
                data = json.loads(e.content)
                self.logger.log(data['error']['message'], level=logging.ERROR)
                operation = self.compute.images().delete(project=self.config.project, image=name).execute()
                if i == 0:
                    self._wait_for_operation_global(self.compute, self.config.project, operation['name'])
                    self.create(instance, i=i+1)
            else:
                raise Exception(e)
