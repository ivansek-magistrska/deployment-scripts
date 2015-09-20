## Deployment scripts
Deployment scripts are Python scripts for deploying showcase for master thesis on Amazon Web Services
and Google Cloud Platform. The showcase is a book store written in Java Spring Framework according to TPC-W standard. Scripts are
configurable so you ca also use them for deploying your application to Amazon Web Services or Google Cloud Platform.

## Installation
To install scripts download zip or checkout repository and then run:

```
$ python setup.py install
```

This will install deployment scripts to your ```site-packages``` folder of your Python distribution.

If you want to install it with ```pip``` you can do this by running the following command:

```
$ pip install -e https://github.com/ivansek/magistrska/deployment-scripts/zipball/deployment-scripts
```

## Usage
You can run scripts in ```cloudscale/deployment_scripts/scripts/``` as standalone or use them as part of your application. The example of using scripts as part of your
application is in ```bin/run.py``` file.

### Amazon Web Services
To deploy showcase on Amazon Web Services edit ```bin/config.aws.example.ini``` file and run:

```
$ python run.py aws config.aws.example.ini
```

### Google Cloud Platform
To deploy showcase on Google Cloud Platform edit ```bin/config.google.example.ini``` file and run:

```
$ python run.py google config.google.example.ini
```

