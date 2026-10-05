from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lag, avg
from pyspark.sql.window import Window

spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("NEXUS-Pressure-Feature-Analysis")
    .getOrCreate()
)

print("==========================================")
print("NEXUS-Manipur Phase 1")
print("Pressure Feature Analysis")
print("==========================================")

df = spark.read.parquet(
    "data/processed/phase1_labeled"
)

# Use training period only
df = df.filter(
    col("datetime") < "2025-01-01"
)

# Time order separately for each location
window = Window.partitionBy(
    "location"
).orderBy(
    "datetime"
)

# Pressure changes
df = df.withColumn(
    "pressure_6h_change",
    col("pressure") - lag("pressure", 6).over(window)
)

df = df.withColumn(
    "pressure_12h_change",
    col("pressure") - lag("pressure", 12).over(window)
)

df = df.withColumn(
    "pressure_24h_change",
    col("pressure") - lag("pressure", 24).over(window)
)

# Positive value means pressure dropped
df = df.withColumn(
    "pressure_drop_6h",
    -col("pressure_6h_change")
)

df = df.withColumn(
    "pressure_drop_12h",
    -col("pressure_12h_change")
)

df = df.withColumn(
    "pressure_drop_24h",
    -col("pressure_24h_change")
)

print()
print("=== Pressure Feature Averages ===")

features = [
    "pressure",
    "pressure_drop_6h",
    "pressure_drop_12h",
    "pressure_drop_24h"
]

summary = df.groupBy(
    "flood_event"
).agg(
    *[
        avg(feature).alias(feature + "_avg")
        for feature in features
    ]
).orderBy("flood_event")

summary.show(truncate=False)

print()
print("=== Correlation With Flood Label ===")

for feature in features:
    correlation = df.stat.corr(
        feature,
        "flood_event"
    )

    print(
        f"{feature:25s} : {correlation:.6f}"
    )

spark.stop()