from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when
from pyspark.ml.feature import VectorAssembler, StringIndexer
from pyspark.ml.classification import RandomForestClassifier

from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml import Pipeline

# ==========================================
# NEXUS-Manipur Phase 1
# Multi-Location Random Forest Training
# ==========================================

spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("NEXUS-Manipur-Random-Forest")
    .getOrCreate()
)

# ------------------------------------------
# Load labelled dataset
# ------------------------------------------

df = spark.read.parquet(
    "data/processed/phase1_labeled_48h"
)

print("==========================================")
print("NEXUS-Manipur Phase 1")
print("Random Forest Training")
print("==========================================")

print()
print("Total records:", df.count())

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
    "rainfall_48h",
    "rainfall_72h",
    "rainfall_7d",
    "soil_moisture_avg_24h",
    "max_rainfall_24h"
]

# Convert location into a categorical numeric
location_indexer = StringIndexer(
    inputCol="location",
    outputCol="location_index",
    handleInvalid="keep"
)


feature_columns = numeric_features + ["location_index" ]
# ------------------------------------------
# Remove missing values
# ------------------------------------------

df = df.dropna(
    subset=numeric_features + ["flood_event", "location"]
)

# ------------------------------------------
# Feature assembler
# ------------------------------------------

assembler = VectorAssembler(
    inputCols=feature_columns,
    outputCol="features"
)

# ------------------------------------------
# Random Forest
# ------------------------------------------

rf = RandomForestClassifier(
    featuresCol="features",
    labelCol="flood_event",
    weightCol="class_weight",
    numTrees=100,
    maxDepth=10,
    seed=42
)
# ------------------------------------------
# Pipeline
# ------------------------------------------

pipeline = Pipeline(
    stages=[
        location_indexer,
        assembler,
        rf
    ]
)
# ==========================================
# Time-based train/test split
# ==========================================

train = df.filter(
    col("datetime") < "2025-01-01"
)

test = df.filter(
    col("datetime") >= "2025-01-01"
)
# Calculate class weights
class_counts = train.groupBy("flood_event").count().collect()

class_count_dict = {
    int(row["flood_event"]): row["count"]
    for row in class_counts
}

total_train = sum(class_count_dict.values())
num_classes = len(class_count_dict)

weight_0 = total_train / (num_classes * class_count_dict[0])
weight_1 = total_train / (num_classes * class_count_dict[1])

print("\n=== Class Weights ===")
print("Class 0 weight:", weight_0)
print("Class 1 weight:", weight_1)

train = train.withColumn(
    "class_weight",
    when(col("flood_event") == 1, weight_1)
    .otherwise(weight_0)
)
print()
print("=== Dataset Split ===")

print("Training records:", train.count())
print("Testing records:", test.count())

print()
print("=== Training Label Distribution ===")

train.groupBy(
    "flood_event"
).count().orderBy(
    "flood_event"
).show()

print()
print("=== Testing Label Distribution ===")

test.groupBy(
    "flood_event"
).count().orderBy(
    "flood_event"
).show()

# ==========================================
# Train
# ==========================================

print()
print("Training Random Forest...")

model = pipeline.fit(train)

print("Training completed.")

# ==========================================
# Predictions
# ==========================================

predictions = model.transform(test)

print()
print("=== Sample Predictions ===")

predictions.select(
    "location",
    "datetime",
    "flood_event",
    "prediction",
    "probability"
).show(20, truncate=False)

# ==========================================
# Weighted evaluation
# ==========================================

accuracy_evaluator = MulticlassClassificationEvaluator(
    labelCol="flood_event",
    predictionCol="prediction",
    metricName="accuracy"
)

weighted_f1_evaluator = MulticlassClassificationEvaluator(
    labelCol="flood_event",
    predictionCol="prediction",
    metricName="f1"
)

accuracy = accuracy_evaluator.evaluate(predictions)
weighted_f1 = weighted_f1_evaluator.evaluate(predictions)

# ==========================================
# Class-specific evaluation
# ==========================================

# Evaluate specifically for flood class = 1

flood_precision_evaluator = MulticlassClassificationEvaluator(
    labelCol="flood_event",
    predictionCol="prediction",
    metricName="precisionByLabel",
    metricLabel=1.0
)

flood_recall_evaluator = MulticlassClassificationEvaluator(
    labelCol="flood_event",
    predictionCol="prediction",
    metricName="recallByLabel",
    metricLabel=1.0
)

flood_f1_evaluator = MulticlassClassificationEvaluator(
    labelCol="flood_event",
    predictionCol="prediction",
    metricName="fMeasureByLabel",
    metricLabel=1.0
)

flood_precision = flood_precision_evaluator.evaluate(
    predictions
)

flood_recall = flood_recall_evaluator.evaluate(
    predictions
)

flood_f1 = flood_f1_evaluator.evaluate(
    predictions
)

print()
print("=== Model Evaluation ===")

print(f"Accuracy             : {accuracy:.4f}")
print(f"Weighted F1          : {weighted_f1:.4f}")
print(f"Flood Precision      : {flood_precision:.4f}")
print(f"Flood Recall         : {flood_recall:.4f}")
print(f"Flood F1             : {flood_f1:.4f}")

# ==========================================
# Confusion matrix
# ==========================================

print()
print("=== Confusion Matrix ===")

predictions.groupBy(
    "flood_event",
    "prediction"
).count().orderBy(
    "flood_event",
    "prediction"
).show()

# ==========================================
# Predictions by location
# ==========================================

print()
print("=== Predictions By Location ===")

predictions.groupBy(
    "location",
    "flood_event",
    "prediction"
).count().orderBy(
    "location",
    "flood_event",
    "prediction"
).show(100)

# ==========================================
# Save model
# ==========================================

model_path = "models/flood_random_forest_48h"

model.write().overwrite().save(
    model_path
)

print()
print("==========================================")
print("Model saved successfully.")
print("==========================================")
print(f"Model path: {model_path}")

spark.stop()