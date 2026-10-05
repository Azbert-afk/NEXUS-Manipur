from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, max, min

spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("NEXUS-Flood-Feature-Check")
    .getOrCreate()
)

print("=" * 50)
print("NEXUS-Manipur")
print("Flood Feature Diagnostic")
print("=" * 50)

df = spark.read.parquet("data/processed/phase1_labeled")

features = [
    "rainfall_24h",
    "rainfall_72h",
    "rainfall_7d",
    "soil_moisture_avg_24h",
    "max_rainfall_24h"
]

print("\n=== 2025 Flood vs Non-Flood ===")

df_2025 = df.filter(
    col("datetime") >= "2025-01-01"
)

df_2025.groupBy("flood_event").agg(
    *[
        avg(col(f)).alias(f"{f}_avg")
        for f in features
    ],
    *[
        max(col(f)).alias(f"{f}_max")
        for f in features
    ]
).orderBy("flood_event").show(truncate=False)

print("\n=== 2025 Flood Features By Location ===")

df_2025.filter(
    col("flood_event") == 1
).groupBy("location").agg(
    *[
        avg(col(f)).alias(f"{f}_avg")
        for f in features
    ],
    *[
        max(col(f)).alias(f"{f}_max")
        for f in features
    ]
).orderBy("location").show(truncate=False)

print("\n=== Individual 2025 Flood Records ===")

df_2025.filter(
    col("flood_event") == 1
).select(
    "location",
    "datetime",
    "rainfall_24h",
    "rainfall_72h",
    "rainfall_7d",
    "soil_moisture_avg_24h",
    "max_rainfall_24h"
).orderBy(
    "location",
    "datetime"
).show(100, truncate=False)

spark.stop()