# Real-Time Emoji Streaming API

A scalable and fault-tolerant system for ingesting, buffering, and processing emoji reactions in real-time using **Flask**, **Kafka**, and **Spark Structured Streaming**.

## Overview

This project simulates a real-time emoji reaction system where multiple clients send emoji reactions to a central API. The API buffers these reactions and forwards them to a Kafka topic. Spark Structured Streaming processes these reactions with window-based aggregations and logs results.

Use cases include:
- Live event reactions
- Social media engagement tracking
- Real-time analytics dashboards

## Architecture

### High-Level Design (HLD)

```
[Clients] --> [Flask API] --> [Kafka Topic] --> [Spark Streaming Processor] --> [Console Logs / Downstream Systems]
```

- **Clients**: Simulated using `emoji_client_simulator.py`. Multiple threads send emoji reactions to the Flask API.
- **Flask API** (`app.py`): Receives emoji reactions, validates and buffers them, and sends them to a Kafka topic.
- **Kafka**: Acts as a durable and scalable message broker.
- **Spark Structured Streaming** (`emoji_streaming_processor2.py`): Reads messages from Kafka, parses them, performs windowed aggregations, and outputs reaction counts.

### Low-Level Design (LLD)

#### Data Flow

1. **Emoji Client Simulation**
   - Generates random emoji data with:
     - `user_id`: UUID
     - `emoji_type`: Random emoji
     - `timestamp`: Current UTC timestamp
   - Sends data as JSON to the Flask API endpoint `/emoji`.

2. **Flask API**
   - Receives incoming requests and validates required fields.
   - Uses a global in-memory buffer with thread locks to store emoji data temporarily.
   - Periodically flushes buffered data to Kafka using a separate thread.
   - Exposes `/health` and `/` endpoints for status checks.

3. **Kafka**
   - Topic: `emoji_reactions`
   - Handles buffering, scalability, and reliability.

4. **Spark Structured Streaming**
   - Reads messages from Kafka in real-time.
   - Parses JSON into structured format.
   - Aggregates reactions over 2-second windows.
   - Outputs results with reaction counts and scaling logic.

#### Component Breakdown

| Component             | Key Functions |
|----------------------|----------------|
| Flask API            | Receives emoji data, validates, buffers, and sends to Kafka |
| Buffer Manager       | Uses locks to safely add and flush data to Kafka |
| Kafka Producer       | Sends messages reliably with retry mechanisms |
| Kafka Topic          | Stores incoming emoji messages |
| Spark Structured Streaming | Reads from Kafka, aggregates, processes data in micro-batches |
| Clients              | Generate traffic and simulate real-time usage |

#### Data Schema

```json
{
  "user_id": "string",
  "emoji_type": "string",
  "timestamp": "string (ISO8601)"
}
```

#### Configuration Variables

| Variable                | Default Value | Description |
|------------------------|---------------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka server address |
| `EMOJI_TOPIC`           | `emoji_reactions` | Kafka topic name |
| `BUFFER_FLUSH_INTERVAL` | `0.5` seconds | Interval to flush the buffer |
| `NUM_CLIENTS`           | `10` | Number of simulated clients |
| `EMOJIS_PER_CLIENT`    | `1000` | Number of emoji messages per client |

## Technologies Used

- **Python 3.x**
- **Flask**
- **Kafka**
- **Spark Structured Streaming**
- **Requests**
- **Threading**
- **JSON**

## Setup Instructions

### Prerequisites

- Install Java (required by Kafka and Spark)
- Install Python packages:
  ```bash
  pip install flask kafka-python requests pyspark python-dateutil
  ```
- Kafka & Zookeeper installed and running locally

### Kafka Setup

1. Start Zookeeper:
   ```bash
   zookeeper-server-start.sh config/zookeeper.properties
   ```

2. Start Kafka broker:
   ```bash
   kafka-server-start.sh config/server.properties
   ```

3. Create the topic:
   ```bash
   kafka-topics.sh --create --topic emoji_reactions --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
   ```

### Run Flask API

```bash
python app.py
```

### Run Emoji Client Simulator

```bash
python emoji_client_simulator.py
```

### Run Spark Streaming Processor

```bash
python emoji_streaming_processor2.py
```

## API Endpoints

### GET `/`

Returns service information.

### POST `/emoji`

Accepts emoji reaction data.

**Request JSON Format:**
```json
{
  "user_id": "string",
  "emoji_type": "string",
  "timestamp": "string (ISO8601 format)"
}
```

**Response:**
```json
{
  "status": "Emoji received",
  "message_id": "UUID"
}
```

### GET `/health`

Returns system health, Kafka connection status, and buffer size.

## Configuration

You can configure the application using environment variables:

```bash
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
export EMOJI_TOPIC="emoji_reactions"
export BUFFER_FLUSH_INTERVAL="0.5"
```

## Future Improvements

- ✅ Add authentication & rate limiting
- ✅ Use a persistent database for buffer overflow scenarios
- ✅ Add monitoring and alerting with Prometheus and Grafana
- ✅ Implement retries with exponential backoff in Kafka producers
- ✅ Containerize using Docker and Docker Compose
- ✅ Add unit tests and integration tests
- ✅ Secure Kafka with SSL/SASL

## Folder Structure

```
.
├── app.py
├── emoji_client_simulator.py
├── emoji_streaming_processor2.py
├── README.md
├── requirements.txt
```

## License

MIT License © 2025
