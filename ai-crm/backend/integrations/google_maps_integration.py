#!/usr/bin/env python3
"""
Google Maps Integration for CRM Location Tracking
"""

import os
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math
import sqlite3
from pathlib import Path

class GoogleMapsIntegration:
    """Google Maps integration for location services and visit tracking"""
    
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        self.base_url = 'https://maps.googleapis.com/maps/api'
        
        if not self.api_key:
            print("Warning: Google Maps API key not found. Some features may not work.")
    
    def geocode_address(self, address: str) -> Dict:
        """Convert address to latitude/longitude coordinates"""
        if not self.api_key:
            raise Exception("Google Maps API key not configured")
        
        url = f"{self.base_url}/geocode/json"
        params = {
            'address': address,
            'key': self.api_key
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                result = data['results'][0]
                location = result['geometry']['location']
                
                return {
                    'latitude': location['lat'],
                    'longitude': location['lng'],
                    'formatted_address': result['formatted_address'],
                    'place_id': result.get('place_id'),
                    'address_components': result.get('address_components', [])
                }
            else:
                raise Exception(f"Geocoding failed: {data['status']}")
        else:
            raise Exception(f"API request failed: {response.status_code}")
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Dict:
        """Convert coordinates to address"""
        if not self.api_key:
            raise Exception("Google Maps API key not configured")
        
        url = f"{self.base_url}/geocode/json"
        params = {
            'latlng': f"{latitude},{longitude}",
            'key': self.api_key
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                result = data['results'][0]
                
                return {
                    'formatted_address': result['formatted_address'],
                    'place_id': result.get('place_id'),
                    'address_components': result.get('address_components', [])
                }
            else:
                raise Exception(f"Reverse geocoding failed: {data['status']}")
        else:
            raise Exception(f"API request failed: {response.status_code}")
    
    def calculate_distance(self, origin: str, destination: str, mode: str = 'driving') -> Dict:
        """Calculate distance and travel time between two locations"""
        if not self.api_key:
            raise Exception("Google Maps API key not configured")
        
        url = f"{self.base_url}/distancematrix/json"
        params = {
            'origins': origin,
            'destinations': destination,
            'mode': mode,
            'units': 'imperial',
            'key': self.api_key
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            if data['status'] == 'OK':
                element = data['rows'][0]['elements'][0]
                
                if element['status'] == 'OK':
                    return {
                        'distance': {
                            'text': element['distance']['text'],
                            'value': element['distance']['value']  # in meters
                        },
                        'duration': {
                            'text': element['duration']['text'],
                            'value': element['duration']['value']  # in seconds
                        },
                        'mode': mode
                    }
                else:
                    raise Exception(f"Distance calculation failed: {element['status']}")
            else:
                raise Exception(f"Distance matrix failed: {data['status']}")
        else:
            raise Exception(f"API request failed: {response.status_code}")
    
    def get_directions(self, origin: str, destination: str, mode: str = 'driving') -> Dict:
        """Get turn-by-turn directions between two locations"""
        if not self.api_key:
            raise Exception("Google Maps API key not configured")
        
        url = f"{self.base_url}/directions/json"
        params = {
            'origin': origin,
            'destination': destination,
            'mode': mode,
            'key': self.api_key
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            if data['status'] == 'OK' and data['routes']:
                route = data['routes'][0]
                leg = route['legs'][0]
                
                return {
                    'distance': leg['distance'],
                    'duration': leg['duration'],
                    'start_address': leg['start_address'],
                    'end_address': leg['end_address'],
                    'steps': leg['steps'],
                    'overview_polyline': route['overview_polyline']['points']
                }
            else:
                raise Exception(f"Directions failed: {data['status']}")
        else:
            raise Exception(f"API request failed: {response.status_code}")
    
    def find_nearby_places(self, latitude: float, longitude: float, 
                          place_type: str = 'establishment', radius: int = 5000) -> List[Dict]:
        """Find nearby places of interest"""
        if not self.api_key:
            raise Exception("Google Maps API key not configured")
        
        url = f"{self.base_url}/place/nearbysearch/json"
        params = {
            'location': f"{latitude},{longitude}",
            'radius': radius,
            'type': place_type,
            'key': self.api_key
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            if data['status'] == 'OK':
                places = []
                for place in data.get('results', []):
                    places.append({
                        'name': place.get('name'),
                        'place_id': place.get('place_id'),
                        'rating': place.get('rating'),
                        'vicinity': place.get('vicinity'),
                        'types': place.get('types', []),
                        'geometry': place.get('geometry', {}),
                        'business_status': place.get('business_status')
                    })
                
                return places
            else:
                raise Exception(f"Places search failed: {data['status']}")
        else:
            raise Exception(f"API request failed: {response.status_code}")
    
    def get_place_details(self, place_id: str) -> Dict:
        """Get detailed information about a specific place"""
        if not self.api_key:
            raise Exception("Google Maps API key not configured")
        
        url = f"{self.base_url}/place/details/json"
        params = {
            'place_id': place_id,
            'fields': 'name,rating,formatted_phone_number,formatted_address,website,opening_hours,reviews',
            'key': self.api_key
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            if data['status'] == 'OK':
                return data['result']
            else:
                raise Exception(f"Place details failed: {data['status']}")
        else:
            raise Exception(f"API request failed: {response.status_code}")

class VisitTracker:
    """Track and manage distributor/dealer visits with database persistence"""
    
    def __init__(self, maps_integration: GoogleMapsIntegration):
        self.maps = maps_integration
        self.db_path = Path('database/visit_tracking.db')
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize the visit tracking database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS visits (
                    visit_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    account_name TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    scheduled_time TEXT NOT NULL,
                    address TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    place_id TEXT,
                    status TEXT NOT NULL DEFAULT 'planned',
                    actual_start_time TEXT,
                    completed_at TEXT,
                    duration_minutes INTEGER,
                    arrival_latitude REAL,
                    arrival_longitude REAL,
                    arrival_address TEXT,
                    distance_to_location_meters INTEGER,
                    travel_time_seconds INTEGER,
                    notes TEXT,
                    outcome TEXT,
                    next_steps TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS visit_activities (
                    activity_id TEXT PRIMARY KEY,
                    visit_id TEXT NOT NULL,
                    activity_type TEXT NOT NULL,
                    description TEXT,
                    timestamp TEXT NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    data TEXT,
                    FOREIGN KEY (visit_id) REFERENCES visits (visit_id)
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_visits_account_id ON visits (account_id)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_visits_status ON visits (status)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_visits_scheduled_time ON visits (scheduled_time)
            ''')
    
    def plan_visit(self, account_data: Dict, visit_purpose: str, 
                   scheduled_time: datetime) -> Dict:
        """Plan a visit to an account location"""
        try:
            # Geocode the account address
            address = account_data.get('address') or account_data.get('billing_address')
            if not address:
                raise Exception("No address found for account")
            
            location_info = self.maps.geocode_address(address)
            
            visit_id = f"VISIT_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            now = datetime.now().isoformat()
            
            visit_plan = {
                'visit_id': visit_id,
                'account_id': account_data.get('account_id'),
                'account_name': account_data.get('name'),
                'purpose': visit_purpose,
                'scheduled_time': scheduled_time.isoformat(),
                'location': {
                    'address': location_info['formatted_address'],
                    'latitude': location_info['latitude'],
                    'longitude': location_info['longitude'],
                    'place_id': location_info.get('place_id')
                },
                'status': 'planned',
                'created_at': now
            }
            
            # Save to database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO visits (
                        visit_id, account_id, account_name, purpose, scheduled_time,
                        address, latitude, longitude, place_id, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    visit_id,
                    account_data.get('account_id'),
                    account_data.get('name'),
                    visit_purpose,
                    scheduled_time.isoformat(),
                    location_info['formatted_address'],
                    location_info['latitude'],
                    location_info['longitude'],
                    location_info.get('place_id'),
                    'planned',
                    now,
                    now
                ))
            
            return visit_plan
            
        except Exception as e:
            raise Exception(f"Failed to plan visit: {str(e)}")
    
    def start_visit(self, visit_id: str, current_location: Tuple[float, float]) -> Dict:
        """Start a visit and log arrival"""
        visit = self.get_visit_by_id(visit_id)
        if not visit:
            raise Exception("Visit not found")
        
        try:
            # Calculate distance from current location to visit location
            current_address = self.maps.reverse_geocode(current_location[0], current_location[1])
            visit_address = visit['location']['address']
            
            distance_info = self.maps.calculate_distance(
                f"{current_location[0]},{current_location[1]}",
                visit_address
            )
            
            # Update visit status
            visit['status'] = 'in_progress'
            visit['actual_start_time'] = datetime.now().isoformat()
            visit['arrival_location'] = {
                'latitude': current_location[0],
                'longitude': current_location[1],
                'address': current_address['formatted_address']
            }
            visit['distance_to_location'] = distance_info
            
            return visit
            
        except Exception as e:
            raise Exception(f"Failed to start visit: {str(e)}")
    
    def complete_visit(self, visit_id: str, notes: str, outcome: str, 
                      next_steps: Optional[str] = None) -> Dict:
        """Complete a visit and log details"""
        visit = self.get_visit_by_id(visit_id)
        if not visit:
            raise Exception("Visit not found")
        
        # Update visit status
        visit['status'] = 'completed'
        visit['completed_at'] = datetime.now().isoformat()
        visit['notes'] = notes
        visit['outcome'] = outcome
        visit['next_steps'] = next_steps
        
        # Calculate visit duration
        if visit.get('actual_start_time'):
            start_time = datetime.fromisoformat(visit['actual_start_time'])
            end_time = datetime.now()
            duration = end_time - start_time
            visit['duration_minutes'] = int(duration.total_seconds() / 60)
        
        return visit
    
    def get_visit_by_id(self, visit_id: str) -> Optional[Dict]:
        """Get visit by ID from database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                'SELECT * FROM visits WHERE visit_id = ?', (visit_id,)
            )
            row = cursor.fetchone()
            
            if row:
                visit = dict(row)
                # Reconstruct location object
                visit['location'] = {
                    'address': visit['address'],
                    'latitude': visit['latitude'],
                    'longitude': visit['longitude'],
                    'place_id': visit['place_id']
                }
                return visit
            return None
    
    def get_visits_by_account(self, account_id: str) -> List[Dict]:
        """Get all visits for an account from database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                'SELECT * FROM visits WHERE account_id = ? ORDER BY scheduled_time DESC',
                (account_id,)
            )
            
            visits = []
            for row in cursor.fetchall():
                visit = dict(row)
                # Reconstruct location object
                visit['location'] = {
                    'address': visit['address'],
                    'latitude': visit['latitude'],
                    'longitude': visit['longitude'],
                    'place_id': visit['place_id']
                }
                visits.append(visit)
            
            return visits
    
    def get_upcoming_visits(self, days_ahead: int = 7) -> List[Dict]:
        """Get upcoming visits within specified days from database"""
        cutoff_date = (datetime.now() + timedelta(days=days_ahead)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM visits 
                WHERE status = 'planned' AND scheduled_time <= ?
                ORDER BY scheduled_time ASC
            ''', (cutoff_date,))
            
            visits = []
            for row in cursor.fetchall():
                visit = dict(row)
                # Reconstruct location object
                visit['location'] = {
                    'address': visit['address'],
                    'latitude': visit['latitude'],
                    'longitude': visit['longitude'],
                    'place_id': visit['place_id']
                }
                visits.append(visit)
            
            return visits
    
    def optimize_visit_route(self, visit_ids: List[str], start_location: str) -> Dict:
        """Optimize route for multiple visits"""
        if not visit_ids:
            return {'visits': [], 'total_distance': 0, 'total_duration': 0}
        
        visits = []
        for vid in visit_ids:
            visit = self.get_visit_by_id(vid)
            if visit:
                visits.append(visit)
        
        if not visits:
            return {'visits': [], 'total_distance': 0, 'total_duration': 0}
        
        try:
            # Simple optimization: calculate distances and sort by proximity
            # In a real implementation, you'd use a more sophisticated algorithm
            current_location = start_location
            optimized_visits = []
            remaining_visits = visits.copy()
            total_distance = 0
            total_duration = 0
            
            while remaining_visits:
                # Find closest visit
                closest_visit = None
                min_distance = float('inf')
                
                for visit in remaining_visits:
                    if visit and visit.get('location') and visit['location'].get('address'):
                        distance_info = self.maps.calculate_distance(
                            current_location,
                            visit['location']['address']
                        )
                        
                        if distance_info['distance']['value'] < min_distance:
                            min_distance = distance_info['distance']['value']
                            closest_visit = visit
                            closest_visit['travel_info'] = distance_info
                
                if closest_visit and closest_visit.get('location'):
                    optimized_visits.append(closest_visit)
                    remaining_visits.remove(closest_visit)
                    current_location = closest_visit['location']['address']
                    if 'travel_info' in closest_visit:
                        total_distance += closest_visit['travel_info']['distance']['value']
                        total_duration += closest_visit['travel_info']['duration']['value']
                else:
                    # No valid visits remaining
                    break
            
            return {
                'visits': optimized_visits,
                'total_distance': total_distance,
                'total_duration': total_duration,
                'total_distance_text': f"{total_distance / 1609.34:.1f} miles",
                'total_duration_text': f"{total_duration // 3600}h {(total_duration % 3600) // 60}m"
            }
            
        except Exception as e:
            raise Exception(f"Failed to optimize route: {str(e)}")

class LocationAnalytics:
    """Analytics for location-based CRM data"""
    
    def __init__(self, maps_integration: GoogleMapsIntegration):
        self.maps = maps_integration
    
    def analyze_territory_coverage(self, accounts: List[Dict], territory: str) -> Dict:
        """Analyze account coverage in a territory"""
        territory_accounts = [acc for acc in accounts if acc.get('territory') == territory]
        
        if not territory_accounts:
            return {'territory': territory, 'account_count': 0, 'coverage_analysis': {}}
        
        # Get coordinates for all accounts
        account_locations = []
        for account in territory_accounts:
            try:
                address = account.get('address') or account.get('billing_address')
                if address:
                    location = self.maps.geocode_address(address)
                    account_locations.append({
                        'account_id': account['account_id'],
                        'name': account['name'],
                        'latitude': location['latitude'],
                        'longitude': location['longitude'],
                        'revenue': account.get('annual_revenue', 0)
                    })
            except Exception:
                continue
        
        if not account_locations:
            return {'territory': territory, 'account_count': 0, 'coverage_analysis': {}}
        
        # Calculate territory center
        avg_lat = sum(loc['latitude'] for loc in account_locations) / len(account_locations)
        avg_lng = sum(loc['longitude'] for loc in account_locations) / len(account_locations)
        
        # Calculate coverage radius (distance from center to furthest account)
        max_distance = 0
        for location in account_locations:
            distance = self.calculate_haversine_distance(
                avg_lat, avg_lng, location['latitude'], location['longitude']
            )
            max_distance = max(max_distance, distance)
        
        # Revenue analysis
        total_revenue = sum(loc['revenue'] for loc in account_locations)
        avg_revenue = total_revenue / len(account_locations) if account_locations else 0
        
        return {
            'territory': territory,
            'account_count': len(account_locations),
            'center_coordinates': {'latitude': avg_lat, 'longitude': avg_lng},
            'coverage_radius_miles': max_distance,
            'total_revenue': total_revenue,
            'average_revenue': avg_revenue,
            'account_locations': account_locations
        }
    
    def calculate_haversine_distance(self, lat1: float, lon1: float, 
                                   lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 3959  # Earth's radius in miles
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def find_optimal_meeting_location(self, account_locations: List[Dict]) -> Dict:
        """Find optimal meeting location for multiple accounts"""
        if not account_locations:
            return {}
        
        # Calculate centroid
        avg_lat = sum(loc['latitude'] for loc in account_locations) / len(account_locations)
        avg_lng = sum(loc['longitude'] for loc in account_locations) / len(account_locations)
        
        try:
            # Find nearby meeting venues (restaurants, hotels, conference centers)
            venues = self.maps.find_nearby_places(
                avg_lat, avg_lng, 
                place_type='restaurant', 
                radius=10000
            )
            
            # Score venues based on proximity to all accounts
            scored_venues = []
            for venue in venues[:10]:  # Limit to top 10 venues
                venue_lat = venue['geometry']['location']['lat']
                venue_lng = venue['geometry']['location']['lng']
                
                total_distance = 0
                for account in account_locations:
                    distance = self.calculate_haversine_distance(
                        venue_lat, venue_lng,
                        account['latitude'], account['longitude']
                    )
                    total_distance += distance
                
                avg_distance = total_distance / len(account_locations)
                
                scored_venues.append({
                    'venue': venue,
                    'average_distance_miles': avg_distance,
                    'total_distance_miles': total_distance
                })
            
            # Sort by average distance
            scored_venues.sort(key=lambda x: x['average_distance_miles'])
            
            return {
                'centroid': {'latitude': avg_lat, 'longitude': avg_lng},
                'recommended_venues': scored_venues[:5],
                'account_count': len(account_locations)
            }
            
        except Exception as e:
            return {
                'centroid': {'latitude': avg_lat, 'longitude': avg_lng},
                'error': str(e),
                'account_count': len(account_locations)
            }

# Example usage and testing
def test_google_maps_integration():
    """Test Google Maps integration"""
    maps = GoogleMapsIntegration()
    
    # Test geocoding (will work without API key for demo)
    print("Testing Google Maps Integration...")
    
    # Mock test data
    test_address = "1600 Amphitheatre Parkway, Mountain View, CA"
    print(f"Test address: {test_address}")
    
    try:
        # This would require a valid API key
        # location = maps.geocode_address(test_address)
        # print(f"Geocoded location: {location}")
        print("Geocoding test skipped (requires API key)")
    except Exception as e:
        print(f"Geocoding failed (expected without API key): {e}")
    
    # Test visit tracker
    visit_tracker = VisitTracker(maps)
    
    # Mock account data
    account_data = {
        'account_id': 'ACC_001',
        'name': 'TechCorp Industries',
        'billing_address': '123 Tech Street, Palo Alto, CA 94301'
    }
    
    try:
        # This would also require API key
        # visit_plan = visit_tracker.plan_visit(
        #     account_data, 
        #     "Product demonstration", 
        #     datetime.now() + timedelta(days=1)
        # )
        # print(f"Visit planned: {visit_plan}")
        print("Visit planning test skipped (requires API key)")
    except Exception as e:
        print(f"Visit planning failed (expected without API key): {e}")
    
    # Test location analytics
    analytics = LocationAnalytics(maps)
    
    # Mock account locations
    mock_accounts = [
        {
            'account_id': 'ACC_001',
            'name': 'TechCorp',
            'territory': 'West Coast',
            'annual_revenue': 5000000,
            'billing_address': '123 Tech St, Palo Alto, CA'
        },
        {
            'account_id': 'ACC_002',
            'name': 'StartupCo',
            'territory': 'West Coast',
            'annual_revenue': 1000000,
            'billing_address': '456 Innovation Dr, San Francisco, CA'
        }
    ]
    
    try:
        # This would also require API key
        # coverage = analytics.analyze_territory_coverage(mock_accounts, 'West Coast')
        # print(f"Territory coverage: {coverage}")
        print("Territory analysis test skipped (requires API key)")
    except Exception as e:
        print(f"Territory analysis failed (expected without API key): {e}")
    
    print("Google Maps integration tests completed")

if __name__ == "__main__":
    test_google_maps_integration()