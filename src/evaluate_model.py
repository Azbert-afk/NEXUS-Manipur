from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.ml import PipelineModel
from pyspark.ml.functions import vector_to_array
from pyspark.ml.evaluation import BinaryClassificationEvaluator

spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("NEXUS-Model-Evaluation")
    .getOrCreate()
)

print("==========================================")
print("NEXUS-Manipur Phase 1")
print("Advanced Model Evaluation")
print("==========================================")

# Load model
model = PipelineModel.load(
    "models/flood_random_forest"
)

# Load labelled data
df = spark.read.parquet(
    "data/processed/phase1_labeled"
)

# Same time-based test set
test = df.filter(
    col("datetime") >= "2025-01-01"
)

print()
print("Test records:", test.count())

# Generate predictions
predictions = model.transform(test)

# Extract flood score
predictions = predictions.withColumn(
    "flood_probability",
    vector_to_array("probability")[1]
)

# ROC-AUC
roc_evaluator = BinaryClassificationEvaluator(
    labelCol="flood_event",
    rawPredictionCol="flood_probability",
    metricName="areaUnderROC"
)

roc_auc = roc_evaluator.evaluate(predictions)

# PR-AUC
pr_evaluator = BinaryClassificationEvaluator(
    labelCol="flood_event",
    rawPredictionCol="flood_probability",
    metricName="areaUnderPR"
)

pr_auc = pr_evaluator.evaluate(predictions)

print()
print("=== Advanced Evaluation ===")
print(f"ROC-AUC : {roc_auc:.4f}")
print(f"PR-AUC  : {pr_auc:.4f}")

spark.stop()