#########
Changelog
#########
All notable changes to the kafka_events NApp are documented in this file.


[2026.1.0] - 2026-04-28
***********************

Changed
=======
- Changed the endpoint from GET /v1/filters to GET /v1/topics and updated it to return allowed and blocked patterns.
- The producer now publishes to multiple topics depending on the matching pattern when the event was captured.
- Added a controller for database updates to reserve newly added allowed topics.

Added
=====
- Added a GET /v1/filters endpoint to list all filters in the filtering pipeline.
- Added a POST /v1/topics endpoint that allows topics and patterns to be added to the Kafka broker.
- Added DELETE /v1/topics/{topic} to delete a specific topic.
- Added PATCH /v1/topics/{topic} to add more topics to a specific topic.
- Added PUT /v1/topics/{topic} to replace the list of patterns for a specific topic.

