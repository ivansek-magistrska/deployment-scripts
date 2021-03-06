from distutils.core import setup
from setuptools import find_packages

setup(
    name='cloudscale-deployment-scripts',
    version='0.1.0',
    author='Simon Ivansek',
    author_email='simon.ivansek@xlab.si',
    packages=find_packages(),
    package_data={'' : ['*.cfg', '*.sh', '*.conf']},
    license='LICENSE.txt',
    description='Deployment scripts for master thesis',
    long_description=open('README.txt').read(),
    include_package_data=True,
    install_requires=[
        "boto==2.36.0",
        "google-api-python-client==1.4.1",
    ],
)