
# 🧠 Real-Time Emoji Reaction Aggregator with Kafka & Spark Streaming

This project implements a **real-time emoji reaction analytics pipeline** using **Apache Spark Structured Streaming** and **Apache Kafka**.  
It demonstrates how live emoji reactions (e.g., from social media or chat platforms) can be **aggregated, scaled, and distributed** efficiently across **multiple Kafka clusters and subscribers**.

---

## 🚀 Overview

The system captures emoji reactions in real time, aggregates them into 2-second time windows, scales the reaction counts, and publishes the results to multiple **Kafka clusters** and **subscriber subtopics** for downstream processing, visualization, or alerting.

The architecture follows a **pub/sub model**, where Spark acts as the **stream processor** and Kafka provides **data distribution and fault tolerance**.

---

## 🧩 Architecture



[Emoji Producer]
↓
[Kafka Topic: emoji_reactions]
↓
[Spark Structured Streaming]
├─ Aggregates reactions (2-sec window)
├─ Scales counts
↓
[EmojiPubSubManager]
├─ Publishes to main topic (emoji_main_publisher)
├─ Distributes to clusters:
│   ├─ emoji_cluster_1 / sub1, sub2, sub3
│   ├─ emoji_cluster_2 / sub1, sub2, sub3
│   └─ emoji_cluster_3 / sub1, sub2, sub3
↓
[Subscribers]
├─ Dashboards
├─ Data warehouses
└─ Notification systems



---

## ⚙️ Components

### 1️⃣ `pubsub.py`
Implements the **Pub/Sub manager** and the **Spark streaming job**:
- Reads raw reactions from Kafka (`emoji_reactions`)
- Aggregates emoji counts in **2-second time windows**
- Scales reaction counts dynamically
- Publishes aggregated results to:
  - A main topic (`emoji_main_publisher`)
  - Multiple cluster topics (`emoji_cluster_1`, `emoji_cluster_2`, `emoji_cluster_3`)
  - Subtopics under each cluster (for fan-out distribution)
- Starts background subscribers for each cluster/subtopic

### 2️⃣ `emoji_streaming_processor2.py`
A simplified version used for **testing and debugging the aggregation logic** without Kafka publishing:
- Performs the same streaming aggregation
- Prints micro-batch outputs directly to the console

---

## 🧮 Aggregation Logic

Emoji reactions are grouped into **2-second windows** and aggregated:

| Window Interval | Operation | Description |
|------------------|------------|--------------|
| `window(event_time, "2 seconds")` | Grouping | Groups reactions by emoji type and time window |
| `count(user_id)` | Aggregation | Counts total reactions per emoji |
| `scaled_reactions` | Scaling | Applies scaling rules for large counts |

### Scaling Rules:
python
when(col("reaction_count") <= 50, lit(1))
.when(col("reaction_count") <= 1000, lit(1))
.otherwise(col("reaction_count"))




## 🧠 Why Clusters After Aggregation?

Even though data is aggregated upstream by Spark, Kafka clusters and subtopics remain crucial for:

* **Distribution** of aggregated results to multiple consumers
* **Fault tolerance** and decoupling of producers/consumers
* **Multi-region or multi-tenant delivery**
* **Post-aggregation processing** (e.g., enrichment, anomaly detection)
* **Data replay** for late subscribers

This architecture ensures **scalability and resilience** across multiple downstream systems.

---

## 🛠️ Setup Instructions

### 1️⃣ Prerequisites

* Python 3.8+
* Apache Kafka running on `localhost:9092`
* Apache Spark 3.1.2+ with Kafka connector
* Java 8 or 11

### 2️⃣ Install Dependencies

bash
pip install confluent-kafka pyspark


### 3️⃣ Start Kafka

Make sure Kafka and Zookeeper are running:

bash
zookeeper-server-start.sh config/zookeeper.properties
kafka-server-start.sh config/server.properties

Create required topics:

bash
kafka-topics.sh --create --topic emoji_reactions --bootstrap-server localhost:9092
kafka-topics.sh --create --topic emoji_main_publisher --bootstrap-server localhost:9092
kafka-topics.sh --create --topic emoji_cluster_1 --bootstrap-server localhost:9092
kafka-topics.sh --create --topic emoji_cluster_2 --bootstrap-server localhost:9092
kafka-topics.sh --create --topic emoji_cluster_3 --bootstrap-server localhost:9092

### 4️⃣ Run the Application

Run the main streaming app:

bash
python pubsub.py

(Optional) Run the simpler version for debugging:

bash
python emoji_streaming_processor2.py


---

## 🧪 Example Input

json
{
  "user_id": "user123",
  "emoji_type": "❤️",
  "timestamp": "2025-10-29T22:31:00"
}


---

## 📊 Example Aggregated Output

json
{
  "window_start": "2025-10-29T22:31:00",
  "window_end": "2025-10-29T22:31:02",
  "emoji": "❤️",
  "reaction_count": 120,
  "scaled_reactions": 120
}


---

## 🧱 Future Improvements

* Add a real-time dashboard using WebSocket or Plotly Dash
* Implement fault-tolerant subscriber checkpointing
* Integrate sentiment analysis with emoji trends
* Store aggregates in Cassandra or PostgreSQL for long-term analysis

---

## 👨‍💻 Authors

**Vedant Singh**
PES University, Electronic City
*Streaming Systems | Kafka | Spark | Real-Time Analytics*

---

## 🪪 License

This project is licensed under the **MIT License** – feel free to modify and use it for educational or research purposes.

---

## 🌟 Acknowledgements

* [Apache Spark Structured Streaming](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
* [Apache Kafka](https://kafka.apache.org/)
* [Confluent Kafka Python Client](https://github.com/confluentinc/confluent-kafka-python)

---

### ✨ “Aggregate once, distribute infinitely.”

Real-time systems are not about computing *faster*, but about **delivering smarter**.



---

Would you like me to make a **shorter GitHub-style version** (around 1/3 the length) — suitable for your repository’s main page while keeping this detailed one as `docs/README_full.md`?

