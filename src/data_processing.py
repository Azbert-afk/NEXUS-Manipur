from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("NEXUS-Manipur-Phase1")
    .getOrCreate()
)

df = spark.read.csv(
    "data/raw/imphal_weather.csv",
    header=True,
    inferSchema=True
)

print("\n=== NEXUS-Manipur Weather Dataset ===")

print("\nFirst 10 records:")
df.show(10)

print("\n=== Dataset Structure ===")
df.printSchema()

print("\n=== Number of Records ===")
print(df.count())

print("\n=== Column Names ===")
print(df.columns)

print("\n=== Missing Values ===")

for column in df.columns:
    missing = df.filter(df[column].isNull()).count()
    print(f"{column}: {missing}")

spark.stop()