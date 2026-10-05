from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, avg
from pyspark.ml.feature import VectorAssembler, StringIndexer
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml import Pipeline
from pyspark.ml.functions import vector_to_array
from pyspark.ml.regression import IsotonicRegression
from pyspark.ml.evaluation import BinaryClassificationEvaluator

spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("NEXUS-Calibrated-Random-Forest")
    .getOrCreate()
)

print("==========================================")
print("NEXUS-Manipur Phase 1")
print("Probability Calibration Experiment")
print("==========================================")

df = spark.read.parquet(
    "data/processed/phase1_labeled"
)

# ------------------------------------------
# Features
# ------------------------------------------

numeric_features = [
    "temperature",
    "humidity",
    "precipitation",
    "pressure",
    "wind_speed",
    "soil_moisture",
    "rainfall_24h",
    "rainfall_72h",
    "rainfall_7d",
    "soil_moisture_avg_24h",
    "max_rainfall_24h"
]

location_indexer = StringIndexer(
    inputCol="location",
    outputCol="location_index",
    handleInvalid="keep"
)

feature_columns = numeric_features + ["location_index"]

df = df.dropna(
    subset=numeric_features + ["flood_event", "location"]
)

assembler = VectorAssembler(
    inputCols=feature_columns,
    outputCol="features"
)

rf = RandomForestClassifier(
    featuresCol="features",
    labelCol="flood_event",
    weightCol="class_weight",
    numTrees=100,
    maxDepth=10,
    seed=42
)

pipeline = Pipeline(
    stages=[
        location_indexer,
        assembler,
        rf
    ]
)

# ------------------------------------------
# Time periods
# ------------------------------------------

train = df.filter(
    col("datetime") < "2024-01-01"
)

calibration = df.filter(
    (col("datetime") >= "2024-01-01") &
    (col("datetime") < "2025-01-01")
)

test = df.filter(
    col("datetime") >= "2025-01-01"
)

print()
print("=== Dataset Split ===")
print("Training:", train.count())
print("Calibration:", calibration.count())
print("Final Test:", test.count())

# ------------------------------------------
# Class weights from training only
# ------------------------------------------

class_counts = train.groupBy(
    "flood_event"
).count().collect()

class_count_dict = {
    int(row["flood_event"]): row["count"]
    for row in class_counts
}

total_train = sum(class_count_dict.values())
num_classes = len(class_count_dict)

weight_0 = total_train / (
    num_classes * class_count_dict[0]
)

weight_1 = total_train / (
    num_classes * class_count_dict[1]
)

train = train.withColumn(
    "class_weight",
    when(col("flood_event") == 1, weight_1)
    .otherwise(weight_0)
)

print()
print("=== Training Class Weights ===")
print("Class 0:", weight_0)
print("Class 1:", weight_1)

# ------------------------------------------
# Train base Random Forest
# ------------------------------------------

print()
print("Training base Random Forest...")

base_model = pipeline.fit(train)

print("Training completed.")

# ------------------------------------------
# Raw probabilities
# ------------------------------------------

calibration_pred = base_model.transform(calibration)
test_pred = base_model.transform(test)

calibration_pred = calibration_pred.withColumn(
    "raw_score",
    vector_to_array("probability")[1]
)

test_pred = test_pred.withColumn(
    "raw_score",
    vector_to_array("probability")[1]
)

# ------------------------------------------
# Fit isotonic calibration
# ------------------------------------------

print()
print("Fitting isotonic calibration...")

calibration_features = VectorAssembler(
    inputCols=["raw_score"],
    outputCol="calibration_features"
)

calibration_data = calibration_features.transform(
    calibration_pred
)

isotonic = IsotonicRegression(
    featuresCol="calibration_features",
    labelCol="flood_event",
    predictionCol="calibrated_probability",
    isotonic=True
)

calibrator = isotonic.fit(calibration_data)

print("Calibration completed.")

# ------------------------------------------
# Apply calibration to test set
# ------------------------------------------

test_data = calibration_features.transform(
    test_pred
)

calibrated_test = calibrator.transform(
    test_data
)

# ------------------------------------------
# Brier scores
# ------------------------------------------

raw_brier = test_data.select(
    avg(
        (col("raw_score") - col("flood_event")) *
        (col("raw_score") - col("flood_event"))
    ).alias("brier")
).collect()[0]["brier"]

calibrated_brier = calibrated_test.select(
    avg(
        (col("calibrated_probability") - col("flood_event")) *
        (col("calibrated_probability") - col("flood_event"))
    ).alias("brier")
).collect()[0]["brier"]

print()
print("=== Brier Score Comparison ===")
print(f"Raw RF Brier Score       : {raw_brier:.6f}")
print(f"Calibrated Brier Score   : {calibrated_brier:.6f}")

# ------------------------------------------
# PR-AUC comparison
# ------------------------------------------

raw_pr = BinaryClassificationEvaluator(
    labelCol="flood_event",
    rawPredictionCol="raw_score",
    metricName="areaUnderPR"
).evaluate(test_data)

calibrated_pr = BinaryClassificationEvaluator(
    labelCol="flood_event",
    rawPredictionCol="calibrated_probability",
    metricName="areaUnderPR"
).evaluate(calibrated_test)

print()
print("=== PR-AUC Comparison ===")
print(f"Raw RF PR-AUC       : {raw_pr:.4f}")
print(f"Calibrated PR-AUC   : {calibrated_pr:.4f}")

# ------------------------------------------
# Example calibrated scores
# ------------------------------------------

print()
print("=== Example Score Conversion ===")

calibrated_test.select(
    "raw_score",
    "calibrated_probability",
    "flood_event"
).orderBy(
    col("raw_score").desc()
).show(20, truncate=False)

spark.stop()