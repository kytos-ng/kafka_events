"""Module with the Constants used in the kafka_events."""

import os


# Bootstrap Server: (str) Location of the Kafka server
BOOTSTRAP_SERVERS = os.environ.get("KAFKA_HOST_ADDR", "localhost:29092")

# Acknowledgements: (str | int) A setting that sets the acknowledgement of messages to Kafka.
# Available options are 0, 1 and "all"
#   0: No acknowledgements. Zero latency but provides no guarantees on delivery.
#   1: Leader acknowledgement. Some latency but provides a guarantee that the message
#      Was sent to the leader.
#   all: Leader & replica acknowledgement: Highest latency but provides the maximum amount
#        of message delivery guarantees. It requires the leader AND all in-sync replicas
#        To acknowledge the delivery of the message.
ACKS = "all"

# Idempotence: (bool) A setting that tells aiokafka to keep track of all messages,
# attaching IDs to them. This removes possible duplicates at the cost increased
# resource consumption
# IMPORTANT: ENABLE_IDEMPOTENCE requires acks == "all"
ENABLE_ITEMPOTENCE = True

# Topic: (str) The name of the topic we will be sending/consuming from
TOPIC_NAME = "event_logs"

# Compression: (str) The type of compression we would like to send with
COMPRESSION_TYPE = "gzip"

# Batch Size: (int) The amount of data (in bytes) allowed to be sent per batch
# 64 * 1024 == 64 KB
BATCH_SIZE = 64 * 1024

# Linger: (int) The amount of time (in milliseconds) that the producer will wait before
# sending the batch.
LINGER_MS = 50

# Request Size: (int) The maximum amount (in bytes) allowed to be sent per request.
# 1024 * 1024 * 5 == 5 MB
MAX_REQUEST_SIZE = 1024 * 1024 * 5

# Kafka Time Limit: (float | int) The amount of time (in seconds) that any connection to kafka must
# complete before.
KAFKA_TIMELIMIT = 5

# FILTERING

# Blocked patterns: list[str], The patterns we want to explicitly block. This takes precendence
# over ALLOWED_NAMESPACES.
BLOCKED_PATTERNS = (
    "kytos/of_core.v0x04.messages.*",
    "kytos/flow_manager.messages.out.*",
    "kytos/of_lldp.messages.out.*",
    "kytos/core.openflow.raw.*",
)
