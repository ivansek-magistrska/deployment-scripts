from googleapiclient.discovery import build
from cloudscale.deployment_scripts.scripts.helpers import GoogleHelpers
import traceback
import logging

class GoogleLoadBalancer(GoogleHelpers):

    def __init__(self, config, logger):
        GoogleHelpers.__init__(self, config, logger)
        self.config = config.config

        credentials = self.login()
        self.compute = build('compute', 'v1', credentials=credentials)

    def create_load_balancer(self, instances):
        # see https://cloud.google.com/compute/docs/load-balancing/network/example
        static_ip = self._create_static_ip()
        health_check = self._create_health_check()
        target_pool = self._create_target_pool(health_check, instances)
        self._create_forwarding_rule(static_ip, target_pool)
        return static_ip['address']

    def _create_forwarding_rule(self, static_ip, target_pool):
        try:
            body = {
                'name': 'cloudscale-fw-rule',
                'IPAddress': static_ip['address'],
                'IPProtocol': 'TCP',
                'portRange': '80',
                'target': target_pool['selfLink']
            }
            operation = self.compute.forwardingRules().insert(project=self.config.project,
                                                  region=self.config.region,
                                                  body=body
            ).execute()
            self._wait_for_operation_region(self.compute, self.config.project, operation['name'], self.config.region)
        except Exception as e:
            self.logger.log(traceback.format_exc().splitlines()[-1], level=logging.ERROR)


    def _create_static_ip(self):
        try:
            body = {
                'name': 'cloudscale'
            }
            operation = self.compute.addresses().insert(project=self.config.project,
                                            region=self.config.region,
                                            body=body
            ).execute()
            self._wait_for_operation_region(self.compute, self.config.project, operation['name'], self.config.region)
        except Exception as e:
            self.logger.log(traceback.format_exc().splitlines()[-1], level=logging.ERROR)

        operation = self.compute.addresses().get(project=self.config.project,
                                         region=self.config.region,
                                         address='cloudscale'
        ).execute()
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

    def _create_target_pool(self, health_check, instances):
        try:
            body = {
                'name': 'cloudscale-target-pool',
                'instances': [i['selfLink'] for i in instances],
                'healthChecks': [health_check['selfLink']]
            }
            operation = self.compute.targetPools().insert(project=self.config.project,
                                              region=self.config.region,
                                              body=body
            ).execute()
            self._wait_for_operation_region(self.compute, self.config.project, operation['name'], self.config.region)
        except Exception as e:
            self.logger.log(traceback.format_exc().splitlines()[-1], level=logging.ERROR)
        operation = self.compute.targetPools().get(project=self.config.project,
                                                 region=self.config.region,
                                                 targetPool='cloudscale-target-pool'
        ).execute()
        return operation
