from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, sum
from pyspark.sql.window import Window
spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("NEXUS-Short-Rainfall-Analysis")
    .getOrCreate()
)

print("==========================================")
print("NEXUS-Manipur Phase 1")
print("Short-Term Rainfall Analysis")
print("==========================================")

# Load labelled dataset
df = spark.read.parquet(
    "data/processed/phase1_labeled"
)

# Training period only
df = df.filter(
    col("datetime") < "2025-01-01"
)

# Separate time sequence for each location

# Calculate short-term rainfall totals

window_6h = Window.partitionBy(
    "location"
).orderBy(
    "datetime"
).rowsBetween(
    -5, 0
)

window_12h = Window.partitionBy(
    "location"
).orderBy(
    "datetime"
).rowsBetween(
    -11, 0
)

window_48h = Window.partitionBy(
    "location"
).orderBy(
    "datetime"
).rowsBetween(
    -47, 0
)

df = df.withColumn(
    "rainfall_6h",
    sum("precipitation").over(window_6h)
)

df = df.withColumn(
    "rainfall_12h",
    sum("precipitation").over(window_12h)
)

df = df.withColumn(
    "rainfall_48h",
    sum("precipitation").over(window_48h)
)
features = [
    "rainfall_6h",
    "rainfall_12h",
    "rainfall_24h",
    "rainfall_48h",
    "rainfall_72h",
    "rainfall_7d"
]

print()
print("=== Flood vs Non-Flood Averages ===")

summary = df.groupBy(
    "flood_event"
).agg(
    *[
        avg(feature).alias(feature + "_avg")
        for feature in features
    ]
).orderBy(
    "flood_event"
)

summary.show(truncate=False)

print()
print("=== Correlation With Flood Label ===")

for feature in features:
    correlation = df.stat.corr(
        feature,
        "flood_event"
    )

    print(
        f"{feature:20s} : {correlation:.6f}"
    )

spark.stop()
