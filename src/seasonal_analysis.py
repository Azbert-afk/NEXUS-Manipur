from pyspark.sql import SparkSession
from pyspark.sql.functions import col, month, count, sum

spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("NEXUS-Seasonal-Analysis")
    .getOrCreate()
)

print("==========================================")
print("NEXUS-Manipur Phase 1")
print("Seasonal Flood Analysis")
print("==========================================")

df = spark.read.parquet(
    "data/processed/phase1_labeled"
)

# Training period only
df = df.filter(
    col("datetime") < "2025-01-01"
)

df = df.withColumn(
    "month",
    month("datetime")
)

summary = df.groupBy(
    "month"
).agg(
    count("*").alias("total_records"),
    sum("flood_event").alias("flood_records")
).withColumn(
    "flood_rate",
    col("flood_records") / col("total_records")
).orderBy(
    "month"
)

print()
print("=== Flood Rate By Month ===")

summary.show(
    20,
    truncate=False
)

spark.stop()