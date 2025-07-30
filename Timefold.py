import requests
from datetime import datetime
from typing import List
from dataclasses import dataclass
import math
import polyline  # Install with: pip install polyline

# Configuration - replace with your actual API keys
OPENWEATHER_API_KEY = "88994e4cc121a227794f40fb58ef5011"
OPENROUTESERVICE_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImQyN2E5NjAyMDRhMzQxMTRhOGQ3OGUyZjJmMGEwMjkwIiwiaCI6Im11cm11cjY0In0="

@dataclass
class RouteSegment:
    index: int
    base_time: float  # minutes
    weather_impact: float
    time_adjustment: float = 0.0

    @property
    def adjusted_time(self):
        return self.base_time * self.weather_impact + self.time_adjustment

class TravelTimeCalculator:
    def __init__(self):
        self.base_weather_url = "https://api.openweathermap.org/data/2.5/weather"
        self.base_route_url = "https://api.openrouteservice.org/v2/directions/driving-car"
        self.geocode_url = "https://api.openrouteservice.org/geocode/search"
        self.cache = {}

    def geocode_location(self, location_name: str) -> List[float]:
        """Convert location name to [longitude, latitude] coordinates"""
        if location_name in self.cache.get('geocode', {}):
            return self.cache['geocode'][location_name]
        
        headers = {'Authorization': OPENROUTESERVICE_API_KEY}
        try:
            response = requests.get(
                f"{self.geocode_url}?text={location_name}&size=1",
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            if data['features']:
                coords = data['features'][0]['geometry']['coordinates']
                self.cache.setdefault('geocode', {})[location_name] = coords
                return coords
            raise ValueError(f"Location not found: {location_name}")
        except Exception as e:
            print(f"Geocoding error for {location_name}: {e}")
            return None

    def get_route_data(self, source: str, destination: str) -> dict:
        """Get route geometry and base travel time"""
        cache_key = f"{source}_{destination}"
        if cache_key in self.cache.get('routes', {}):
            return self.cache['routes'][cache_key]
        
        source_coords = self.geocode_location(source)
        dest_coords = self.geocode_location(destination)
        if not source_coords or not dest_coords:
            return None

        headers = {'Authorization': OPENROUTESERVICE_API_KEY}
        try:
            response = requests.post(
                self.base_route_url,
                headers=headers,
                json={"coordinates": [source_coords, dest_coords]}
            )
            response.raise_for_status()
            data = response.json()
            
            # Decode polyline for precise route
            route_points = polyline.decode(data['routes'][0]['geometry'])
            
            route_data = {
                'coordinates': route_points,
                'base_time': data['routes'][0]['summary']['duration'] / 60,
                'distance': data['routes'][0]['summary']['distance'] / 1000
            }
            self.cache.setdefault('routes', {})[cache_key] = route_data
            return route_data
        except Exception as e:
            print(f"Route error: {e}")
            return None

    def get_weather_conditions(self, lat: float, lon: float) -> dict:
        """Get current weather at specified coordinates"""
        cache_key = f"{lat}_{lon}"
        if cache_key in self.cache.get('weather', {}):
            return self.cache['weather'][cache_key]
        
        try:
            response = requests.get(
                f"{self.base_weather_url}?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
            )
            response.raise_for_status()
            data = response.json()
            weather = {
                'conditions': data['weather'][0]['main'],
                'temp': data['main']['temp'],
                'wind': data['wind']['speed'],
                'visibility': data.get('visibility', 10000)
            }
            self.cache.setdefault('weather', {})[cache_key] = weather
            return weather
        except Exception as e:
            print(f"Weather error at ({lat}, {lon}): {e}")
            return None

    def sample_route_weather(self, coordinates: List[List[float]], samples: int = 10) -> List[dict]:
        """Collect weather data at multiple points along the route with minimum spacing"""
        if len(coordinates) < samples:
            step = 1
        else:
            step = len(coordinates) // samples
        
        weather_data = []
        last_lat, last_lon = None, None
        min_spacing_km = 1.0  # Minimum 1km between samples
        
        for i in range(0, len(coordinates), step):
            lat, lon = coordinates[i]
            
            # Ensure minimum spacing between samples
            if last_lat and self._haversine(last_lon, last_lat, lon, lat) < min_spacing_km:
                continue
                
            weather = self.get_weather_conditions(lat, lon)
            if weather:
                weather_data.append(weather)
                last_lat, last_lon = lat, lon
                if len(weather_data) >= samples:
                    break
        
        return weather_data

    def _haversine(self, lon1: float, lat1: float, lon2: float, lat2: float) -> float:
        """Calculate distance between two GPS points in km"""
        R = 6371  # Earth radius in km
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = (math.sin(dLat/2) * math.sin(dLat/2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dLon/2) * math.sin(dLon/2))
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    def get_weather_impact(self, condition: str) -> float:
        """Impact multipliers for different weather conditions"""
        impacts = {
            'Clear': 1.0,
            'Clouds': 1.05,
            'Rain': 1.25,
            'Drizzle': 1.15,
            'Thunderstorm': 1.4,
            'Snow': 1.6,
            'Fog': 1.5,
            'Mist': 1.3,
            'Haze': 1.2
        }
        return impacts.get(condition, 1.1)

    def get_traffic_factor(self, hour: int, weekday: int, distance: float) -> float:
        """Hyderabad-specific traffic model considering distance"""
        # Base traffic factor
        if weekday >= 5:  # Weekend
            base_factor = 1.2 if 12 <= hour < 18 else 1.0
        else:  # Weekday
            if 7 <= hour < 10: base_factor = 1.6    # Morning rush
            elif 16 <= hour < 19: base_factor = 1.7  # Evening rush
            elif 10 <= hour < 16: base_factor = 1.3  # Midday
            else: base_factor = 0.9                  # Night
        
        # Distance adjustment
        if distance > 10:  # Longer distances more affected by traffic
            return base_factor * 1.2
        elif distance > 5:
            return base_factor * 1.1
        return base_factor

    def optimize_route(self, base_time: float, weather_samples: List[dict], traffic_factor: float) -> float:
        """Local optimization algorithm"""
        num_segments = len(weather_samples)
        segments = [
            RouteSegment(
                index=i,
                base_time=base_time/num_segments,
                weather_impact=self.get_weather_impact(w['conditions'])
            )
            for i, w in enumerate(weather_samples)
        ]
        
        # Optimization iterations
        for _ in range(100):
            avg_time = sum(s.adjusted_time for s in segments) / num_segments
            for seg in segments:
                # Apply three constraints:
                # 1. Minimize time
                # 2. Penalize large adjustments
                # 3. Balance segments
                adjustment = (-0.1 * seg.adjusted_time +          # Minimize time
                             -0.2 * seg.time_adjustment +        # Penalize adjustments
                             0.15 * (avg_time - seg.adjusted_time))  # Balance
                seg.time_adjustment += adjustment
        
        return sum(s.adjusted_time for s in segments) * traffic_factor

    def calculate_travel_time(self, source: str, destination: str) -> float:
        """Main function to calculate optimized travel time"""
        print(f"\nCalculating travel time from {source} to {destination}...")
        
        # 1. Get route data
        route_data = self.get_route_data(source, destination)
        if not route_data:
            print("Error: Could not get route data")
            return None
        
        print(f"\nRoute Distance: {route_data['distance']:.2f} km")
        print(f"Base Travel Time: {route_data['base_time']:.2f} minutes")
        
        # 2. Get weather samples
        weather_samples = self.sample_route_weather(route_data['coordinates'])
        if not weather_samples:
            print("Warning: Using default weather (Clear)")
            weather_samples = [{'conditions': 'Clear', 'temp': 30, 'wind': 0}]
        
        print("\nWeather Conditions Along Route:")
        for i, w in enumerate(weather_samples[:5]):  # Show first 5 samples
            print(f"Point {i+1}: {w['conditions']} (Temp: {w['temp']}°C, Wind: {w['wind']} m/s)")
        
        # 3. Get traffic factor
        now = datetime.now()
        traffic_factor = self.get_traffic_factor(now.hour, now.weekday(), route_data['distance'])
        print(f"\nTraffic Conditions: {'Weekday' if now.weekday() < 5 else 'Weekend'}")
        print(f"Current Hour: {now.hour}:00, Traffic Factor: {traffic_factor:.2f}x")
        
        # 4. Optimize
        optimized_time = self.optimize_route(
            route_data['base_time'],
            weather_samples,
            traffic_factor
        )
        
        # 5. Display results
        print("\n=== OPTIMIZED TRAVEL TIME ===")
        print(f"Base Time: {route_data['base_time']:.2f} minutes")
        print(f"Weather Impact: {sum(self.get_weather_impact(w['conditions']) for w in weather_samples)/len(weather_samples):.2f}x")
        print(f"Traffic Impact: {traffic_factor:.2f}x")
        print(f"\nFinal Estimated Time: {optimized_time:.2f} minutes ({optimized_time/60:.1f} hours)")
        
        return optimized_time

if __name__ == "__main__":
    calculator = TravelTimeCalculator()
    
    # Example: KPHB to Ameerpet in Hyderabad
    calculator.calculate_travel_time("KPHB, Hyderabad", "Ameerpet, Hyderabad")
