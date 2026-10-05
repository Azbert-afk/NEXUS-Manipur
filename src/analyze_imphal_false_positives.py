from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.ml import PipelineModel
from pyspark.ml.functions import vector_to_array

spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("NEXUS-Imphal-False-Positive-Analysis")
    .getOrCreate()
)

print("==========================================")
print("NEXUS-Manipur Phase 1")
print("Imphal False Positive Analysis")
print("==========================================")

# Load current main model
model = PipelineModel.load(
    "models/flood_random_forest"
)

# Load labelled dataset
df = spark.read.parquet(
    "data/processed/phase1_labeled"
)

# Same test period used by the main model
test = df.filter(
    col("datetime") >= "2025-01-01"
)

# Generate predictions
predictions = model.transform(test)

predictions = predictions.withColumn(
    "flood_probability",
    vector_to_array("probability")[1]
)

# ------------------------------------------
# Imphal false positives
# ------------------------------------------

false_positives = predictions.filter(
    (col("location") == "Imphal") &
    (col("flood_event") == 0) &
    (col("prediction") == 1)
)

print()
print("=== Top Imphal False Positives ===")

false_positives.select(
    "datetime",
    "flood_probability",
    "pressure",
    "rainfall_24h",
    "rainfall_72h",
    "rainfall_7d",
    "soil_moisture",
    "soil_moisture_avg_24h",
    "temperature",
    "humidity"
).orderBy(
    col("flood_probability").desc()
).show(20, truncate=False)

# ------------------------------------------
# Imphal real flood records
# ------------------------------------------

flood_records = predictions.filter(
    (col("location") == "Imphal") &
    (col("flood_event") == 1)
)

print()
print("=== Imphal Flood Records ===")

flood_records.select(
    "datetime",
    "flood_probability",
    "pressure",
    "rainfall_24h",
    "rainfall_72h",
    "rainfall_7d",
    "soil_moisture",
    "soil_moisture_avg_24h",
    "temperature",
    "humidity"
).show(20, truncate=False)

# ------------------------------------------
# Average feature values
# ------------------------------------------

print()
print("=== Average Feature Values ===")

print("Imphal False Positives:")
false_positives.select(
    "pressure",
    "rainfall_24h",
    "rainfall_72h",
    "rainfall_7d",
    "soil_moisture",
    "soil_moisture_avg_24h",
    "temperature",
    "humidity"
).describe().show()

print("Imphal Flood Records:")
flood_records.select(
    "pressure",
    "rainfall_24h",
    "rainfall_72h",
    "rainfall_7d",
    "soil_moisture",
    "soil_moisture_avg_24h",
    "temperature",
    "humidity"
).describe().show()

spark.stop()