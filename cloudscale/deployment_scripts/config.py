import novaclient
from oauth2client.client import SignedJwtAssertionCredentials
from cloudscale.deployment_scripts.scripts import read_config, create_user_path

class Config:

    def __init__(self, infrastructure, output_directory, config_path):
        self.provider = infrastructure
        self.config_path = config_path
        self.user_path = create_user_path(output_directory)
        self.cfg = read_config(self.config_path)

    def save(self, section, variable, value):
        self.cfg.save_option(self.config_path, section, variable, str(value))

class AWSConfig:

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.cfg = config.cfg

        self.read_config()

    def read_config(self):
        self.showcase_location      = self.cfg.get('APPLICATION', 'distribution_url')
        self.connection_pool_size   = self.cfg.get('APPLICATION', 'connection_pool_size')
        self.access_key             = self.cfg.get('AWS', 'aws_access_key_id')
        self.secret_key             = self.cfg.get('AWS', 'aws_secret_access_key')
        self.region                 = self.cfg.get('AWS', 'region')
        self.availability_zone      = self.cfg.get('AWS', 'availability_zone')
        self.instance_type          = self.cfg.get('EC2', 'instance_type')
        self.ami_id                 = self.cfg.get('EC2', 'ami_id')
        self.key_name               = self.cfg.get('EC2', 'key_name')
        self.key_pair               = self.cfg.get('EC2', 'key_pair')
        self.remote_user            = self.cfg.get('EC2', 'remote_user')
        self.instance_identifier    = self.cfg.get('EC2', 'instance_identifier')
        self.num_instances          = int(self.cfg.get('APPLICATION', 'num_instances'))
        self.cooldown               = int(self.cfg.get('AUTO_SCALABILITY', 'cooldown'))
        self.is_autoscalable        = self.cfg.get('AUTO_SCALABILITY', 'enabled')
        self.is_autoscalable        = self.is_autoscalable == 'yes'
        self.database_name          = self.cfg.get('DATABASE', 'name')
        self.database_user          = self.cfg.get('DATABASE', 'user')
        self.database_password      = self.cfg.get('DATABASE', 'password')
        self.database_dump_url      = self.cfg.get('DATABASE', 'dump_url')
        self.rds_instance_type      = self.cfg.get('RDS', 'instance_type')
        self.rds_num_replicas       = int(self.cfg.get('RDS', 'num_replicas'))
        self.rds_master_identifier  = self.cfg.get('RDS', 'master_identifier')
        self.rds_replica_identifier = self.cfg.get('RDS', 'replica_identifier')
        self.static_files_url       = self.cfg.get('APPLICATION', 'static_files_url')
        self.deploy_name            = 'showcase-1-a'
        self.ip_addresses           = []

class OpenstackConfig:
    def __init__(self, config, logger):
        self.logger = logger
        self.config = config
        self.cfg = config.cfg

        self.read_config()

        self.nc = novaclient.Client(self.user, self.pwd, self.tenant, auth_url=self.url)

    def read_config(self):
        self.user                       = self.cfg.get('OPENSTACK', 'username')
        self.pwd                        = self.cfg.get('OPENSTACK', 'password')
        self.url                        = self.cfg.get('OPENSTACK', 'auth_url')
        self.tenant                     = self.cfg.get('OPENSTACK', 'tenant_name')
        self.image_name                 = self.cfg.get('APPLICATION', 'image_name')
        self.remote_user                = self.cfg.get('APPLICATION', 'image_username')

        self.instance_type              = self.cfg.get('APPLICATION', 'instance_type')

        self.num_instances              = self.cfg.get('APPLICATION', 'num_instances')
        self.key_name                   = self.cfg.get('OPENSTACK', 'key_name')
        self.key_pair                   = self.cfg.get('OPENSTACK', 'key_pair')

        self.database_type              = self.cfg.get('DATABASE', 'database_type').lower()
        self.database_instance_type     = self.cfg.get('DATABASE', 'instance_type')
        self.database_num_replicas      = self.cfg.get('DATABASE', 'num_replicas')
        self.database_name              = self.cfg.get('DATABASE', 'database_name')
        self.database_user              = self.cfg.get('DATABASE', 'database_user')
        self.database_pass              = self.cfg.get('DATABASE', 'database_pass')
        self.connection_pool_size       = self.cfg.get('DATABASE', 'connection_pool_size')
        self.mongo_image_name           = self.cfg.get('MONGODB', 'image_name')
        self.mysql_setup_type           = self.cfg.get('MYSQL', 'setup_type')
        self.mysql_image_name           = self.cfg.get('MYSQL', 'image_name')
        self.showcase_url               = self.get_showcase_url()
        self.dump_url                   = self.get_dump_url()


    def get_dump_url(self):
        if self.database_type == 'mysql':
            return self.cfg.get('MYSQL', 'dump_url')
        elif self.database_type == 'mongodb' or self.database_type == 'mongo':
            return self.cfg.get('MONGODB', 'dump_url')
        else:
            raise Exception("Wrong database type!")

    def get_showcase_url(self):
        if self.database_type == 'mysql':
            return self.cfg.get('MYSQL', 'showcase_url')
        elif self.database_type == 'mongodb' or self.database_type == 'mongo':
            return self.cfg.get('MONGODB', 'showcase_url')
        else:
            raise Exception("Wrong database type!")

class GoogleConfig:
    def __init__(self, config, logger):
        self.logger = logger
        self.config = config

        self.cfg = config.cfg

        self.read_config()

    def read_config(self):
        self.config.client_email = self.cfg.get('CREDENTIALS', 'client_email')
        self.config.p12_path = self.cfg.get('CREDENTIALS', 'p12_path')
        self.config.json_file = self.cfg.get('CREDENTIALS', 'json_file')

        self.config.num_instances = self.cfg.get('INSTANCES', 'num_instances')
        self.config.zone = self.cfg.get('INSTANCES', 'zone')
        self.config.instance_type = self.cfg.get('INSTANCES', 'instance_type')
        self.config.image = self.cfg.get('INSTANCES', 'image')
        self.config.project = self.cfg.get('INSTANCES', 'project')
        self.config.instance_name = self.cfg.get('INSTANCES', 'instance_name')
        self.config.instances_group_name = self.cfg.get('INSTANCES', 'instances_group_name')
        self.config.region = self.cfg.get('INSTANCES', 'region')
        self.config.public_key_path = self.cfg.get('INSTANCES', 'public_key_path')
        self.config.private_key_path = self.cfg.get('INSTANCES', 'private_key_path')
        self.config.remote_user = self.cfg.get('INSTANCES', 'remote_user')

        self.config.db_tier = self.cfg.get('DATABASE', 'tier')
        self.config.db_instance_name = self.cfg.get('DATABASE', 'instance_name')
        self.config.db_dump_url = self.cfg.get('DATABASE', 'dump_url')
        self.config.db_username = self.cfg.get('DATABASE', 'username')
        self.config.db_password = self.cfg.get('DATABASE', 'password')
        self.config.db_name = self.cfg.get('DATABASE', 'database')
        self.config.num_replicas = self.cfg.get('DATABASE', 'num_replicas')

        self.config.showcase_location = self.cfg.get('APPLICATION', 'showcase_location')
        self.config.connection_pool_size = self.cfg.get('APPLICATION', 'connection_pool_size')
        self.config.static_files_url = self.cfg.get('APPLICATION', 'static_files_url')

        self.config.autoscalable = self.cfg.get('AUTOSCALABILITY', 'enabled')
        self.config.autoscalable = True if self.config.autoscalable == 'yes' else False
        self.config.cooldown = self.cfg.get('AUTOSCALABILITY', 'cooldown')
        self.config.min_instances = self.cfg.get('AUTOSCALABILITY', 'min_instances')
        self.config.max_instances = self.cfg.get('AUTOSCALABILITY', 'max_instances')
        self.config.cpu_threshold = self.cfg.get('AUTOSCALABILITY', 'cpu_threshold')


