from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf
from pyspark.sql.types import DoubleType
from pyspark.ml import PipelineModel
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("NEXUS-Threshold-Test")
    .getOrCreate()
)

print("=" * 50)
print("NEXUS-Manipur")
print("Random Forest Threshold Testing")
print("=" * 50)

# Load labelled data
df = spark.read.parquet("data/processed/phase1_labeled_48h")

# Same time-based test period
test = df.filter(
    col("datetime") >= "2025-01-01"
)

# Load trained model
model = PipelineModel.load("models/flood_random_forest_48h")

# Generate predictions
predictions = model.transform(test)

print("\nTest records:", predictions.count())

# Extract probability of flood class
get_flood_probability = udf(
    lambda v: float(v[1]),
    DoubleType()
)

predictions = predictions.withColumn(
    "flood_probability",
    get_flood_probability(col("probability"))
)

print("\n=== Threshold Results ===")

thresholds = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90]

for threshold in thresholds:

    result = predictions.withColumn(
        "threshold_prediction",
        (col("flood_probability") >= threshold).cast("double")
    )

    tp = result.filter(
        (col("flood_event") == 1) &
        (col("threshold_prediction") == 1)
    ).count()

    fp = result.filter(
        (col("flood_event") == 0) &
        (col("threshold_prediction") == 1)
    ).count()

    fn = result.filter(
        (col("flood_event") == 1) &
        (col("threshold_prediction") == 0)
    ).count()

    tn = result.filter(
        (col("flood_event") == 0) &
        (col("threshold_prediction") == 0)
    ).count()

    if tp + fp > 0:
        precision = tp / (tp + fp)
    else:
        precision = 0.0

    if tp + fn > 0:
        recall = tp / (tp + fn)
    else:
        recall = 0.0

    if precision + recall > 0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0.0

    print(
        f"Threshold: {threshold:.2f} | "
        f"TP: {tp:4d} | "
        f"FP: {fp:4d} | "
        f"FN: {fn:4d} | "
        f"TN: {tn:5d} | "
        f"Precision: {precision:.4f} | "
        f"Recall: {recall:.4f} | "
        f"F1: {f1:.4f}"
    )

print("\n=== Highest Flood Probabilities ===")

predictions.select(
    "location",
    "datetime",
    "flood_event",
    "flood_probability"
).orderBy(
    col("flood_probability").desc()
).show(30, truncate=False)

spark.stop()