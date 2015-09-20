from oauth2client.client import SignedJwtAssertionCredentials
import time


class GoogleHelpers():

    def __init__(self, config, logger):
        self.config = config.config
        self.logger = logger

    def login(self):
        client_email = self.config.client_email
        with open(self.config.p12_path) as f:
            private_key = f.read()

        credentials = SignedJwtAssertionCredentials(client_email, private_key,
            'https://www.googleapis.com/auth/cloud-platform')
        return credentials

    def _wait_for_operation(self, result, status='DONE'):
            if result['status'] == status:
                self.logger.log("done.")
                if 'error' in result:
                    raise Exception(result['error'])
                return result
            else:
                self.logger.log('.', append_to_last=True)
                time.sleep(1)

    def _wait_for_operation_global(self, compute, project, operation):
        self.logger.log('Waiting for operation to finish')
        while True:
            result = compute.globalOperations().get(
                    project=project,
                    operation=operation).execute()
            r = self._wait_for_operation(result)
            if not r is None:
                return r

    def _wait_for_operation_region(self, compute, project, operation, region):
        self.logger.log('Waiting for operation to finish')
        while True:
            result = compute.regionOperations().get(
                    project=project,
                    region=region,
                    operation=operation).execute()
            r = self._wait_for_operation(result)
            if not r is None:
                return r

    def _wait_for_operation_zone(self, compute, project, operation, zone):
        self.logger.log('Waiting for operation to finish')
        while True:
            result = compute.zoneOperations().get(
                    project=project,
                    zone=zone,
                    operation=operation).execute()
            r = self._wait_for_operation(result)
            if not r is None:
                return r