from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import (
    col,
    sum,
    avg,
    max,
    lag
)

spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("NEXUS-Manipur-Feature-Engineering")
    .getOrCreate()
)

df = spark.read.csv(
    "data/raw/imphal_weather.csv",
    header=True,
    inferSchema=True
)

# Make sure records are ordered by time
df = df.orderBy("datetime")

# Window definitions
window_24h = Window.orderBy("datetime").rowsBetween(-23, 0)
window_72h = Window.orderBy("datetime").rowsBetween(-71, 0)
window_7d = Window.orderBy("datetime").rowsBetween(-167, 0)

# Create accumulated rainfall features
df = df.withColumn(
    "rainfall_24h",
    sum("precipitation").over(window_24h)
)

df = df.withColumn(
    "rainfall_72h",
    sum("precipitation").over(window_72h)
)

df = df.withColumn(
    "rainfall_7d",
    sum("precipitation").over(window_7d)
)

# Create rolling soil moisture average
df = df.withColumn(
    "soil_moisture_avg_24h",
    avg("soil_moisture").over(window_24h)
)

# Create maximum hourly rainfall over the previous 24 hours
df = df.withColumn(
    "max_rainfall_24h",
    max("precipitation").over(window_24h)
)

print("\n=== Feature-Engineered Dataset ===")

df.select(
    "datetime",
    "precipitation",
    "rainfall_24h",
    "rainfall_72h",
    "rainfall_7d",
    "soil_moisture_avg_24h",
    "max_rainfall_24h"
).show(20)

print("\n=== Dataset Structure ===")
df.printSchema()

# Save processed data
output_path = "data/processed/phase1_features"

df.write.mode("overwrite").parquet(output_path)

print("\nProcessed dataset saved to:")
print(output_path)

spark.stop()