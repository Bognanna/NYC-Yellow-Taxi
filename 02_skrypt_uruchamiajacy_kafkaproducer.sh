#!/bin/bash

#Wymagany wgrany plik KafkaProducer.jar
CLUSTER_NAME=$(/usr/share/google/get_metadata_value attributes/dataproc-cluster-name)

java -cp /usr/lib/kafka/libs/*:KafkaProducer.jar \
	com.example.bigdata.TestProducer datasets/yellow_tripdata_result 15 NYC-taxi-topic \
	1 ${CLUSTER_NAME}-w-0:9092