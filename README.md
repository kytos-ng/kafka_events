# Overview

This NApp integrates Kafka with the Kytos SDN platform to enable event-driven messaging and real-time event streaming.

# Planned Features

- Asynchronous Kafka producer with support for compression and acknowledgments.
- Event listener for new KytosEvents, which then serializes and publishes events to Kafka.
- Resilient Kafka client with automatic retries for connectivity issues.
- Uses Main asyncio loop to handle asynchronous tasks serialization and publishing.
- Regex filtering logic to handle serialization permission easily and efficiently.
- Endpoints to dynamically add, list, and remove serialization permissions.

# Installing

To install this NApp, first, make sure to have the same venv activated as you have ``kytos`` installed on:

.. code:: shell

   $ git clone https://github.com/kytos-ng/kafka_events.git
   $ cd kafka_events
   $ python3 -m pip install --editable .

To install the kytos environment, please follow our
`development environment setup <https://github.com/kytos-ng/documentation/blob/master/tutorials/napps/development_environment_setup.rst>`_.


For the following sections, you will need to create and activate a virtual environment, or `venv`. The following commands create and activate it:

```sh
python3 -m venv venv
source venv/bin/activate
```

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