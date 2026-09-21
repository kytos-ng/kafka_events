# Overview

This NApp integrates Kafka with the Kytos SDN platform to enable event-driven messaging and real-time event streaming.

# Planned Features

- Asynchronous Kafka producer with support for compression and acknowledgments.
- Event listener for new KytosEvents, which then serializes and publishes events to Kafka.
- Resilient Kafka client with automatic retries for connectivity issues.
- Uses the main asyncio loop to handle asynchronous task serialization and publishing.
- Regex filtering logic to handle serialization permissions easily and efficiently.
- Endpoints to dynamically add, list, and remove serialization permissions.

# Installing

To install this NApp, first make sure that you have activated the same virtual environment in which ``kytos`` is installed:

.. code:: shell

   $ git clone https://github.com/kytos-ng/kafka_events.git
   $ cd kafka_events
   $ python3 -m pip install --editable .

To install the Kytos environment, please follow our
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

Event consumption and serialization follow the principle of least privilege, meaning that events must be explicitly accepted before they can be propagated to Kafka. The filtering logic uses regular expressions to quickly accept or deny incoming events based on preset patterns. Currently, the NApp mainly supports wildcard logic, but it can easily be extended to support matching as well:

## Wildcard

The expected functionality takes any regular expression and compares values against it.

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

# Endpoints

## GET /v1/patterns

Lists a summary of all Pattern objects in the filtering pipeline. The response looks similar to the following:

```
    {
        "allowed": {
            "flows": [
                "kytos/flow_manager.flow.added",
                "kytos.flow_manager.flows.single.install",
            ],
            "of_lldp": ["kytos/of_lldp.interface.is.nni"]
        },
        "blocked": [
            "kytos/of_core.v0x04.messages.*",
            "kytos/flow_manager.messages.out.*",
            "kytos/of_lldp.messages.out.*",
            "kytos/core.openflow.raw.*",
            "kytos/mef_eline.evcs_loaded"
        ]
    }
```

## POST /v1/patterns

Adds patterns with their list of topics. The body looks like this:

```
    {
        "flows": [
            "kytos/flow_manager.flow.added"
            ,"kytos.flow_manager.flows.single.install"
        ]
    }
```

## DELETE /v1/patterns/{topic}

Deletes a topic from the pool.

## PATCH /v1/patterns/{topic}

Adds patterns only to a specific topic.

## PUT /v1/patterns/{topic}

Replaces the list of patterns for a specific topic.
