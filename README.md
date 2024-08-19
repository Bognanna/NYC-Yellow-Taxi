# NYC-Yellow-Taxi
This is a project for "Stream Processing in Big Data Systems" course. It uses Kafka to create topics, Spark Structured Streaming to process datastream and direct results to Postgresql database. The project is under active developement.

![Architecture](https://github.com/Bognanna/NYC-Yellow-Taxi/blob/main/img/architecture.PNG)

## Executing project

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

-- 00_skrypt_przygotowujacy_pozostale_skrypty.sh\
-- 01_skrypt_tworzacy_zrodlowe_tematy_kafki.sh\
-- 02_skrypt_uruchamiajacy_kafkaproducer.sh\
-- 03_program_przetwarzania_strumieni_danych.py\
-- 04_skrypt_uruchamiajacy_program_przetwarzania_strumieni_danych.sh\
-- 05_1_skrypt_przygotowujacy_miejsce_docelowe.sql\
-- 05_2_skrypt_uruchamiajacy_skrypt_przygotowujacy_miejsce_docelowe.sh\
-- 06_skrypt_odczytujacy_wyniki_z_miejsca_docelowego.sh\
-- KafkaProducer.jar\
-- **datasets**\
----- taxi_zone_lookup.csv\
----- **yellow_tripdata_result**\
-------- part-00000-....csv\
-------- ...\

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
### Create postgresql database
In one of the terminals run script 05_2 to create streamoutput database in postgresql and taxiagg table.
```
./05_2_skrypt_uruchamiajacy_skrypt_przygotowujacy_miejsce_docelowe.sh
```

### Run kafkaproducer.sh
In onother terminal run script 01 to create kafka topics.
```
./01_skrypt_tworzacy_zrodlowe_tematy_kafki.sh
```
Run script 02 in order to start sending records to created topic.
```
./02_skrypt_uruchamiajacy_kafkaproducer.sh
```

### Run Spark application
In last unused terminal run script 04.
```
./04_skrypt_uruchamiajacy_program_przetwarzania_strumieni_danych.sh
```

### Check taxiagg status
In order to show taxiagg table run script 06.
```
./06_skrypt_odczytujacy_wyniki_z_miejsca_docelowego.sh
```

## Code description
### Producer
KafkaProducer.jar takes as an input 5 arguments:
- `inputDir` (str) path to directory with csv files
- `sleepTime` (str) number of seconds to termiantion which program will wait after posting content from all files from `inputDir`
- `topicName` (str) name of the Kafka topic on which producer will post content
- `headerLength` (str) number of header lines in a file, these lines will be ignored by the producer
- `bootstrapServers` (str) addresses of the Kafka brokers in a bootstrap Kafka cluster

KafkaProducer looks for files in `inputDir` and post their content line by line on topic `topicName`.

### Transformations - 03_..._.py
Program reads lines from kafka topic and converts them from csv format to dataframe. It aggregates them and post them to postgresql table.

**TODO**
- [x] Use data from static table `taxi_zones_lookup` to make aggregations on borough
- [] Add windows and watermarks
- [] Chose proper trigger
- [] Data check and outlier filter

Read data stream:
```python
	taxiDS = spark.readStream \
		.format("kafka") \
		.option("kafka.bootstrap.servers", f"{HOST_NAME}:{port}")\
		.option("subscribe", topic_name) \
		.load()
```

Convert csv format to dataframe:
```python
	csv_schema = "tripID INT, start_stop INT, timestamp STRING, locationID INT, passenger_count INT, trip_distance FLOAT, payment_type INT, amount FLOAT, VendorID INT"

	dataDF = taxi_csv.select(
			from_csv(taxi_csv.value, csv_schema).alias("val")
		).select(
			col("val.tripID").cast("int").alias("tripID"), \
			col("val.start_stop").cast("int").alias("start_stop"), \
			to_timestamp(col("val.timestamp")).alias("dt"), \
			col("val.passenger_count").cast("int").alias("passenger_count"), \
			col("val.trip_distance").cast("float").alias("trip_distance"), \
			col("val.payment_type").cast("int").alias("payment_type"), \
			col("val.amount").cast("float").alias("amount"), \
			col("val.VendorID").cast("int").alias("VendorID"), \
			col("val.locationID").cast("int").alias("locationID")
		)
```

Aggregate data
```python
	count_cond = lambda cond: sum(when(cond, 1).otherwise(0))
	sum_cond = lambda cond, val: sum(when(cond, val).otherwise(0))

	resultDF = dataDF.join(
			zoneDF, dataDF.locationID == zoneDF.locationID, 'left'
		).groupBy(
			[date_format("dt", 'yyyy-MM-dd').alias("date"), col("Borough").alias("borough")]
		).agg(
			count_cond(col("start_stop") == 0).alias("N_departures"),
			count_cond(col("start_stop") == 1).alias("N_arrivals"),
			sum_cond(col("start_stop") == 0, col("passenger_count")).alias("N_departing"),
			sum_cond(col("start_stop") == 1, col("passenger_count")).alias("N_arriving")	
		)
```

Store result in Postgresql
```python
	streamWriter = resultDF.writeStream.outputMode("complete").foreachBatch (
		lambda batchDF, batchId:
			batchDF.write
			.format("jdbc")
			.mode("overwrite")
			.option("url", f"jdbc:postgresql://{HOST_NAME}:8432/streamoutput")
			.option("dbtable", "taxiagg")
			.option("user", "postgres")
			.option("password", "mysecretpassword")
			.option("truncate", "true")
			.save()
	)
```

### Store results - option A
**TODO**

### Store results - option C
Right now program uses 'complete' outputMode, however without defined windows and watermarks it posts results to late. **TODO**

### Anomalies detection
**TODO**

### Store results
Results of stream processing are stored in postgresql table. It is caused by the need of storing big amounts of data and the need of easy access to them and to filter options.

Results of detecting anomalies will be posted to another kafka topic to ensure as fast as possible alarming about anomaly detection.
  



