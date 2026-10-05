from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import (
    col,
    sum,
    avg,
    max
)

# ==========================================
# NEXUS-Manipur Phase 1
# Location-Aware Feature Engineering
# ==========================================

INPUT_PATH = "data/raw/manipur_weather.csv"
OUTPUT_PATH = "data/processed/phase1_features"

spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("NEXUS-Feature-Engineering")
    .getOrCreate()
)

print("==========================================")
print("NEXUS-Manipur Phase 1")
print("Feature Engineering")
print("==========================================")

print()
print("Reading weather data...")

df = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv(INPUT_PATH)
)

print(f"Input records: {df.count()}")

# ------------------------------------------
# Window definitions
# ------------------------------------------
# IMPORTANT:
# Windows are partitioned by location so
# rainfall calculations never mix locations.

window_24h = (
    Window
    .partitionBy("location")
    .orderBy("datetime")
    .rowsBetween(-23, 0)
)

window_72h = (
    Window
    .partitionBy("location")
    .orderBy("datetime")
    .rowsBetween(-71, 0)
)

window_7d = (
    Window
    .partitionBy("location")
    .orderBy("datetime")
    .rowsBetween(-167, 0)
)

# ------------------------------------------
# Feature creation
# ------------------------------------------

df = df.withColumn(
    "rainfall_24h",
    sum(col("precipitation")).over(window_24h)
)

df = df.withColumn(
    "rainfall_72h",
    sum(col("precipitation")).over(window_72h)
)

df = df.withColumn(
    "rainfall_7d",
    sum(col("precipitation")).over(window_7d)
)

df = df.withColumn(
    "soil_moisture_avg_24h",
    avg(col("soil_moisture")).over(window_24h)
)

df = df.withColumn(
    "max_rainfall_24h",
    max(col("precipitation")).over(window_24h)
)

# ------------------------------------------
# Save
# ------------------------------------------

print()
print("Saving engineered features...")

(
    df
    .write
    .mode("overwrite")
    .parquet(OUTPUT_PATH)
)

print()
print("==========================================")
print("Feature engineering completed.")
print("==========================================")
print(f"Output: {OUTPUT_PATH}")

print()
print("Locations:")
df.select("location").distinct().orderBy("location").show()

print("Feature columns:")
df.select(
    "location",
    "datetime",
    "rainfall_24h",
    "rainfall_72h",
    "rainfall_7d",
    "soil_moisture_avg_24h",
    "max_rainfall_24h"
).show(10, truncate=False)

spark.stop()