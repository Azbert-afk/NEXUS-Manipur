import streamlit as st
import requests
from datetime import date, timedelta
from statistics import mean


# =========================================================
# NEXUS-MANIPUR
# Phase 1 - Future Prediction Prototype
# =========================================================


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="NEXUS-Manipur",
    page_icon="🌧️",
    layout="wide"
)


# ---------------------------------------------------------
# LOCATION DATA
# ---------------------------------------------------------

LOCATIONS = {
    "Imphal": {
        "lat": 24.8170,
        "lon": 93.9368
    },
    "Thoubal": {
        "lat": 24.6388,
        "lon": 94.0100
    },
    "Bishnupur": {
        "lat": 24.6285,
        "lon": 93.7690
    },
    "Senapati": {
        "lat": 25.2670,
        "lon": 94.0270
    },
    "Kakching": {
        "lat": 24.4980,
        "lon": 94.0080
    },
    "Churachandpur": {
        "lat": 24.3333,
        "lon": 93.6833
    }
}


# ---------------------------------------------------------
# OPEN-METEO
# ---------------------------------------------------------

@st.cache_data(ttl=900)
def get_weather(latitude, longitude):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "hourly": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "precipitation,"
            "surface_pressure,"
            "wind_speed_10m,"
            "soil_moisture_0_to_7cm"
        ),

        "forecast_days": 16,
        "timezone": "auto"
    }

    response = requests.get(
        url,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    return response.json()


# ---------------------------------------------------------
# GET CONDITIONS FOR SELECTED DATE
# ---------------------------------------------------------

def get_date_data(weather, selected_date):

    hourly = weather.get("hourly", {})

    times = hourly.get("time", [])
    temperature = hourly.get("temperature_2m", [])
    humidity = hourly.get("relative_humidity_2m", [])
    rainfall = hourly.get("precipitation", [])
    pressure = hourly.get("surface_pressure", [])
    wind = hourly.get("wind_speed_10m", [])
    soil = hourly.get("soil_moisture_0_to_7cm", [])

    date_string = selected_date.isoformat()

    indices = [
        i for i, timestamp in enumerate(times)
        if timestamp.startswith(date_string)
    ]

    if not indices:
        return None

    def valid(values):
        return [
            values[i]
            for i in indices
            if values[i] is not None
        ]

    temp_values = valid(temperature)
    humidity_values = valid(humidity)
    rain_values = valid(rainfall)
    pressure_values = valid(pressure)
    wind_values = valid(wind)
    soil_values = valid(soil)

    return {
        "temperature": mean(temp_values) if temp_values else 0,
        "humidity": mean(humidity_values) if humidity_values else 0,
        "rainfall_24h": sum(rain_values) if rain_values else 0,
        "pressure": mean(pressure_values) if pressure_values else 0,
        "wind_speed": mean(wind_values) if wind_values else 0,
        "soil_moisture": mean(soil_values) if soil_values else 0
    }


# ---------------------------------------------------------
# GET MULTI-DAY RAINFALL
# ---------------------------------------------------------

def get_rainfall_total(weather, start_date, number_of_days):

    hourly = weather.get("hourly", {})

    times = hourly.get("time", [])
    rainfall = hourly.get("precipitation", [])

    total = 0.0

    for day_offset in range(number_of_days):

        current_date = start_date + timedelta(days=day_offset)
        current_string = current_date.isoformat()

        day_values = [
            rainfall[i]
            for i, timestamp in enumerate(times)
            if timestamp.startswith(current_string)
            and rainfall[i] is not None
        ]

        total += sum(day_values)

    return total


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.title("NEXUS-Manipur")

st.caption(
    "Environmental Hazard & Future Risk Prediction System"
)

st.info(
    "🌦️ Forecast conditions are automatically retrieved from "
    "Open-Meteo. You can edit the values before running a prediction."
)


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

st.sidebar.header("🔮 Prediction Control")

location = st.sidebar.selectbox(
    "Location",
    list(LOCATIONS.keys())
)

today = date.today()

selected_date = st.sidebar.date_input(
    "Prediction Date",
    value=today + timedelta(days=1),
    min_value=today,
    max_value=today + timedelta(days=9)
)

horizon = st.sidebar.selectbox(
    "Prediction Horizon",
    [
        "24 Hours",
        "48 Hours",
        "72 Hours"
    ]
)


# ---------------------------------------------------------
# LOCATION INFORMATION
# ---------------------------------------------------------

latitude = LOCATIONS[location]["lat"]
longitude = LOCATIONS[location]["lon"]


st.sidebar.markdown("---")

st.sidebar.caption(
    f"Coordinates\n"
    f"{latitude}, {longitude}"
)


# ---------------------------------------------------------
# LOAD FORECAST
# ---------------------------------------------------------

try:

    weather = get_weather(
        latitude,
        longitude
    )

    forecast = get_date_data(
        weather,
        selected_date
    )

except requests.RequestException as error:

    forecast = None

    st.error(
        f"Unable to connect to Open-Meteo: {error}"
    )

except Exception as error:

    forecast = None

    st.error(
        f"Something went wrong: {error}"
    )


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

forecast_key = (
    location,
    str(selected_date)
)

if forecast is not None:

    if st.session_state.get("forecast_key") != forecast_key:

        st.session_state.forecast_key = forecast_key

        st.session_state.rainfall_24h = forecast[
            "rainfall_24h"
        ]

        st.session_state.rainfall_48h = get_rainfall_total(
            weather,
            selected_date,
            2
        )

        st.session_state.rainfall_7d = get_rainfall_total(
            weather,
            selected_date,
            7
        )

        st.session_state.temperature = forecast[
            "temperature"
        ]

        st.session_state.humidity = forecast[
            "humidity"
        ]

        st.session_state.pressure = forecast[
            "pressure"
        ]

        st.session_state.wind_speed = forecast[
            "wind_speed"
        ]

        st.session_state.soil_moisture = forecast[
            "soil_moisture"
        ]


# ---------------------------------------------------------
# FORECAST SECTION
# ---------------------------------------------------------

st.header("🌦️ Forecast Environmental Conditions")

st.caption(
    f"{location} • "
    f"{selected_date.strftime('%d %B %Y')} • "
    f"{horizon}"
)


# ---------------------------------------------------------
# RAINFALL
# ---------------------------------------------------------

st.subheader("Rainfall & Soil")

r1, r2, r3, r4 = st.columns(4)

with r1:

    rainfall_24h = st.number_input(
        "Rainfall 24h (mm)",
        min_value=0.0,
        max_value=500.0,
        step=0.1,
        key="rainfall_24h"
    )

with r2:

    rainfall_48h = st.number_input(
        "Rainfall 48h (mm)",
        min_value=0.0,
        max_value=800.0,
        step=0.1,
        key="rainfall_48h"
    )

with r3:

    rainfall_7d = st.number_input(
        "Rainfall 7d (mm)",
        min_value=0.0,
        max_value=1500.0,
        step=0.1,
        key="rainfall_7d"
    )

with r4:

    soil_moisture = st.number_input(
        "Soil Moisture",
        min_value=0.0,
        max_value=1.0,
        step=0.001,
        key="soil_moisture"
    )


# ---------------------------------------------------------
# ATMOSPHERE
# ---------------------------------------------------------

st.subheader("Atmospheric Conditions")

a1, a2, a3, a4 = st.columns(4)

with a1:

    temperature = st.number_input(
        "Temperature (°C)",
        min_value=-20.0,
        max_value=60.0,
        step=0.1,
        key="temperature"
    )

with a2:

    humidity = st.number_input(
        "Humidity (%)",
        min_value=0.0,
        max_value=100.0,
        step=1.0,
        key="humidity"
    )

with a3:

    pressure = st.number_input(
        "Pressure (hPa)",
        min_value=800.0,
        max_value=1100.0,
        step=0.1,
        key="pressure"
    )

with a4:

    wind_speed = st.number_input(
        "Wind Speed (km/h)",
        min_value=0.0,
        max_value=250.0,
        step=0.1,
        key="wind_speed"
    )


st.caption(
    "✏️ Values are auto-filled from Open-Meteo and remain editable "
    "for scenario testing."
)


# ---------------------------------------------------------
# ACTION
# ---------------------------------------------------------

st.markdown("---")

run_prediction = st.button(
    "🚨 Run Future Prediction",
    type="primary",
    use_container_width=True
)


# ---------------------------------------------------------
# PREDICTION PROTOTYPE
# ---------------------------------------------------------

st.header("🔮 Prediction Result")

if run_prediction:

    # -----------------------------------------------------
    # TEMPORARY DEMONSTRATION SCORE
    #
    # This is NOT the Random Forest.
    # It exists only until the forecast-to-model
    # feature pipeline is connected.
    # -----------------------------------------------------

    rainfall_signal = (
        (rainfall_24h / 50) * 0.20
        + (rainfall_48h / 100) * 0.25
        + (rainfall_7d / 250) * 0.25
    )

    soil_signal = soil_moisture * 0.15

    humidity_signal = (humidity / 100) * 0.05

    pressure_signal = max(
        0,
        min(
            (1015 - pressure) / 20,
            1
        )
    ) * 0.10

    score = (
        rainfall_signal
        + soil_signal
        + humidity_signal
        + pressure_signal
    )

    probability = max(
        0,
        min(
            score,
            0.99
        )
    )

    probability_percent = probability * 100

    if probability_percent >= 70:

        risk = "HIGH"
        message = "Significant flood signal detected."

    elif probability_percent >= 40:

        risk = "MEDIUM"
        message = "Potential flood conditions detected."

    else:

        risk = "LOW"
        message = "No strong flood signal detected."

    result_left, result_right = st.columns(
        [2, 1]
    )

    with result_left:

        st.subheader("Prediction Summary")

        st.write(
            f"**Location:** {location}"
        )

        st.write(
            f"**Prediction Date:** "
            f"{selected_date.strftime('%d %B %Y')}"
        )

        st.write(
            f"**Prediction Horizon:** {horizon}"
        )

        st.progress(
            int(probability_percent)
        )

        st.metric(
            "Estimated Flood Probability",
            f"{probability_percent:.1f}%"
        )

        st.write(message)

    with result_right:

        if risk == "HIGH":

            st.error(
                f"⚠️ {risk} FLOOD RISK"
            )

        elif risk == "MEDIUM":

            st.warning(
                f"🟠 {risk} FLOOD RISK"
            )

        else:

            st.success(
                f"✅ {risk} FLOOD RISK"
            )


else:

    st.info(
        "Forecast conditions are ready. "
        "Adjust any values you want and press "
        "'Run Future Prediction'."
    )


# ---------------------------------------------------------
# DATA SOURCE
# ---------------------------------------------------------

st.markdown("---")

st.header("📡 Data Source")

source1, source2 = st.columns(2)

with source1:

    st.write("**Open-Meteo Forecast API**")

    st.write(
        "Automatic meteorological forecast input."
    )

    st.link_button(
        "Open Open-Meteo",
        "https://open-meteo.com/",
        use_container_width=True
    )

with source2:

    st.write("**Selected Location**")

    st.write(
        f"{location}"
    )

    st.write(
        f"Latitude: {latitude}"
    )

    st.write(
        f"Longitude: {longitude}"
    )


# ---------------------------------------------------------
# PHASE 1 PIPELINE
# ---------------------------------------------------------

st.markdown("---")

st.header("NEXUS Phase 1 Pipeline")

p1, p2, p3, p4, p5 = st.columns(5)

with p1:
    st.write("🌦️")
    st.write("Forecast")

with p2:
    st.write("⚙️")
    st.write("Features")

with p3:
    st.write("🤖")
    st.write("Random Forest")

with p4:
    st.write("📊")
    st.write("Probability")

with p5:
    st.write("🚨")
    st.write("Risk")


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.markdown("---")

st.caption(
    "NEXUS-Manipur | Phase 1 Future Prediction Prototype"
)