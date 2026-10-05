from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml import Pipeline


# ==========================================
# NEXUS-Manipur Phase 1
# Random Forest Training
# ==========================================

spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("NEXUS-Manipur-Random-Forest")
    .getOrCreate()
)


# Load labelled dataset
df = spark.read.parquet(
    "data/processed/phase1_labeled"
)


# Features used by the model
feature_columns = [
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


# Remove records with missing feature values
df = df.dropna(
    subset=feature_columns + ["flood_event"]
)


# Create feature vector
assembler = VectorAssembler(
    inputCols=feature_columns,
    outputCol="features"
)


# Random Forest classifier
rf = RandomForestClassifier(
    labelCol="flood_event",
    featuresCol="features",
    numTrees=100,
    maxDepth=10,
    seed=42
)


# Build pipeline
pipeline = Pipeline(
    stages=[
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


print("\n=== Dataset Split ===")

print("Training records:", train.count())
print("Testing records:", test.count())


print("\n=== Training Label Distribution ===")

train.groupBy(
    "flood_event"
).count().show()


print("\n=== Testing Label Distribution ===")

test.groupBy(
    "flood_event"
).count().show()


# ==========================================
# Train model
# ==========================================

print("\nTraining Random Forest...")

model = pipeline.fit(train)

print("Training completed.")


# ==========================================
# Make predictions
# ==========================================

predictions = model.transform(test)


print("\n=== Sample Predictions ===")

predictions.select(
    "datetime",
    "flood_event",
    "prediction",
    "probability"
).show(20, truncate=False)


# ==========================================
# Evaluation
# ==========================================

accuracy_evaluator = MulticlassClassificationEvaluator(
    labelCol="flood_event",
    predictionCol="prediction",
    metricName="accuracy"
)

f1_evaluator = MulticlassClassificationEvaluator(
    labelCol="flood_event",
    predictionCol="prediction",
    metricName="f1"
)

precision_evaluator = MulticlassClassificationEvaluator(
    labelCol="flood_event",
    predictionCol="prediction",
    metricName="weightedPrecision"
)

recall_evaluator = MulticlassClassificationEvaluator(
    labelCol="flood_event",
    predictionCol="prediction",
    metricName="weightedRecall"
)


accuracy = accuracy_evaluator.evaluate(predictions)
f1 = f1_evaluator.evaluate(predictions)
precision = precision_evaluator.evaluate(predictions)
recall = recall_evaluator.evaluate(predictions)


print("\n=== Model Evaluation ===")

print(f"Accuracy : {accuracy:.4f}")
print(f"F1 Score : {f1:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall   : {recall:.4f}")


# ==========================================
# Confusion matrix
# ==========================================

print("\n=== Confusion Matrix ===")

predictions.groupBy(
    "flood_event",
    "prediction"
).count().orderBy(
    "flood_event",
    "prediction"
).show()


# ==========================================
# Save model
# ==========================================

model_path = "models/flood_random_forest"

model.write().overwrite().save(model_path)

print("\nModel saved to:")
print(model_path)


spark.stop()