import argparse
import socket
from pyspark.sql import SparkSession
from pyspark.sql.functions import expr
from pyspark.sql.functions import from_csv, col, to_timestamp
from pyspark.sql.types import TimestampType
from pyspark.sql.functions import date_format, sum, when
from pyspark.sql import DataFrame
from pyspark.sql.streaming import StreamingQueryManager



#ZONE_PATH = "gs://pbd-03-24-bk/project/datasets/taxi_zone_lookup.csv"
HOST_NAME = socket.gethostname()
SCALA_VERSION = '2.12'
SPARK_VERSION = '3.3.2'
POSTGRESQL_VERSION = '42.6.0'

packages = [f'org.apache.spark:spark-sql-kafka-0-10_{SCALA_VERSION}:{SPARK_VERSION}']

def parse_args():
    
    parser = argparse.ArgumentParser(
        description = "Using Spark Structured Streaming deal with stream of NYC Yellow Taxi data") 
    
    args = parser.parse_args()

    return args


def init_spark_session(title = "Spark StrStr - NYC Taxi"):

	spark = SparkSession.builder\
		.appName(title)\
		.config("spark.jars.packages", ",".join(packages))\
		.config("spark.driver.extraClassPath", f'./postgresql-{POSTGRESQL_VERSION}.jar')\
		.config("spark.jars", f'./postgresql-{POSTGRESQL_VERSION}.jar')\
		.getOrCreate()
	
	return spark


def create_taxi_zones_df(taxi_zones_file_path):

	zoneDF = spark.read.csv(taxi_zones_file_path, header=True, inferSchema=True)
	zoneDF = zoneDF.withColumnRenamed("LocationID", "locationID")

	return zoneDF


def convert_csv_to_df(taxi_csv):
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
	
	return dataDF


def read_taxi_data_stream(port = '9092', topic_name = "NYC-taxi-topic"):

	taxiDS = spark.readStream \
		.format("kafka") \
		.option("kafka.bootstrap.servers", f"{HOST_NAME}:{port}")\
		.option("subscribe", topic_name) \
		.load()
	
	taxi_csv= taxiDS.select(expr("CAST(value AS STRING)").alias("value"))
	taxiDF = convert_csv_to_df(taxi_csv)

	return taxiDF


def create_resultDF(dataDF, zoneDF):
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
	
	return resultDF


def direct_result_to_console(resultDF):
	streamWriter = resultDF.writeStream\
		.outputMode("complete")\
		.format("console")\
		.start()

	return streamWriter

def direct_result_to_database(resultDF):

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

	return streamWriter

#---------------------------
#--------  MAIN ------------
#---------------------------

if __name__ == "__main__":
    
	args = parse_args()

	spark = init_spark_session()

	zoneDF = create_taxi_zones_df(ZONE_PATH)
	taxiDF = read_taxi_data_stream()

	resultDF = create_resultDF(taxiDF, zoneDF)

	#direct_result_to_console(resultDF)

	streamWriter = direct_result_to_database(resultDF)

	query = streamWriter.start()
	spark.streams.awaitAnyTermination()
