import csv
import json
import urllib.request

# ==========================================
# NEXUS-Manipur Phase 1
# Historical Weather Data Collection
# ==========================================

# Imphal coordinates
LATITUDE = 24.8170
LONGITUDE = 93.9368

# Historical period
START_DATE = "2020-01-01"
END_DATE = "2025-12-31"

# Output file
OUTPUT_FILE = "data/raw/imphal_weather.csv"

# Open-Meteo Historical Weather API
URL = (
    "https://archive-api.open-meteo.com/v1/archive"
    f"?latitude={LATITUDE}"
    f"&longitude={LONGITUDE}"
    f"&start_date={START_DATE}"
    f"&end_date={END_DATE}"
    "&hourly="
    "temperature_2m,"
    "relative_humidity_2m,"
    "precipitation,"
    "pressure_msl,"
    "wind_speed_10m,"
    "soil_moisture_0_to_7cm"
    "&timezone=Asia%2FKolkata"
)

print("==========================================")
print("NEXUS-Manipur Phase 1")
print("Historical Weather Data Collection")
print("==========================================")
print()
print("Location: Imphal")
print(f"Latitude: {LATITUDE}")
print(f"Longitude: {LONGITUDE}")
print(f"Period: {START_DATE} to {END_DATE}")
print()
print("Connecting to Open-Meteo...")

try:
    with urllib.request.urlopen(URL) as response:
        data = json.loads(response.read().decode())

    hourly = data["hourly"]

    times = hourly["time"]
    temperature = hourly["temperature_2m"]
    humidity = hourly["relative_humidity_2m"]
    precipitation = hourly["precipitation"]
    pressure = hourly["pressure_msl"]
    wind_speed = hourly["wind_speed_10m"]
    soil_moisture = hourly["soil_moisture_0_to_7cm"]

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "datetime",
            "temperature",
            "humidity",
            "precipitation",
            "pressure",
            "wind_speed",
            "soil_moisture"
        ])

        for i in range(len(times)):
            writer.writerow([
                times[i],
                temperature[i],
                humidity[i],
                precipitation[i],
                pressure[i],
                wind_speed[i],
                soil_moisture[i]
            ])

    print()
    print("Data collection completed successfully.")
    print(f"Records collected: {len(times)}")
    print(f"Saved to: {OUTPUT_FILE}")

except Exception as e:
    print()
    print("ERROR: Data collection failed.")
    print(e)