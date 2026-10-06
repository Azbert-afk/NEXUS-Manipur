import streamlit as st
import requests
import folium

from datetime import date, timedelta
from statistics import mean
from streamlit_folium import st_folium


st.set_page_config(
    page_title="NEXUS-Manipur",
    page_icon="🌧️",
    layout="wide"
)


# ---------------------------------------------------------
# Preset places
# These are only quick-jump options.
# The map itself is the main location selector.
# ---------------------------------------------------------

PLACES = {
    "Imphal East": (24.8166, 93.9421),
    "Imphal West": (24.7905, 93.8679),
    "Thoubal": (24.6388, 94.0100),
    "Bishnupur": (24.6285, 93.7690),
    "Senapati": (25.2670, 94.0270),
    "Kakching": (24.4980, 94.0080),
    "Churachandpur": (24.3333, 93.6833)
}


# ---------------------------------------------------------
# Six seasons
# ---------------------------------------------------------

def get_season(month):

    if month in [1, 2]:
        return "Shishira", "❄️", "Cool season"

    if month in [3, 4]:
        return "Vasanta", "🌸", "Spring season"

    if month in [5, 6]:
        return "Grishma", "☀️", "Summer season"

    if month in [7, 8]:
        return "Varsha", "🌧️", "Rainy season"

    if month in [9, 10]:
        return "Sharad", "🍂", "Autumn season"

    return "Hemanta", "🌾", "Pre-winter season"


# ---------------------------------------------------------
# Open-Meteo
# ---------------------------------------------------------

@st.cache_data(ttl=900)
def get_weather(latitude, longitude):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "hourly": (
            "temperature_2m,"
            "apparent_temperature,"
            "relative_humidity_2m,"
            "precipitation,"
            "precipitation_probability,"
            "weather_code,"
            "cloud_cover,"
            "visibility,"
            "sunshine_duration,"
            "dew_point_2m,"
            "pressure_msl,"
            "wind_speed_10m,"
            "wind_direction_10m,"
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
# Selected date weather
# ---------------------------------------------------------

def get_day_data(weather, selected_date):

    hourly = weather.get("hourly", {})

    times = hourly.get("time", [])
    temperature = hourly.get("temperature_2m", [])
    feels_like = hourly.get("apparent_temperature", [])
    humidity = hourly.get("relative_humidity_2m", [])
    rainfall = hourly.get("precipitation", [])
    rain_probability = hourly.get("precipitation_probability", [])
    weather_code = hourly.get("weather_code", [])
    cloud_cover = hourly.get("cloud_cover", [])
    visibility = hourly.get("visibility", [])
    sunshine = hourly.get("sunshine_duration", [])
    dew_point = hourly.get("dew_point_2m", [])
    pressure = hourly.get("pressure_msl", [])
    wind = hourly.get("wind_speed_10m", [])
    wind_direction = hourly.get("wind_direction_10m", [])
    soil = hourly.get("soil_moisture_0_to_7cm", [])

    wanted = selected_date.isoformat()

    indexes = [
        i for i, timestamp in enumerate(times)
        if timestamp.startswith(wanted)
    ]

    if not indexes:
        return None

    def pick(values):

        return [
            values[i]
            for i in indexes
            if values[i] is not None
        ]

    temp = pick(temperature)
    feels = pick(feels_like)
    hum = pick(humidity)
    rain = pick(rainfall)
    rain_prob = pick(rain_probability)
    codes = pick(weather_code)
    clouds = pick(cloud_cover)
    visibility_values = pick(visibility)
    sunshine_values = pick(sunshine)
    dew = pick(dew_point)
    press = pick(pressure)
    wind_values = pick(wind)
    wind_dirs = pick(wind_direction)
    soil_values = pick(soil)

    return {
        "temperature": mean(temp) if temp else 0,
        "feels_like": mean(feels) if feels else 0,
        "humidity": mean(hum) if hum else 0,
        "rainfall": sum(rain) if rain else 0,
        "rain_probability": max(rain_prob) if rain_prob else 0,
        "weather_codes": codes,
        "cloud_cover": mean(clouds) if clouds else 0,
        "visibility": (
            mean(visibility_values)
            if visibility_values else 0
        ),
        "sunshine": (
            sum(sunshine_values)
            if sunshine_values else 0
        ),
        "dew_point": mean(dew) if dew else 0,
        "pressure": mean(press) if press else 0,
        "wind_speed": mean(wind_values) if wind_values else 0,
        "wind_direction": (
            mean(wind_dirs)
            if wind_dirs else 0
        ),
        "soil_moisture": (
            mean(soil_values)
            if soil_values else 0
        )
    }


# ---------------------------------------------------------
# Rainfall totals
# ---------------------------------------------------------

def rainfall_total(weather, start_date, days):

    hourly = weather.get("hourly", {})

    times = hourly.get("time", [])
    rainfall = hourly.get("precipitation", [])

    total = 0.0

    for offset in range(days):

        current_date = (
            start_date + timedelta(days=offset)
        ).isoformat()

        values = [
            rainfall[i]
            for i, timestamp in enumerate(times)
            if timestamp.startswith(current_date)
            and rainfall[i] is not None
        ]

        total += sum(values)

    return total


# ---------------------------------------------------------
# Weather descriptions
# ---------------------------------------------------------

def weather_description(codes):

    if not codes:
        return "Unknown"

    code = max(
        set(codes),
        key=codes.count
    )

    names = {
        0: "Clear sky",
        1: "Mostly clear",
        2: "Partly cloudy",
        3: "Cloudy",
        45: "Fog",
        48: "Fog",
        51: "Light drizzle",
        53: "Drizzle",
        55: "Heavy drizzle",
        61: "Light rain",
        63: "Rain",
        65: "Heavy rain",
        71: "Light snow",
        73: "Snow",
        75: "Heavy snow",
        80: "Rain showers",
        81: "Rain showers",
        82: "Heavy rain showers",
        95: "Thunderstorm",
        96: "Thunderstorm with hail",
        99: "Thunderstorm with hail"
    }

    return names.get(
        int(code),
        "Variable conditions"
    )


def rain_status(data):

    chance = data["rain_probability"]
    amount = data["rainfall"]

    if chance >= 70 or amount >= 5:
        return "🌧️ Rain expected"

    if chance >= 40 or amount > 0.2:
        return "🌦️ Rain possible"

    return "☀️ Low chance of rain"


def sky_status(clouds):

    if clouds >= 80:
        return "☁️ Mostly cloudy"

    if clouds >= 50:
        return "⛅ Partly cloudy"

    if clouds >= 20:
        return "🌤️ Mostly clear"

    return "☀️ Clear"


def humidity_status(value):

    if value >= 80:
        return "💧 High"

    if value >= 50:
        return "💧 Moderate"

    return "💧 Low"


def fog_status(data):

    codes = data["weather_codes"]
    visibility = data["visibility"]

    if any(
        int(code) in [45, 48]
        for code in codes
    ):
        return "🌫️ Fog likely"

    if visibility < 2000:
        return "🌫️ Reduced visibility"

    return "👁️ Unlikely"


def sunshine_status(seconds):

    hours = seconds / 3600

    if hours >= 6:
        return "☀️ Good"

    if hours >= 3:
        return "🌤️ Moderate"

    return "☁️ Low"


def storm_status(codes):

    storm_codes = [95, 96, 99]

    if any(
        int(code) in storm_codes
        for code in codes
    ):
        return "⛈️ Possible"

    return "✅ Unlikely"


def wind_direction(degrees):

    directions = [
        "N", "NE", "E", "SE",
        "S", "SW", "W", "NW"
    ]

    return directions[
        round(degrees / 45) % 8
    ]


# ---------------------------------------------------------
# Map
# ---------------------------------------------------------

def make_map(latitude, longitude):

    m = folium.Map(
        location=[latitude, longitude],
        zoom_start=10,
        control_scale=True
    )

    folium.TileLayer(
        "OpenStreetMap",
        name="Standard Map",
        control=True
    ).add_to(m)

    # Satellite imagery layer
    folium.TileLayer(
        tiles=(
            "https://server.arcgisonline.com/"
            "ArcGIS/rest/services/"
            "World_Imagery/MapServer/tile/"
            "{z}/{y}/{x}"
        ),
        attr=(
            "Tiles © Esri"
        ),
        name="Satellite",
        overlay=False,
        control=True
    ).add_to(m)

    folium.Marker(
        [latitude, longitude],
        tooltip="Selected NEXUS Location",
        popup=(
            f"Latitude: {latitude:.6f}<br>"
            f"Longitude: {longitude:.6f}"
        )
    ).add_to(m)

    folium.LayerControl().add_to(m)

    return m


# ---------------------------------------------------------
# Start point
# ---------------------------------------------------------

if "selected_lat" not in st.session_state:
    st.session_state.selected_lat = PLACES["Imphal East"][0]

if "selected_lon" not in st.session_state:
    st.session_state.selected_lon = PLACES["Imphal East"][1]

if "location_name" not in st.session_state:
    st.session_state.location_name = "Imphal East"

if "last_map_click" not in st.session_state:
    st.session_state.last_map_click = None


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.title("NEXUS-Manipur")

st.caption(
    "Environmental Hazard & Future Risk Prediction System"
)

st.info(
    "🗺️ Click anywhere on the map to choose a location. "
    "NEXUS will use the selected latitude and longitude "
    "for its weather forecast."
)


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

st.sidebar.header("🔮 Prediction Control")

selected_date = st.sidebar.date_input(
    "Prediction Date",
    value=date.today() + timedelta(days=1),
    min_value=date.today(),
    max_value=date.today() + timedelta(days=9)
)

horizon = st.sidebar.selectbox(
    "Prediction Horizon",
    [
        "24 Hours",
        "48 Hours",
        "72 Hours"
    ]
)


st.sidebar.markdown("---")

st.sidebar.write("Quick Location")

quick_place = st.sidebar.selectbox(
    "Jump to",
    ["Map selection"] + list(PLACES.keys())
)

if quick_place != "Map selection":

    quick_lat, quick_lon = PLACES[quick_place]

    st.session_state.selected_lat = quick_lat
    st.session_state.selected_lon = quick_lon
    st.session_state.location_name = quick_place


# ---------------------------------------------------------
# Current coordinates
# ---------------------------------------------------------

lat = st.session_state.selected_lat
lon = st.session_state.selected_lon


# ---------------------------------------------------------
# Map
# ---------------------------------------------------------

st.header("🗺️ Select Location")

st.caption(
    "Click any point on the map. "
    "The marker will move to the selected coordinates."
)

map_object = make_map(
    lat,
    lon
)

map_result = st_folium(
    map_object,
    width=None,
    height=500,
    returned_objects=["last_clicked"],
    key="nexus_location_map"
)


# ---------------------------------------------------------
# Handle map click
# ---------------------------------------------------------

clicked = map_result.get("last_clicked")

if clicked:

    new_lat = round(
        float(clicked["lat"]),
        6
    )

    new_lon = round(
        float(clicked["lng"]),
        6
    )

    new_click = (
        new_lat,
        new_lon
    )

    if new_click != st.session_state.last_map_click:

        st.session_state.last_map_click = new_click
        st.session_state.selected_lat = new_lat
        st.session_state.selected_lon = new_lon
        st.session_state.location_name = "Custom Map Point"

        st.rerun()


# ---------------------------------------------------------
# Selected location
# ---------------------------------------------------------

st.subheader("📍 Selected Location")

location_col1, location_col2, location_col3 = st.columns(3)

with location_col1:

    st.metric(
        "Latitude",
        f"{lat:.6f}"
    )

with location_col2:

    st.metric(
        "Longitude",
        f"{lon:.6f}"
    )

with location_col3:

    season, season_icon, season_text = get_season(
        selected_date.month
    )

    st.metric(
        "Season",
        f"{season_icon} {season}"
    )


st.caption(
    f"Location mode: {st.session_state.location_name}"
)


# ---------------------------------------------------------
# Get weather for selected coordinates
# ---------------------------------------------------------

try:

    weather = get_weather(
        lat,
        lon
    )

    forecast = get_day_data(
        weather,
        selected_date
    )

except requests.RequestException as error:

    weather = None
    forecast = None

    st.error(
        f"Could not reach Open-Meteo: {error}"
    )

except Exception as error:

    weather = None
    forecast = None

    st.error(
        f"Something went wrong: {error}"
    )


# ---------------------------------------------------------
# Forecast
# ---------------------------------------------------------

if forecast:

    rain24 = rainfall_total(
        weather,
        selected_date,
        1
    )

    rain48 = rainfall_total(
        weather,
        selected_date,
        2
    )

    rain7 = rainfall_total(
        weather,
        selected_date,
        7
    )


    # -----------------------------------------------------
    # Load values into editable controls
    # -----------------------------------------------------

    forecast_key = (
        round(lat, 6),
        round(lon, 6),
        str(selected_date)
    )

    if st.session_state.get(
        "forecast_key"
    ) != forecast_key:

        st.session_state.forecast_key = forecast_key

        st.session_state.rainfall_24h = float(rain24)
        st.session_state.rainfall_48h = float(rain48)
        st.session_state.rainfall_7d = float(rain7)

        st.session_state.temperature = float(
            forecast["temperature"]
        )

        st.session_state.humidity = float(
            forecast["humidity"]
        )

        st.session_state.pressure = float(
            forecast["pressure"]
        )

        st.session_state.wind_speed = float(
            forecast["wind_speed"]
        )

        st.session_state.soil_moisture = float(
            forecast["soil_moisture"]
        )


    # -----------------------------------------------------
    # Weather feed
    # -----------------------------------------------------

    st.markdown("---")

    st.header("🌦️ Weather Feed")

    st.caption(
        "Forecast interpretation for the selected point."
    )

    feed1, feed2, feed3, feed4 = st.columns(4)

    with feed1:

        st.info(
            f"**Rain**\n\n"
            f"{rain_status(forecast)}"
        )

    with feed2:

        st.info(
            f"**Sky**\n\n"
            f"{sky_status(forecast['cloud_cover'])}"
        )

    with feed3:

        st.info(
            f"**Humidity**\n\n"
            f"{humidity_status(forecast['humidity'])}"
        )

    with feed4:

        st.info(
            f"**Fog**\n\n"
            f"{fog_status(forecast)}"
        )


    feed5, feed6, feed7, feed8 = st.columns(4)

    with feed5:

        st.info(
            f"**Sunshine**\n\n"
            f"{sunshine_status(forecast['sunshine'])}"
        )

    with feed6:

        st.info(
            f"**Storm**\n\n"
            f"{storm_status(forecast['weather_codes'])}"
        )

    with feed7:

        st.info(
            f"**Condition**\n\n"
            f"{weather_description(forecast['weather_codes'])}"
        )

    with feed8:

        st.info(
            f"**Rain Chance**\n\n"
            f"{forecast['rain_probability']:.0f}%"
        )


    # -----------------------------------------------------
    # Editable forecast data
    # -----------------------------------------------------

    st.markdown("---")

    st.header("🌧️ Forecast Conditions")

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
        "✏️ Forecast values are automatic but remain editable "
        "for scenario testing."
    )


    # -----------------------------------------------------
    # Extra conditions
    # -----------------------------------------------------

    st.markdown("---")

    st.header("More Weather Details")

    d1, d2, d3, d4 = st.columns(4)

    with d1:

        st.metric(
            "Feels Like",
            f"{forecast['feels_like']:.1f} °C"
        )

    with d2:

        st.metric(
            "Cloud Cover",
            f"{forecast['cloud_cover']:.0f}%"
        )

    with d3:

        st.metric(
            "Visibility",
            f"{forecast['visibility'] / 1000:.1f} km"
        )

    with d4:

        st.metric(
            "Dew Point",
            f"{forecast['dew_point']:.1f} °C"
        )


    d5, d6, d7, d8 = st.columns(4)

    with d5:

        st.metric(
            "Wind Direction",
            wind_direction(
                forecast["wind_direction"]
            )
        )

    with d6:

        st.metric(
            "Pressure",
            f"{forecast['pressure']:.1f} hPa"
        )

    with d7:

        st.metric(
            "Rainfall",
            f"{rain24:.1f} mm"
        )

    with d8:

        st.metric(
            "Soil Moisture",
            f"{forecast['soil_moisture']:.3f}"
        )


    # -----------------------------------------------------
    # Prediction
    # -----------------------------------------------------

    st.markdown("---")

    run_prediction = st.button(
        "🚨 Run Future Prediction",
        type="primary",
        use_container_width=True
    )

    st.header("🔮 Prediction Result")

    if run_prediction:

        # Temporary interface score.
        # The trained Random Forest comes here later.

        rainfall_signal = (
            (rainfall_24h / 50) * 0.20
            + (rainfall_48h / 100) * 0.25
            + (rainfall_7d / 250) * 0.25
        )

        soil_signal = soil_moisture * 0.15

        humidity_signal = (
            humidity / 100
        ) * 0.05

        pressure_signal = (
            max(
                0,
                min(
                    (1015 - pressure) / 20,
                    1
                )
            )
            * 0.10
        )

        score = (
            rainfall_signal
            + soil_signal
            + humidity_signal
            + pressure_signal
        )

        probability = max(
            0,
            min(score, 0.99)
        )

        percentage = probability * 100


        if percentage >= 70:

            risk = "HIGH"

        elif percentage >= 40:

            risk = "MEDIUM"

        else:

            risk = "LOW"


        p1, p2 = st.columns([2, 1])

        with p1:

            st.write(
                f"**Latitude:** {lat:.6f}"
            )

            st.write(
                f"**Longitude:** {lon:.6f}"
            )

            st.write(
                f"**Date:** "
                f"{selected_date.strftime('%d %B %Y')}"
            )

            st.write(
                f"**Horizon:** {horizon}"
            )

            st.progress(
                min(int(percentage), 100)
            )

            st.metric(
                "Estimated Flood Probability",
                f"{percentage:.1f}%"
            )

        with p2:

            if risk == "HIGH":

                st.error(
                    "⚠️ HIGH FLOOD RISK"
                )

            elif risk == "MEDIUM":

                st.warning(
                    "🟠 MEDIUM FLOOD RISK"
                )

            else:

                st.success(
                    "✅ LOW FLOOD RISK"
                )


    else:

        st.info(
            "Forecast data is ready. "
            "Adjust the conditions if needed, "
            "then run the prediction."
        )


    # -----------------------------------------------------
    # Data source
    # -----------------------------------------------------

    st.markdown("---")

    st.header("📡 Data Source")

    st.write(
        "Open-Meteo Forecast API"
    )

    st.write(
        f"Latitude: {lat:.6f}"
    )

    st.write(
        f"Longitude: {lon:.6f}"
    )

    st.link_button(
        "Open Open-Meteo",
        "https://open-meteo.com/",
        use_container_width=True
    )


else:

    st.warning(
        "No forecast data was returned for this date."
    )


# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------

st.markdown("---")

st.caption(
    "NEXUS-Manipur | Phase 1 Future Prediction Prototype"
)