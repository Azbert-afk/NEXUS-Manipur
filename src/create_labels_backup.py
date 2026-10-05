from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    to_date,
    when,
    lit
)

spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("NEXUS-Manipur-Create-Labels")
    .getOrCreate()
)

# Load processed weather features
weather = spark.read.parquet(
    "data/processed/phase1_features"
)

# Load documented flood events
events = spark.read.csv(
    "data/external/flood_events.csv",
    header=True,
    inferSchema=True
)

# Convert datetime to date
weather = weather.withColumn(
    "date",
    to_date(col("datetime"))
)

# Convert event dates to date
events = events.withColumn(
    "start_date",
    to_date(col("start_date"))
).withColumn(
    "end_date",
    to_date(col("end_date"))
)

# Create initial flood label
weather = weather.withColumn(
    "flood_event",
    lit(0)
)

# Apply every documented event
for event in events.collect():

    start_date = event["start_date"]
    end_date = event["end_date"]

    weather = weather.withColumn(
        "flood_event",
        when(
            (col("date") >= lit(start_date)) &
            (col("date") <= lit(end_date)),
            1
        ).otherwise(col("flood_event"))
    )

print("\n=== Flood Events Used ===")

events.select(
    "event_id",
    "start_date",
    "end_date",
    "location",
    "severity"
).show()

print("\n=== Flood Label Counts ===")

weather.groupBy(
    "flood_event"
).count().show()

print("\n=== 2025 Flood Labels ===")

weather.filter(
    (col("date") >= "2025-01-01") &
    (col("date") <= "2025-12-31") &
    (col("flood_event") == 1)
).groupBy(
    to_date(col("datetime")).alias("date")
).count().show(50)

# Save updated labelled dataset
output_path = "data/processed/phase1_labeled"

weather.write.mode("overwrite").parquet(output_path)

print("\nUpdated labeled dataset saved to:")
print(output_path)

spark.stop()