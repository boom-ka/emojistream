from flask import Flask, request, jsonify
from kafka import KafkaProducer
from kafka.errors import KafkaError
import json
import threading
import time
import random
import uuid
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
EMOJI_TOPIC = os.getenv('EMOJI_TOPIC', 'emoji_reactions')
BUFFER_FLUSH_INTERVAL = float(os.getenv('BUFFER_FLUSH_INTERVAL', 0.5))

# Global variables
producer = None
emoji_buffer = []
buffer_lock = threading.Lock()

def create_kafka_producer():
    """Create Kafka producer with error handling"""
    global producer
    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            retries=3,
            max_block_ms=10000
        )
        logger.info("Kafka producer initialized successfully")
        return producer
    except KafkaError as e:
        logger.error(f"Kafka connection error: {e}")
        return None

def flush_buffer():
    """Periodically flush emoji data to Kafka producer"""
    while True:
        time.sleep(BUFFER_FLUSH_INTERVAL)
        with buffer_lock:
            if emoji_buffer and producer:
                try:
                    for emoji_data in emoji_buffer:
                        future = producer.send(EMOJI_TOPIC, emoji_data)
                        future.get(timeout=10)  # Wait for send confirmation
                    producer.flush()
                    logger.info(f"Flushed {len(emoji_buffer)} emoji messages")
                    emoji_buffer.clear()
                except KafkaError as e:
                    logger.error(f"Error sending messages to Kafka: {e}")

@app.route('/')
def home():
    """Home route to provide basic information"""
    return jsonify({
        "service": "Emoji Streaming API",
        "version": "1.0.0",
        "status": "Running"
    })

@app.route('/emoji', methods=['POST'])
def receive_emoji():
    """API endpoint to receive emoji reactions"""
    try:
        emoji_data = request.json

        # Validate incoming data
        if not emoji_data or not all(key in emoji_data for key in ['user_id', 'emoji_type', 'timestamp']):
            return jsonify({"error": "Invalid emoji data"}), 400

        with buffer_lock:
            emoji_buffer.append(emoji_data)
        
        return jsonify({
            "status": "Emoji received", 
            "message_id": str(uuid.uuid4())
        }), 200

    except Exception as e:
        logger.error(f"Error processing emoji: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "kafka_connected": producer is not None,
        "buffer_size": len(emoji_buffer)
    }), 200

def start_background_threads():
    """Start background threads for buffer flushing"""
    # Create Kafka producer
    create_kafka_producer()
    
    # Start buffer flushing thread
    threading.Thread(target=flush_buffer, daemon=True).start()

if __name__ == '__main__':
    # Initialize background processes
    start_background_threads()
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)
