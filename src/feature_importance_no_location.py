from pyspark.sql import SparkSession
from pyspark.ml import PipelineModel

spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("NEXUS-Feature-Importance-No-Location")
    .getOrCreate()
)

model = PipelineModel.load(
    "models/flood_random_forest_no_location"
)

rf_model = model.stages[-1]

feature_names = [
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

importances = rf_model.featureImportances.toArray()

print("==========================================")
print("NEXUS-Manipur Phase 1")
print("Feature Importance - No Location")
print("==========================================")

for name, importance in sorted(
    zip(feature_names, importances),
    key=lambda x: x[1],
    reverse=True
):
    print(f"{name:30s} : {importance:.6f}")

spark.stop()