# Overview

This NApp integrates Kafka with the Kytos SDN platform to enable event-driven messaging and real-time event streaming.

# Planned Features

- Asynchronous Kafka producer with support for compression and acknowledgments.
- Event listener for new KytosEvents, which then serializes and publishes events to Kafka.
- Resilient Kafka client with automatic retries for connectivity issues.
- Uses Main asyncio loop to handle asynchronous tasks serialization and publishing.
- Regex filtering logic to handle serialization permission easily and efficiently.
- Endpoints to dynamically add, list, and remove serialization permissions.

# Requirements

- [aiokafka](https://aiokafka.readthedocs.io/en/stable/)

# Events

## Subscribed

- All core NApps (`kytos/*` and `kytos.*`)
    - `kytos/mef_eline.*`
    - `kytos/of_core.*`
    - `kytos/flow_manager.*`
    - `kytos/topology.*`
    - `kytos/of_lldp.*`
    - `kytos/pathfinder.*`
    - `kytos/maintenance.*`

# Filtering

Event consumption and serialization follows the principle of `least privilege`, meaning events must be explicitly accepted to be allowed to be propagated to Kafka. Filtering logic uses `regex` to quickly accept or deny incoming events, based on preset patterns. Currently, the NApp mainly supports wildcard logic, but can be easily extended for matching as well:

## Wildcard

The expected functionality, takes in any regex logic and compares values to them

```
# Example
{"pattern": "kytos[./](.*)", "description": "Allows all core NApps"}
```

## Match

To achieve match functionality, you must start and end your match with `^` and `$` respectively.

```
# Example
{"pattern": "^amlight/pathfinder.created$", "description": "Allow ONLY this pattern"}
```

# Planned Endpoint

## GET /v1/filters

Lists the summary of all Filter objects in the filtering pipeline, where the dynamic key is the UUID of the Filter. The response looks similar to the following:

```
[
    "AOIJ8A9JCA898XA01": {
        "pattern": str,
        "mutable": bool,
        "description": str
    },
    "OPKAS9C0A2OJE180U": {
        "pattern": str,
        ...
    },
    ...
]
```

# Development

For the following sections, you will need to create and activate a virtual environment, or `venv`. The following commands create and activate it:

```sh
python3 -m venv venv
source venv/bin/activate
```

## Testing

Testing uses `Tox` and `setup.py` for automated testing, running unit tests with coverage and a lint suite. We do this to simplify testing for developers and centralize flows for CI pipelines when create pull requests. In addition, `Tox` isolates each test to their own environment, reducing unintended side effects.

However, testing requires specific dependency versions to avoid unintended issues with `setup.py`. The following installs them for you:

```sh
pip install tox==4.13.0 virtualenv==20.25.1 pip==24.3.1 setuptools==75.6.0 wheel==0.45.1
```

### Running Tests

Assuming you have already cloned the repository and are inside of it, we activate the automated testing suites by simply running the following command. Then, `Tox` will take care of installing necessary dependencies and run the suites.

```sh
tox
```

If you want to run a specific environment in `Tox`, use the `-e` command and specify the test:

```sh
tox -e coverage
```

```sh
tox -e lint
```

## Integrating with Kytos

The following is a list of commands that allow you quickly download and run the NApp with Kytos. This guide will first get all the necessary Docker dependencies in order before starting Kytos and connecting the NApp.

**NOTE**: If you followed the `Testing` section, you will see that `Tox` uses modern `packaging` versions, while `Kytos` requires `packaging==24.0`. If you see this issue, run the following command to create a fresh virtual environment:

```sh
deactivate
rm -rf venv

python3 -m venv venv
source venv/bin/activate
```

### Mongo Docker Container

Run the following command to create a Docker container running MongoDB 7.0.

```sh
sudo docker run -p 27017:27017 -d mongo:7.0
sudo docker exec -it mongo mongosh --eval 'db.getSiblingDB("kytos").createUser({user: "kytos", pwd: "kytos", roles: [ { role: "dbAdmin", db: "kytos" } ]})'
```

If you are unable to run MongoDB >= 5.0 due to `AVX` restrictions, speak to team members familiar with the application to find next steps.

### Setup Kytos

Next, while you likely have already install `kafka_events`, you can connect it to `Kytos` in a simple way by using the following commands:

```sh
git clone https://github.com/kytos-ng/kytos
cd ./kytos
python -m pip install --editable . --no-cache-dir

cd ..

git clone https://github.com/kytos-ng/kafka_events.git
cd ./kafka_events
python -m pip install --editable . --no-cache-dir

cd ..

pip install aiokafka
```

### Alternative Setup

If you have already installed `kafka_events` and cannot use the simple `pip install .` method, you can use the following commands.

```sh
git clone https://github.com/kytos-ng/kytos
cd ./kytos
python -m pip install --editable . --no-cache-dir

cd ../kafka_events

python3 setup.py develop
```

### Optional - Complete Environment

This is an optional step, but using this script allows you to simulate a richer environment with Kytos.

```sh
  for repo in python-openflow kytos-utils of_core flow_manager topology of_lldp pathfinder coloring sdntrace kytos_stats sdntrace_cp mef_eline; do
    git clone https://github.com/kytos-ng/$repo
    cd $repo
    python -m pip install --editable . --no-cache-dir
    cd ..
  done
```

### Run Kytos

```sh
export MONGO_PASSWORD=kytos
export MONGO_USERNAME=kytos
export MONGO_DBNAME=kytos
export MONGO_HOST_SEEDS=127.0.0.1:27017

docker-compose up -d

kytosd -f -E --database mongodb
```
