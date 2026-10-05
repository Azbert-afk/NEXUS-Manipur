import csv
import json
import urllib.request

# ==========================================
# NEXUS-Manipur Phase 1
# Multi-Location Historical Weather Collection
# ==========================================

START_DATE = "2020-01-01"
END_DATE = "2025-12-31"

OUTPUT_FILE = "data/raw/manipur_weather.csv"

# Locations and coordinates
LOCATIONS = {
    "Imphal": (24.8170, 93.9368),
    "Thoubal": (24.6388, 94.0100),
    "Bishnupur": (24.6285, 93.7690),
    "Senapati": (25.2670, 94.0270),
    "Kakching": (24.4980, 94.0080),
    "Churachandpur": (24.3333, 93.6833)
}

print("==========================================")
print("NEXUS-Manipur Phase 1")
print("Multi-Location Weather Collection")
print("==========================================")
print()
print(f"Period: {START_DATE} to {END_DATE}")
print(f"Locations: {len(LOCATIONS)}")
print()

all_records = []

for location, coordinates in LOCATIONS.items():

    latitude, longitude = coordinates

    print("------------------------------------------")
    print(f"Collecting: {location}")
    print(f"Latitude:  {latitude}")
    print(f"Longitude: {longitude}")
    print("------------------------------------------")

    URL = (
        "https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={latitude}"
        f"&longitude={longitude}"
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

        for i in range(len(times)):

            all_records.append([
                location,
                times[i],
                temperature[i],
                humidity[i],
                precipitation[i],
                pressure[i],
                wind_speed[i],
                soil_moisture[i]
            ])

        print(f"Records collected: {len(times)}")

    except Exception as e:

        print(f"ERROR collecting {location}: {e}")


print()
print("Saving combined dataset...")

with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.writer(file)

    writer.writerow([
        "location",
        "datetime",
        "temperature",
        "humidity",
        "precipitation",
        "pressure",
        "wind_speed",
        "soil_moisture"
    ])

    writer.writerows(all_records)


print()
print("==========================================")
print("Data collection completed.")
print("==========================================")
print(f"Locations collected: {len(LOCATIONS)}")
print(f"Total records: {len(all_records)}")
print(f"Saved to: {OUTPUT_FILE}")