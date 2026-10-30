#########
Changelog
#########
All notable changes to the kafka_events NApp will be documented in this file.


[2026.1.0] - 2026-04-28
***********************

Added
=====
- Added GET /v1/filters endpoint to list all filters in the filtering pipeline.
- When kytos initializes without Kafka broker available, the NApp will keep trying to connect after an event is sent every ``KAFKA_ERROR_LOG_INTERVAL`` seconds. The default value is 60 seconds.
