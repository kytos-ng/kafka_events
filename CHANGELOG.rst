#########
Changelog
#########
All notable changes to the kafka_events NApp will be documented in this file.


[2026.1.0] - 2026-04-28
***********************

Changed
=======
- ``LINGER_MS`` increased to 50
- ``KAFKA_TIMELIMIT`` increased to 50 to better match ``aiokafka`` expectations.
- Producer now relies in the timeout set in its constructor instead of ``asyncio.wait_for``.

Fixed
=====
- Updated the docker image settings to match the configuration from ``settings.py``
- Upgraded aiokafka version from ``0.12.0`` to ``0.14.0`` which has the correct implementation for batches.

Added
=====
- Added GET /v1/filters endpoint to list all filters in the filtering pipeline.
- Now topics are allowed to be created while kytos is running
- Applied retries for producer when sending messages to kafka broker. 3 retries, each retry will wait from 10 to 15 seconds.
