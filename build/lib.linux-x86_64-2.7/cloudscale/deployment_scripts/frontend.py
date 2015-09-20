import os
import time
from cloudscale.deployment_scripts.config import AWSConfig, GoogleConfig
from cloudscale.deployment_scripts.scripts.infrastructure.aws import aws_create_keypair
from cloudscale.deployment_scripts.scripts.infrastructure.aws import aws_create_instance
from cloudscale.deployment_scripts.scripts.infrastructure.aws import aws_create_loadbalancer
from cloudscale.deployment_scripts.scripts.infrastructure.google.google_create_instance import GoogleCreateInstance
from cloudscale.deployment_scripts.scripts.infrastructure.google.google_create_load_balancer import GoogleLoadBalancer
from cloudscale.deployment_scripts.scripts.software import deploy_showcase
from cloudscale.deployment_scripts.scripts.infrastructure.aws import aws_create_ami
from cloudscale.deployment_scripts.scripts.infrastructure.aws import aws_create_autoscalability
from cloudscale.deployment_scripts.scripts.infrastructure.openstack import openstack_create_showcase_instances
from cloudscale.deployment_scripts.scripts.infrastructure.openstack import openstack_create_balancer_instance
from cloudscale.deployment_scripts.scripts.infrastructure.google.google_autoscalability import GoogleAutoscalability
from cloudscale.deployment_scripts.scripts.infrastructure.google.google_http_load_balancer import GoogleHttpLoadBalancer
from cloudscale.deployment_scripts.scripts.infrastructure.google.google_create_image import GoogleCreateImage

class Frontend:

    def __init__(self, config, logger):
        self.config = config
        self.cfg = config.cfg
        self.logger = logger

        self.instance_ids = []
        self.ip_addresses = []

        self.file_path = "/".join(os.path.abspath(__file__).split('/')[:-1])

        self.remote_deploy_path = self.cfg.get('software', 'remote_deploy_path')
        self.deploy_name = "showcase-1-a"

    def setup_aws_frontend(self):
        self.cfg = self.config.cfg

        i = aws_create_keypair.CreateKeyPair(
            config=self.config,
            user_path=self.config.user_path,
            logger=self.logger
        )
        i.create()

        self.config.save('EC2', 'key_pair', "%s/%s.pem" % (self.config.user_path, self.config.cfg.get('EC2', 'key_name')))

        self.key_pair = self.cfg.get('EC2', 'key_pair')

        config = AWSConfig(self.config, self.logger)
        showcase_url = None
        if not config.is_autoscalable:
            i = aws_create_instance.CreateEC2Instance(config=config, logger=self.logger)

            instances = i.create_all(config.num_instances)


            for instance in instances:
                self.ip_addresses.append(instance.ip_address)

            config.ip_addresses = self.ip_addresses
            loadbalancer = None
            if len(instances) > 1:
                i = aws_create_loadbalancer.CreateLoadbalancer(
                    config=config,
                    logger=self.logger
                )
                loadbalancer = i.create(instances)

            deploy_showcase.DeploySoftware(config)

            showcase_url = loadbalancer.dns_name if loadbalancer else instances[0].ip_address

        else:
            i = aws_create_instance.CreateEC2Instance(config=config, logger=self.logger)
            instance = i.create()
            self.config.save('infrastructure', 'ip_address', instance.ip_address)
            self.ip_addresses.append(instance.ip_address)

            config.ip_addresses = self.ip_addresses
            deploy_showcase.DeploySoftware(config)

            aws_create_ami.EC2CreateAMI(config=config, logger=self.logger)

            autoscalability = aws_create_autoscalability.Autoscalability(
                config=config,
                logger=self.logger
            )
            showcase_url = autoscalability.create()

        time.sleep(60)
        return showcase_url

    def setup_openstack_frontend(self):
        openstack_create_showcase_instances.CreateInstance(self.config, self.logger)
        public_ip = openstack_create_balancer_instance.CreateInstance(self.config, self.logger).get_public_ip()
        return public_ip

    def setup_google_frontend(self):
        config = GoogleConfig(self.config, self.logger)

        config.key_pair = config.config.private_key_path
        config.remote_user = config.config.remote_user
        config.database_user = config.config.db_username
        config.database_password = config.config.db_password
        config.database_name = config.config.db_name
        config.rds_num_replicas = config.config.num_replicas
        config.showcase_location = config.config.showcase_location
        config.deploy_name = self.deploy_name
        config.static_files_url = config.config.static_files_url.replace('/', '\/')
        config.connection_pool_size = config.config.connection_pool_size

        if config.config.autoscalable:
            i = GoogleCreateInstance(config, self.logger)
            instance = i.create_instance_for_autoscaling()

            config.ip_addresses = [instance['networkInterfaces'][0]['accessConfigs'][0]['natIP']]
            deploy_showcase.DeploySoftware(config)

            time.sleep(30)
            i.terminate_instance(instance['name'])
            create_image = GoogleCreateImage(config, self.logger)
            create_image.create(instance)

            autoscalability = GoogleAutoscalability(config, self.logger)
            instance_group = autoscalability.create()
            load_balancer = GoogleHttpLoadBalancer(config, self.logger)
            url = load_balancer.create(instance_group)

        else:
            i = GoogleCreateInstance(config, self.logger)
            instances = i.create()

            load_balancer = GoogleLoadBalancer(config, self.logger)
            url = load_balancer.create_load_balancer(instances)

            config.ip_addresses = [i['networkInterfaces'][0]['accessConfigs'][0]['natIP'] for i in instances]

            deploy_showcase.DeploySoftware(config)


        self.config.save('infrastructure', 'ip_addresses', ",".join(self.ip_addresses))

        return url
