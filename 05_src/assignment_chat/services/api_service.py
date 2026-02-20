import json
from typing import Dict, Any, Optional
from urllib.request import urlopen
from urllib.parse import urlencode


def _http_get_json(url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if params:
        url = f"{url}?{urlencode(params)}"
    with urlopen(url) as r:
        data = r.read().decode("utf-8")
    return json.loads(data)


def _c_to_f(c: float) -> float:
    return (c * 9.0 / 5.0) + 32.0


def get_current_weather(city: str) -> Dict[str, Any]:
    """
    Uses Open-Meteo:
    1) Geocoding API to turn a city name into lat/lon
    2) Forecast API to get current weather
    Returns a transformed natural-language summary + structured fields.
    """
    geo = _http_get_json(
        "https://geocoding-api.open-meteo.com/v1/search",
        {"name": city, "count": 1, "language": "en", "format": "json"},
    )

    results = geo.get("results") or []
    if not results:
        return {
            "ok": False,
            "city": city,
            "message": f"I couldn't find a location for '{city}'. Try a more specific name (e.g., 'Toronto, Canada').",
        }

    loc = results[0]
    name = loc.get("name", city)
    country = loc.get("country", "")
    lat = loc.get("latitude")
    lon = loc.get("longitude")

    wx = _http_get_json(
        "https://api.open-meteo.com/v1/forecast",
        {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,apparent_temperature,wind_speed_10m",
            "temperature_unit": "celsius",
            "wind_speed_unit": "kmh",
        },
    )

    current = wx.get("current") or {}
    temp_c = current.get("temperature_2m")
    feels_c = current.get("apparent_temperature")
    wind_kmh = current.get("wind_speed_10m")

    if temp_c is None:
        return {
            "ok": False,
            "city": city,
            "message": f"I found '{name}', but couldn't fetch current weather right now.",
        }

    summary = (
        f"Right now in {name}{', ' + country if country else ''}: "
        f"{temp_c:.1f}°C ({_c_to_f(temp_c):.1f}°F). "
        f"Feels like {feels_c:.1f}°C ({_c_to_f(feels_c):.1f}°F). "
        f"Wind is about {wind_kmh:.0f} km/h."
    )

    return {
        "ok": True,
        "city": name,
        "country": country,
        "latitude": lat,
        "longitude": lon,
        "temperature_c": float(temp_c),
        "feels_like_c": float(feels_c) if feels_c is not None else None,
        "wind_kmh": float(wind_kmh) if wind_kmh is not None else None,
        "summary": summary,
    }