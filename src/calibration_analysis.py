from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, avg, count, lit
from pyspark.ml import PipelineModel
from pyspark.ml.functions import vector_to_array

spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("NEXUS-Calibration-Analysis")
    .getOrCreate()
)

print("==========================================")
print("NEXUS-Manipur Phase 1")
print("Probability Calibration Analysis")
print("==========================================")

model = PipelineModel.load(
    "models/flood_random_forest"
)

df = spark.read.parquet(
    "data/processed/phase1_labeled"
)

test = df.filter(
    col("datetime") >= "2025-01-01"
)

predictions = model.transform(test)

predictions = predictions.withColumn(
    "flood_score",
    vector_to_array("probability")[1]
)

# Create probability bins
predictions = predictions.withColumn(
    "probability_bin",
    when(col("flood_score") < 0.1, "0.0-0.1")
    .when(col("flood_score") < 0.2, "0.1-0.2")
    .when(col("flood_score") < 0.3, "0.2-0.3")
    .when(col("flood_score") < 0.4, "0.3-0.4")
    .when(col("flood_score") < 0.5, "0.4-0.5")
    .when(col("flood_score") < 0.6, "0.5-0.6")
    .when(col("flood_score") < 0.7, "0.6-0.7")
    .when(col("flood_score") < 0.8, "0.7-0.8")
    .when(col("flood_score") < 0.9, "0.8-0.9")
    .otherwise("0.9-1.0")
)

print()
print("=== Calibration By Score Range ===")

calibration = predictions.groupBy(
    "probability_bin"
).agg(
    count("*").alias("records"),
    avg("flood_score").alias("average_score"),
    avg("flood_event").alias("actual_flood_rate")
)

calibration.orderBy(
    "probability_bin"
).show(20, truncate=False)

# Brier score
brier = predictions.select(
    avg(
        (col("flood_score") - col("flood_event")) *
        (col("flood_score") - col("flood_event"))
    ).alias("brier_score")
).collect()[0]["brier_score"]

print()
print("=== Brier Score ===")
print(f"Brier Score: {brier:.6f}")

spark.stop()