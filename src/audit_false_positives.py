from pyspark.sql import SparkSession
from pyspark.ml.functions import vector_to_array
from pyspark.sql.functions import col
from pyspark.ml import PipelineModel


spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("NEXUS-False-Positive-Audit")
    .getOrCreate()
)

print("=" * 55)
print("NEXUS-Manipur")
print("False Positive / High Risk Audit")
print("=" * 55)

# Load labelled data
df = spark.read.parquet(
    "data/processed/phase1_labeled"
)

# Only 2025 test period
test = df.filter(
    col("datetime") >= "2025-01-01"
)

# Load trained Random Forest
model = PipelineModel.load(
    "models/flood_random_forest"
)

# Generate predictions
predictions = model.transform(test)

print("\nTest records:", predictions.count())

# Spark ML probability vector:
# probability[1] = probability of flood
predictions = predictions.withColumn(
    "flood_probability",
    vector_to_array("probability")[1]
)
print("\n=== High Probability Non-Flood Records ===")

false_positives = predictions.filter(
    (col("flood_event") == 0) &
    (col("flood_probability") >= 0.90)
)

false_positives.select(
    "location",
    "datetime",
    "flood_event",
    "flood_probability",
    "rainfall_24h",
    "rainfall_72h",
    "rainfall_7d",
    "soil_moisture_avg_24h",
    "max_rainfall_24h"
).orderBy(
    col("flood_probability").desc()
).show(30, truncate=False)

print("\n=== High Probability Non-Flood Count By Location ===")

false_positives.groupBy(
    "location"
).count().orderBy(
    col("count").desc()
).show()

print("\n=== Highest Rainfall Among Non-Flood Records ===")

test.filter(
    col("flood_event") == 0
).select(
    "location",
    "datetime",
    "rainfall_24h",
    "rainfall_72h",
    "rainfall_7d",
    "soil_moisture_avg_24h",
    "max_rainfall_24h"
).orderBy(
    col("rainfall_72h").desc()
).show(30, truncate=False)

spark.stop()