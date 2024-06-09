#!/bin/bash

CLUSTER_NAME=$(/usr/share/google/get_metadata_value attributes/dataproc-cluster-name)

kafka-topics.sh --create \
	--bootstrap-server ${CLUSTER_NAME}-w-1:9092 \
	--replication-factor 2 --partitions 3 --topic NYC-taxi-topic