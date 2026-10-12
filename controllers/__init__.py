import os
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Iterator, List, Optional, Union

import pymongo
from bson.decimal128 import Decimal128
from pymongo.collection import ReturnDocument
from pymongo.errors import ConnectionFailure, ExecutionTimeout
from pymongo.operations import UpdateOne
from tenacity import retry_if_exception_type, stop_after_attempt, wait_random

from kytos.core import log
from kytos.core.db import Mongo
from kytos.core.retry import before_sleep, for_all_methods, retries


@for_all_methods(
    retries,
    stop=stop_after_attempt(
        int(os.environ.get("MONGO_AUTO_RETRY_STOP_AFTER_ATTEMPT", 3))
    ),
    wait=wait_random(
        min=int(os.environ.get("MONGO_AUTO_RETRY_WAIT_RANDOM_MIN", 0.1)),
        max=int(os.environ.get("MONGO_AUTO_RETRY_WAIT_RANDOM_MAX", 1)),
    ),
    before_sleep=before_sleep,
    retry=retry_if_exception_type((ConnectionFailure, ExecutionTimeout)),
)
class TopicController:
    """TopicController."""
    def __init__(self, get_mongo = lambda: Mongo()) -> None:
        """Initialize TopicController."""
        self.mongo = get_mongo()
        self.db_client = self.mongo.client
        self.db = self.db_client[self.mongo.db_name]

    def get_allowed_topics_patterns(self) -> dict[str, List[str]]:
        """Get all allowed topics."""
        allowed_topics = {}
        for topic_patterns in self.db.allowed_patterns.find():
            print(f"topic_patterns: {topic_patterns}")
            allowed_topics[topic_patterns["_id"]] = topic_patterns["patterns"]
        return allowed_topics

    def insert_allowed_patterns(self, topic_dict: dict[str, List[str]]) -> None:
        """Insert allowed topics and patterns."""
        payload = []
        for topic, patterns in topic_dict.items():
            payload.append(
                UpdateOne(
                    {"_id": topic},
                    {"$set": {"patterns": patterns}},
                    upsert=True,
                )
            )

        self.db.allowed_patterns.bulk_write(payload)

    def delete_allowed_topic(self, topic: str) -> None:
        """Delete allowed topic."""
        self.db.allowed_patterns.delete_one({"_id": topic})