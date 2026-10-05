from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, stddev

spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("NEXUS-Rainfall-Feature-Analysis")
    .getOrCreate()
)

print("==========================================")
print("NEXUS-Manipur Phase 1")
print("Rainfall Feature Analysis")
print("==========================================")

df = spark.read.parquet(
    "data/processed/phase1_labeled"
)

# Use only the training period so we do not inspect
# the final 2025 test period while designing features.
train = df.filter(
    col("datetime") < "2025-01-01"
)

rainfall_features = [
    "rainfall_24h",
    "rainfall_72h",
    "rainfall_7d",
    "max_rainfall_24h",
    "soil_moisture",
    "soil_moisture_avg_24h"
]

print()
print("=== Training Data ===")
print("Training records:", train.count())

print()
print("=== Flood vs Non-Flood Feature Averages ===")

summary = train.groupBy(
    "flood_event"
).agg(
    *[
        avg(c).alias(c + "_avg")
        for c in rainfall_features
    ]
).orderBy("flood_event")

summary.show(truncate=False)

print()
print("=== Flood vs Non-Flood Standard Deviations ===")

std_summary = train.groupBy(
    "flood_event"
).agg(
    *[
        stddev(c).alias(c + "_std")
        for c in rainfall_features
    ]
).orderBy("flood_event")

std_summary.show(truncate=False)

print()
print("=== Feature Correlation With Flood Label ===")

for feature in rainfall_features:
    correlation = train.stat.corr(
        feature,
        "flood_event"
    )

    print(
        f"{feature:30s} : {correlation:.6f}"
    )

spark.stop()