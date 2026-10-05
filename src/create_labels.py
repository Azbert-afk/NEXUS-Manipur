from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    to_date,
    when,
    lit
)

# ==========================================
# NEXUS-Manipur Phase 1
# Location-Aware Flood Label Creation
# ==========================================

spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("NEXUS-Manipur-Create-Labels")
    .getOrCreate()
)

# ------------------------------------------
# Load weather features
# ------------------------------------------

weather = spark.read.parquet(
    "data/processed/phase1_features"
)

# ------------------------------------------
# Load documented flood events
# ------------------------------------------

events = spark.read.csv(
    "data/external/flood_events.csv",
    header=True,
    inferSchema=True
)

# ------------------------------------------
# Convert dates
# ------------------------------------------

weather = weather.withColumn(
    "date",
    to_date(col("datetime"))
)

events = (
    events
    .withColumn("start_date", to_date(col("start_date")))
    .withColumn("end_date", to_date(col("end_date")))
)

# ------------------------------------------
# Start with no flood
# ------------------------------------------

weather = weather.withColumn(
    "flood_event",
    lit(0)
)

# ------------------------------------------
# Apply each documented event
# ------------------------------------------

print()
print("=== Applying Flood Events ===")

for event in events.collect():

    event_id = event["event_id"]
    location = event["location"]
    start_date = event["start_date"]
    end_date = event["end_date"]

    print(
        f"Applying {event_id}: "
        f"{location} | {start_date} -> {end_date}"
    )

    weather = weather.withColumn(
        "flood_event",
        when(
            (col("location") == lit(location)) &
            (col("date") >= lit(start_date)) &
            (col("date") <= lit(end_date)),
            1
        ).otherwise(col("flood_event"))
    )

# ------------------------------------------
# Display events
# ------------------------------------------

print()
print("=== Flood Events Used ===")

events.select(
    "event_id",
    "start_date",
    "end_date",
    "location",
    "hazard_type",
    "severity"
).show(truncate=False)

# ------------------------------------------
# Overall label counts
# ------------------------------------------

print()
print("=== Flood Label Counts ===")

weather.groupBy(
    "flood_event"
).count().orderBy(
    "flood_event"
).show()

# ------------------------------------------
# Labels by location
# ------------------------------------------

print()
print("=== Flood Labels By Location ===")

weather.groupBy(
    "location",
    "flood_event"
).count().orderBy(
    "location",
    "flood_event"
).show()

# ------------------------------------------
# 2025 flood labels by location
# ------------------------------------------

print()
print("=== 2025 Flood Labels By Location ===")

weather.filter(
    (col("date") >= "2025-01-01") &
    (col("date") <= "2025-12-31") &
    (col("flood_event") == 1)
).groupBy(
    "location"
).count().orderBy(
    "location"
).show()

# ------------------------------------------
# Save labelled dataset
# ------------------------------------------

output_path = "data/processed/phase1_labeled"

weather.write.mode("overwrite").parquet(
    output_path
)

print()
print("==========================================")
print("Updated labeled dataset saved.")
print("==========================================")
print(f"Output: {output_path}")

spark.stop()