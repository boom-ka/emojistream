import kafka
from confluent_kafka import Producer, Consumer
import json
import threading
import uuid
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

class EmojiPubSubManager:
    def __init__(self, kafka_bootstrap_servers='localhost:9092'):
        self.bootstrap_servers = kafka_bootstrap_servers
        self.main_publisher_topic = 'emoji_main_publisher'
        self.cluster_topics = [
            'emoji_cluster_1', 
            'emoji_cluster_2', 
            'emoji_cluster_3'
        ]
        self.cluster_subtopics = {
            'emoji_cluster_1': [
                'emoji_cluster_1_sub1',
                'emoji_cluster_1_sub2', 
                'emoji_cluster_1_sub3'
            ],
            'emoji_cluster_2': [
                'emoji_cluster_2_sub1',
                'emoji_cluster_2_sub2', 
                'emoji_cluster_2_sub3'
            ],
            'emoji_cluster_3': [
                'emoji_cluster_3_sub1',
                'emoji_cluster_3_sub2', 
                'emoji_cluster_3_sub3'
            ]
        }
        self.producer_config = {
            'bootstrap.servers': self.bootstrap_servers,
            'client.id': f'emoji_pubsub_producer_{uuid.uuid4()}'
        }
        self.consumer_config = {
            'bootstrap.servers': self.bootstrap_servers,
            'group.id': f'emoji_pubsub_consumer_{uuid.uuid4()}',
            'auto.offset.reset': 'earliest'
        }

    def create_producer(self):
        """Create a Kafka producer."""
        return Producer(self.producer_config)

    def create_consumer(self, topic):
        """Create a Kafka consumer for a specific topic."""
        consumer = Consumer(self.consumer_config)
        consumer.subscribe([topic])
        return consumer

    def publish_to_main_topic(self, aggregated_data):
        """Publish aggregated emoji data to the main publisher topic."""
        producer = self.create_producer()
        try:
            producer.produce(
                self.main_publisher_topic, 
                key=str(aggregated_data['window_start']).encode('utf-8'),
                value=json.dumps(aggregated_data).encode('utf-8')
            )
            producer.flush()
            print(f"Published to main topic: {aggregated_data}")
        except Exception as e:
            print(f"Error publishing to main topic: {e}")

    def distribute_to_clusters(self, aggregated_data):
        """Distribute data to cluster-specific topics and their subtopics."""
        producer = self.create_producer()
        for cluster_topic, subtopics in self.cluster_subtopics.items():
            try:
                # Publish to main cluster topic
                producer.produce(
                    cluster_topic,
                    key=str(aggregated_data['window_start']).encode('utf-8'),
                    value=json.dumps(aggregated_data).encode('utf-8')
                )

                # Distribute to subtopics using round-robin or hash-based partitioning
                subtopic = subtopics[hash(str(aggregated_data['emoji'])) % len(subtopics)]
                producer.produce(
                    subtopic,
                    key=str(aggregated_data['window_start']).encode('utf-8'),
                    value=json.dumps(aggregated_data).encode('utf-8')
                )

                producer.flush()
                print(f"Published to {cluster_topic} and {subtopic}: {aggregated_data}")
            except Exception as e:
                print(f"Error publishing to {cluster_topic}: {e}")

    def start_cluster_subscriber(self, cluster_topic):
        """Start a subscriber for a specific cluster topic."""
        def subscribe_and_process():
            consumer = self.create_consumer(cluster_topic)
            try:
                while True:
                    msg = consumer.poll(1.0)
                    if msg is None:
                        continue
                    if msg.error():
                        print(f"Consumer error: {msg.error()}")
                        continue

                    emoji_data = json.loads(msg.value().decode('utf-8'))
                    self.process_cluster_data(emoji_data)
            except Exception as e:
                print(f"Error in cluster subscriber for {cluster_topic}: {e}")
            finally:
                consumer.close()

        thread = threading.Thread(target=subscribe_and_process)
        thread.start()
        return thread

    def process_cluster_data(self, emoji_data):
        """Process data received by cluster subscribers."""
        print(f"Cluster processing emoji data: {emoji_data}")
        # Add your custom processing logic here

    def setup_cluster_subscribers(self):
        """Set up subscribers for all cluster topics and their subtopics."""
        subscriber_threads = []

        # Subscribe to main cluster topics
        for cluster_topic in self.cluster_topics:
            thread = self.start_cluster_subscriber(cluster_topic)
            subscriber_threads.append(thread)

        # Subscribe to subtopics
        for subtopics in self.cluster_subtopics.values():
            for subtopic in subtopics:
                thread = self.start_cluster_subscriber(subtopic)
                subscriber_threads.append(thread)

        return subscriber_threads

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

    return aggregated_stream

def main():
    spark = create_spark_session()
    pubsub_manager = EmojiPubSubManager()

    # Set up cluster subscribers
    cluster_threads = pubsub_manager.setup_cluster_subscribers()

    try:
        # Process the stream
        aggregated_stream = process_stream(spark)

        # Process each micro-batch
        def process_batch(batch_df, batch_id):
            print(f"Processing Batch {batch_id}")
            batch_data = batch_df.collect()
            for row in batch_data:
                aggregated_data = {
                    "window_start": str(row["window_start"]),
                    "window_end": str(row["window_end"]),
                    "emoji": row["emoji"],
                    "reaction_count": row["reaction_count"],
                    "scaled_reactions": row["scaled_reactions"]
                }
                # Publish to main topic and distribute to clusters
                pubsub_manager.publish_to_main_topic(aggregated_data)
                pubsub_manager.distribute_to_clusters(aggregated_data)

        # Start the streaming query
        query = aggregated_stream.writeStream \
            .foreachBatch(process_batch) \
            .outputMode("update") \
            .start()

        query.awaitTermination()
    except Exception as e:
        print(f"Error in streaming application: {e}")
    finally:
        spark.stop()
        # Optional: Add cleanup for cluster threads
        for thread in cluster_threads:
            thread.join()

if __name__ == "__main__":
    main()
