from cloudscale.deployment_scripts.config import GoogleConfig
from cloudscale.deployment_scripts.scripts.infrastructure.openstack import openstack_create_mysql_instances
from cloudscale.deployment_scripts.scripts.platform.aws import configure_rds
from cloudscale.deployment_scripts.scripts.platform.google.google_create_sql_instance import GoogleCreateSQLInstance
from cloudscale.deployment_scripts.scripts.infrastructure.openstack import openstack_create_mongodb_instances
class Backend:

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

    def setup_rds(self):
        configure_rds.ConfigureRDS(self.config, self.logger)

    def setup_google(self):
        config = GoogleConfig(self.config, self.logger)
        i = GoogleCreateSQLInstance(config, self.logger)
        ip = i.create()
        self.logger.log('Database instance is available at %s' % ip)
        self.logger.log('Importing dump to MySQL')
        #i.import_data(ip, self.config.db_username, self.config.db_password, self.config.db_name, self.config.db_dump_url)
        self.config.save('platform', 'urls', ip)

    def setup_openstack_mysql(self):
        openstack_create_mysql_instances.ConfigureMySQL(self.config, self.logger)

    def setup_openstack_mongodb(self):
        openstack_create_mongodb_instances.ConfigureMongodb(self.config, self.logger)