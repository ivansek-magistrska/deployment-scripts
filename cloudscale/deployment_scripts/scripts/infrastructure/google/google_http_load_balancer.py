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

class GoogleHttpLoadBalancer(GoogleHelpers):

    def __init__(self, config, logger):
        GoogleHelpers.__init__(self, config, logger)

        credentials = self.login()
        self.compute = build('compute', 'v1', credentials=credentials)

    def create(self, instance_group):
        health_check = self._create_health_check()
        backend_service = self._create_backend_service(health_check, instance_group)
        url_map = self._create_url_map(backend_service)
        target_http_proxy = self._create_target_http_proxy(url_map)
        static_ip = self._create_static_ip()
        global_forwarding_rule = self._create_global_forwarding_rule(target_http_proxy, static_ip)
        return static_ip['address']

    def _create_url_map(self, backend_service):
        self.logger.log('Creating url map')
        name = 'cloudscale-url-map'
        try:
            body = {
                'name': name,
                'defaultService': backend_service['selfLink']
            }

            operation = self.compute.urlMaps().insert(project=self.config.project, body=body).execute()
            self._wait_for_operation_global(self.compute, self.config.project, operation['name'])
        except Exception as e:
            self.logger.log(traceback.format_exc().splitlines()[-1], level=logging.ERROR)
        operation = self.compute.urlMaps().get(project=self.config.project, urlMap=name).execute()
        return operation

    def _create_backend_service(self, health_check, instance_group):
        self.logger.log('Creating backend service')
        name = 'cloudscale-backend-service'
        try:
            body = {
                'name': name,
                'backends': [
                    {
                        'group': instance_group['selfLink']
                    }
                ],
                'healthChecks': [health_check['selfLink']],
            }

            operation = self.compute.backendServices().insert(project=self.config.project, body=body).execute()
            self._wait_for_operation_global(self.compute, self.config.project, operation['name'])
        except Exception as e:
            self.logger.log(traceback.format_exc().splitlines()[-1], level=logging.ERROR)
        operation = self.compute.backendServices().get(project=self.config.project, backendService=name).execute()
        return operation

    def _create_health_check(self):
        self.logger.log('Creating health check')

        try:
            body = {
                'name': 'cloudscale-health-check',
                'port': 80,
                'requestPath': '/',
                'checkIntervalSec': 5,
                'unhealthyThreshold': 2,
                'healthyThreshold': 2,
                'timeoutSec': 5,
            }

            operation = self.compute.httpHealthChecks().insert(project=self.config.project, body=body).execute()
            self._wait_for_operation_global(self.compute, self.config.project, operation['name'])
        except Exception as e:
            self.logger.log(traceback.format_exc().splitlines()[-1], level=logging.ERROR)
        operation = self.compute.httpHealthChecks().get(project=self.config.project, httpHealthCheck='cloudscale-health-check').execute()
        return operation

    def _create_target_http_proxy(self, url_map):
        name = 'cloudscale-target-http-proxy'
        try:
            body = {
                'name': name,
                'urlMap': url_map['selfLink']
            }
            operation = self.compute.targetHttpProxies().insert(project=self.config.project,
                                            body=body
            ).execute()
            self._wait_for_operation_global(self.compute, self.config.project, operation['name'])
        except Exception as e:
            self.logger.log(traceback.format_exc().splitlines()[-1], level=logging.ERROR)

        operation = self.compute.targetHttpProxies().get(project=self.config.project,
                                         targetHttpProxy=name
        ).execute()
        return operation

    def _create_global_forwarding_rule(self, target_http_proxy, static_ip):
        name = 'cloudscale-global-forwarding-rule'
        try:
            body = {
                'name': name,
                'portRange': 80,
                'IPAddress': static_ip['address'],
                'IPProtocol': 'TCP',
                'target': target_http_proxy['selfLink']
            }
            operation = self.compute.globalForwardingRules().insert(project=self.config.project,
                                                              body=body
            ).execute()
            self._wait_for_operation_global(self.compute, self.config.project, operation['name'])
        except Exception as e:
            self.logger.log(traceback.format_exc().splitlines()[-1], level=logging.ERROR)

        operation = self.compute.globalForwardingRules().get(project=self.config.project,
                                         forwardingRule=name
        ).execute()
        return operation

    def _create_static_ip(self):
        self.logger.log('Creating global static IP address')
        name = 'cloudscale-as'
        try:
            body = {
                'name': name
            }
            operation = self.compute.globalAddresses().insert(project=self.config.project,
                                            body=body
            ).execute()
            self._wait_for_operation_global(self.compute, self.config.project, operation['name'])
        except Exception as e:
            self.logger.log(traceback.format_exc().splitlines()[-1], level=logging.ERROR)

        operation = self.compute.globalAddresses().get(project=self.config.project,
                                         address=name
        ).execute()
        return operation