from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauth2client.client import SignedJwtAssertionCredentials
import time
import logging
import json
import traceback
from cloudscale.deployment_scripts.config import GoogleConfig
from cloudscale.deployment_scripts.scripts.helpers import GoogleHelpers


class GoogleCreateInstance(GoogleHelpers):

    def __init__(self, config, logger):
        GoogleHelpers.__init__(self, config, logger)

        credentials = self.login()
        self.compute = build('compute', 'v1', credentials=credentials)
        #self._add_ssh_keys()

    def create(self):
        if self.config.num_instances > 1:
            instances = self._create_instances()
            return instances
        else:
            instance = self._create_one_instance(1)
            return [instance]
            #self._add_firewall_rule(self.config.project)

    def _add_ssh_keys(self):
        with open(self.config.public_key_path) as fp:
            public_key = fp.read()

        body = {
            'items': [
                {
                    'attributes/sshKeys': [
                        public_key
                    ]
                }
            ]
        }
        operation = self.compute.projects().setCommonInstanceMetadata(project=self.config.project, body=body).execute()
        self._wait_for_operation_global(self.compute, self.config.project, operation['name'])
        return

    def _create_instances(self):
        #self._create_instances_group()
        instances = self._create_multiple_instances()
        #self._add_instances_to_group(instances)
        return instances



    def _create_multiple_instances(self):
        instances = []
        for i in xrange(int(self.config.num_instances)):
            instances.append(self._create_one_instance(i))

        self._add_firewall_rule(self.config.project)
        time.sleep(30)
        return instances



    def _create_one_instance(self, i):
        self.logger.log('Creating instance %s.' % (i+1))
        project = self.config.project
        zone = self.config.zone
        image = self.config.image
        instance_type = self.config.instance_type
        instance_name = '%s-%s' % (self.config.instance_name, i)
        operation = self._create_instance(image, instance_type, self.compute, project, zone, instance_name)
        return operation

    def create_instance_for_autoscaling(self):
        try:
            self._delete_disk('cloudscale-999')

            instance = self._create_one_instance(999)
            operation = self.compute.instances().setDiskAutoDelete(project=self.config.project,
                                                                   zone=self.config.zone,
                                                                   instance=instance['name'],
                                                                   autoDelete=False,
                                                                   deviceName=instance['disks'][0]['deviceName']
            ).execute()
            self._wait_for_operation_zone(self.compute, self.config.project, operation['name'], self.config.zone)

        except Exception as e:
            self.logger.log(traceback.format_exc().splitlines()[-1], level=logging.ERROR)

        operation = self.compute.instances().get(project=self.config.project, zone=self.config.zone, instance='cloudscale-999').execute()
        return operation

    def _delete_disk(self, name):
        self.logger.log('Deleting the disk with name %s' % name)
        try:
            operation = self.compute.disks().delete(project=self.config.project,
                                        disk='cloudscale-999',
                                        zone=self.config.zone
            ).execute()
            self._wait_for_operation_zone(self.compute, self.config.project, operation['name'], self.config.zone)
        except Exception as e:
            self.logger.log(traceback.format_exc().splitlines()[-1], level=logging.ERROR)

    def terminate_instance(self, name):
        try:
            operation = self.compute.instances().delete(project=self.config.project, zone=self.config.zone, instance=name).execute()
            self._wait_for_operation_zone(self.compute, self.config.project, operation['name'], self.config.zone)
        except Exception as e:
            self.logger.log(traceback.format_exc().splitlines()[-1], level=logging.ERROR)

    def _add_firewall_rule(self, project):
        try:
            firewall_rule = {
                'name': 'http-ssh',
                    'sourceRanges': ['0.0.0.0/0'],
                'allowed': [
                    {
                        'IPProtocol': 'tcp',
                        'ports': ['80', '22']
                    }
                ]
            }
            self.logger.log('Adding firewall rule for 80 and 22 ports')
            operation = self.compute.firewalls().insert(project=project, body=firewall_rule).execute()

            self._wait_for_operation_region(self.compute, self.config.project, operation['name'], self.config.region)
        except HttpError as e:
            self.logger.log(traceback.format_exc().splitlines()[-1], level=logging.ERROR)

    def _list_instances(self, compute, project, zone):
        result = compute.instances().list(project=project, zone=zone).execute()
        return result['items']

    def _create_instance(self, image, type, compute, project, zone, name):
        try:
            source_disk_image = "projects/%s/global/images/%s" % (project, image)
            machine_type = "zones/%s/machineTypes/%s" % (zone, type)
            #startup_script = open('startup-script.sh', 'r').read()
            #image_url = "http://storage.googleapis.com/gce-demo-input/photo.jpg"
            #image_caption = "Ready for dessert?"
            with open(self.config.public_key_path) as fp:
                public_key = fp.read()

            config = {
                'name': name,
                'machineType': machine_type,
                'tags': {
                    'items': ['cloudscale', 'http-server'],
                },

                # Specify the boot disk and the image to use as a source.
                'disks': [
                    {
                        'boot': True,
                        'autoDelete': True,
                        'initializeParams': {
                            'sourceImage': source_disk_image,
                        }
                    }
                ],

                # Specify a network interface with NAT to access the public
                # internet.
                'networkInterfaces': [{
                    'network': 'global/networks/default',
                    'accessConfigs': [
                        {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
                    ]
                }],

                # Allow the instance to access cloud storage and logging.
                'serviceAccounts': [{
                    'email': 'default',
                    'scopes': [
                        'https://www.googleapis.com/auth/devstorage.read_write',
                        'https://www.googleapis.com/auth/logging.write'
                    ]
                }],

                # Metadata is readable from the instance and allows you to
                # pass configuration from deployment scripts to instances.
                'metadata': {
                    'items': [
                        {
                            'key': 'sshKeys',
                            'value': public_key
                        },
                        #{
                        # Startup script is automatically executed by the
                        # instance upon startup.
                        #'key': 'startup-script',
                        # 'value': startup_script
                        # },
                    #{
                    #    'key': 'url',
                    #    'value': image_url
                    #}, {
                    #    'key': 'text',
                    #    'value': image_caption
                    #},
                    {
                        # Every project has a default Cloud Storage bucket that's
                        # the same name as the project.
                        'key': 'bucket',
                        'value': project
                    }]
                }
            }

            operation = compute.instances().insert(
                                                    project=project,
                                                    zone=zone,
                                                    body=config
            ).execute()

            self._wait_for_operation_zone(self.compute, self.config.project, operation['name'], self.config.zone)
        except Exception as e:
            self.logger.log(traceback.format_exc().splitlines()[-1], level=logging.ERROR)

        operation = self.compute.instances().get(project=project, zone=zone, instance=name).execute()
        return operation
