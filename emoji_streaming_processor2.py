from pyspark.sql import SparkSession
from pyspark.sql.functions import col, window, count, first, from_json, when, lit
from pyspark.sql.types import StructType, StructField, StringType, TimestampType

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
INPUT_TOPIC = 'emoji_reactions'

def create_spark_session():
    """Create a Spark session with Kafka support."""
    spark = SparkSession.builder \
        .appName("RealTimeEmojiAggregator") \
        .config("spark.jars.packages", 
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2,org.apache.kafka:kafka-clients:2.6.0") \
        .config("spark.sql.streaming.checkpointLocation", "/tmp/emoji_reactions_checkpoint") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark

def create_schema():
    """Define schema for incoming Kafka data."""
    return StructType([
        StructField("user_id", StringType(), True),
        StructField("emoji_type", StringType(), True),
        StructField("timestamp", StringType(), True)
    ])

def process_stream(spark):
    """Process the Kafka stream with 2-second interval aggregation."""
    # Read data from Kafka
    kafka_stream = spark.readStream.format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", INPUT_TOPIC) \
        .load()
    
    # Parse JSON data from Kafka
    parsed_stream = kafka_stream.select(
        from_json(col("value").cast("string"), create_schema()).alias("data")
    ).select("data.*")
    
    # Convert timestamp to proper type
    parsed_stream = parsed_stream.withColumn(
        "event_time", col("timestamp").cast(TimestampType())
    )
    
    # Windowed aggregation (2-second intervals)
    aggregated_stream = parsed_stream.groupBy(
        window(col("event_time"), "2 seconds"),  # 2-second interval
        col("emoji_type")
    ).agg(
        count("user_id").alias("reaction_count"),
        first("emoji_type").alias("emoji")
    ).select(
        col("window.start").alias("window_start"),
        col("window.end").alias("window_end"),
        col("emoji"),
        col("reaction_count"),
        # Apply scaling logic
        when(col("reaction_count") <= 50, lit(1))
        .when(col("reaction_count") <= 1000, lit(1))
        .otherwise(col("reaction_count")).alias("scaled_reactions")
    )
    
    # Process each micro-batch
    def process_batch(batch_df, batch_id):
        """Micro-batch processing."""
        print(f"Processing Batch {batch_id}")
        batch_data = batch_df.collect()  # Avoid toPandas to skip Pandas dependency
        for row in batch_data:
            print(row)

    # Write stream using micro-batching
    query = aggregated_stream.writeStream \
        .outputMode("complete") \
        .foreachBatch(process_batch) \
        .start()
    
    return query

def main():
    spark = create_spark_session()
    try:
        query = process_stream(spark)
        query.awaitTermination()
    except Exception as e:
        print(f"Error in streaming application: {e}")
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
