# NYC-Yellow-Taxi
This is a project for "Stream Processing in Big Data Systems" course. It uses Kafka to create topics, Spark Structured Streaming to process datastream and direct results to Postgresql database. The project is under active developement. 

## First Steps

### Run the project on Google Cloud dataproc cluster
To run the cluster use this command providing proper `CLUSTER_NAME`, `REGION`, `PROJECT_ID` values.
```
  gcloud dataproc clusters create ${CLUSTER_NAME} \
  	--enable-component-gateway --region ${REGION} --subnet default \
  	--master-machine-type n1-standard-4 --master-boot-disk-size 50 \
  	--num-workers 2 --worker-machine-type n1-standard-2 --worker-boot-disk-size 50 \
  	--image-version 2.1-debian11 --optional-components DOCKER,ZOOKEEPER \
  	--project ${PROJECT_ID} --max-age=2h \
  	--metadata "run-on-master=true" \
  	--initialization-actions \
  	gs://goog-dataproc-initialization-actions-${REGION}/kafka/kafka.sh
```
Then connect to VM instance using SSH client. Overall you will need 3 connections: one for producer, one for consument and one for database.

### Upload scripts
Upload files from this repository to the virtual machine.

### Upload data
Download to your local machine needed datasets: [taxi_zone_lookup] (http://www.cs.put.poznan.pl/kjankiewicz/bigdata/stream_project/taxi_zone_lookup.csv) and [yellow_tripdata_result] (http://www.cs.put.poznan.pl/kjankiewicz/bigdata/stream_project/yellow_tripdata_result.zip). Unpack the zip file and upload everyting to the virtual machine. You can as well upload the files to your Google Cloud Bucket and copy them using following command:
```
hadoop fs -copyToLocal gs://${BUCKET_NAME}${PATH_TO_DIR}
```
### Directory tree structure
Files and directories shoud be placed as following:

-- 00_skrypt_przygotowujacy_pozostale_skrypty.sh
-- 01_skrypt_tworzacy_zrodlowe_tematy_kafki.sh
-- 02_skrypt_uruchamiajacy_kafkaproducer.sh
-- 03_program_przetwarzania_strumieni_danych.py
-- 04_skrypt_uruchamiajacy_program_przetwarzania_strumieni_danych.sh
-- 05_1_skrypt_przygotowujacy_miejsce_docelowe.sql
-- 05_2_skrypt_uruchamiajacy_skrypt_przygotowujacy_miejsce_docelowe.sh
-- 06_skrypt_odczytujacy_wyniki_z_miejsca_docelowego.sh
-- KafkaProducer.jar
-- *datasets*
----- taxi_zone_lookup.csv
----- *yellow_tripdata_result*
-------- part-00000-....csv
-------- ...

### Prepare scripts
Run following commands to give executable permissions to 00_skrypt_przygotowujacy_pozostale_skrypty.sh file and to replace CR characters (windows) with nothing (unix) in order to Bash be able to read and execute the file.
```
chmod +x 00_skrypt_przygotowujacy_pozostale_skrypty.sh
sed -i -e 's/\r$//' 00_skrypt_przygotowujacy_pozostale_skrypty.sh
```
Then run the script. It will do the same with the rest of the scripts:
```
./00_skrypt_przygotowujacy_pozostale_skrypty.sh
```
## Create postgresql database
In one of the terminals run script 05_2 to create streamoutput database in postgresql and taxiagg table.
```
./05_2_skrypt_uruchamiajacy_skrypt_przygotowujacy_miejsce_docelowe.sh
```

## Run kafkaproducer.sh
In onother terminal run script 01 to create kafka topics.
```
./01_skrypt_tworzacy_zrodlowe_tematy_kafki.sh
```
Run script 02 in order to start sending records to created topic.
```
./02_skrypt_uruchamiajacy_kafkaproducer.sh
```

## Run Spark application
In last unused terminal run script 04.
```
./04_skrypt_uruchamiajacy_program_przetwarzania_strumieni_danych.sh
```

## Checking taxiagg status
In order to schow taxiagg table run script 06.
```
./06_skrypt_odczytujacy_wyniki_z_miejsca_docelowego.sh
```

