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

class GoogleAutoscalability(GoogleHelpers):

    def __init__(self, config, logger):
        GoogleHelpers.__init__(self, config, logger)

        credentials = self.login()
        self.compute = build('compute', 'v1', credentials=credentials)

    def create(self):
        instance_template = self._create_instance_template()
        instance_group = self._create_instances_group(instance_template)
        try:
            body = {
                'name': 'cloudscale-as',
                'target': instance_group['selfLink'],
                'autoscalingPolicy': {
                    'minNumReplicas': self.config.min_instances,
                    'maxNumReplicas': self.config.max_instances,
                    'coolDownPeriodSec': self.config.cooldown,
                    'cpuUtilization':{
                        'utilizationTarget': int(self.config.cpu_threshold)/100.0
                    }
                }
            }
            operation = self.compute.autoscalers().insert(project=self.config.project, zone=self.config.zone, body=body).execute()
            self._wait_for_operation_zone(self.compute, self.config.project, operation['name'], self.config.zone)
        except HttpError as e:
            if int(e.resp['status']) == 409:
                data = json.loads(e.content)
                self.logger.log(data['error']['message'], level=logging.ERROR)
                #self._add_instances_to_group(instances)
            else:
                raise Exception(e)

        instance_group = self.compute.instanceGroups().get(project=self.config.project,
                                              zone=self.config.zone,
                                              instanceGroup=self.config.instances_group_name).execute()
        return instance_group

    def _create_instance_template(self):
        try:
            body = {
                'name': 'cloudscale',
                'properties': {
                    'machineType': self.config.instance_type,
                    'networkInterfaces': [
                        {
                            'network': 'https://www.googleapis.com/compute/v1/projects/magistrska-1026/global/networks/default',
                            'accessConfigs': [
                                {
                                    'name': 'External NAT',
                                    'type': 'ONE_TO_ONE_NAT'
                                }
                            ]
                        }
                    ],
                    'disks': [
                        {
                            'boot': True,
                            'mode': 'READ_WRITE',
                            'autoDelete': True,
                            'initializeParams':{
                                'sourceImage':'https://www.googleapis.com/compute/v1/projects/magistrska-1026/global/images/cloudscale-autoscaling',
                                'diskType':'pd-standard',
                                'diskSizeGb': 10
                            }
                        }
                    ],
                }
            }

            operation = self.compute.instanceTemplates().insert(project=self.config.project, body=body).execute()
            self._wait_for_operation_global(self.compute, self.config.project, operation['name'])
        except HttpError as e:
            if int(e.resp['status']) == 409:
                data = json.loads(e.content)
                self.logger.log(data['error']['message'], level=logging.ERROR)
            else:
                raise Exception(e)
        operation = self.compute.instanceTemplates().get(project=self.config.project, instanceTemplate='cloudscale').execute()
        return operation

    def _add_instances_to_group(self, instances):
        try:
            body = {
                    'instances': [{'instance': i['selfLink']} for i in instances]
            }

            operation = self.compute.instanceGroups().addInstances(project=self.config.project,
                                                                  zone=self.config.zone,
                                                              instanceGroup=self.config.instances_group_name,
                                                              body=body
            ).execute()
            self._wait_for_operation_zone(self.compute, self.config.project, operation['name'], self.config.zone)
        except Exception as e:
            self.logger.log(traceback.format_exc().splitlines()[-1], level=logging.ERROR)

    def _create_instances_group(self, instance_template):
        self.logger.log('Creating instance group')
        try:
            body = {
#            'network': '',
                'baseInstanceName': self.config.instances_group_name,
                'name': self.config.instances_group_name,
                'instanceTemplate': instance_template['selfLink'],
                'targetSize': 1,
                'namedPorts': [
                    {
                        'name': 'http',
                        'port': 80
                    }
                ]
            }
            operation = self.compute.instanceGroupManagers().insert(project=self.config.project,
                                                    zone=self.config.zone,
                                                    body=body
            ).execute()
            self._wait_for_operation_zone(self.compute, self.config.project, operation['name'], self.config.zone)
            #self._add_instances_to_group(instances)

        except HttpError as e:
            if int(e.resp['status']) == 409:
                data = json.loads(e.content)
                self.logger.log(data['error']['message'], level=logging.ERROR)
                #self._add_instances_to_group(instances)
            else:
                raise Exception(e)
        operation = self.compute.instanceGroupManagers().get(project=self.config.project,
                                              zone=self.config.zone,
                                              instanceGroupManager=self.config.instances_group_name).execute()
        return operation
