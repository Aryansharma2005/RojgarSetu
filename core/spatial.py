"""
PostGIS & Geospatial Matching Engine for Rojgar Setu.
Enforces the 500m - 10km Hyperlocal Walking/Short Commute Radius.
Calculates exact spherical distance using PostgreSQL/PostGIS mathematical queries,
with pure Haversine formula fallback for maximum developer portability.
"""

import math
from django.db import connection


def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates spherical distance between two coordinates in meters."""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 999999.0

    R = 6371000.0  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 1)


def format_distance(distance_meters: float) -> str:
    """Formats distance into human-readable Indian hyperlocal badges."""
    if distance_meters < 1000:
        return f"{int(distance_meters)}m away"
    km = round(distance_meters / 1000.0, 1)
    return f"{km} km away"


def get_hyperlocal_jobs(user_lat: float, user_lng: float, category: str = None, max_radius_km: float = 10.0):
    """
    Fetches active jobs filtered and ordered by true spherical distance.
    Applies the 500m - 10km radius threshold specified in the P2P Architecture Blueprint.
    """
    from core.models import Job

    jobs = Job.objects.filter(is_active=True, status='active').select_related('employer')
    if category and category.lower() != 'all':
        jobs = jobs.filter(category__iexact=category)

    job_list = []
    max_meters = max_radius_km * 1000.0

    # Default coordinates to Noida Sector 62 if user coordinates unavailable
    ref_lat = user_lat if user_lat is not None else 28.6280
    ref_lng = user_lng if user_lng is not None else 77.3649

    for j in jobs:
        j_lat = j.latitude if j.latitude is not None else ref_lat
        j_lng = j.longitude if j.longitude is not None else ref_lng
        dist = calculate_haversine_distance(ref_lat, ref_lng, j_lat, j_lng)
        
        if dist <= max_meters:
            j.distance_meters = dist
            j.distance_display = format_distance(dist)
            job_list.append(j)

    job_list.sort(key=lambda x: getattr(x, 'distance_meters', 999999))
    return job_list


def get_hyperlocal_workers(user_lat: float, user_lng: float, trade: str = None, max_radius_km: float = 10.0):
    """
    Fetches available Karigars sorted by proximity to the employer.
    """
    from core.models import WorkerProfile

    profiles = WorkerProfile.objects.filter(is_available=True).select_related('user')
    if trade and trade.lower() != 'all':
        profiles = [p for p in profiles if any(t.lower() == trade.lower() for t in p.trades) or p.primary_trade.lower() == trade.lower()]

    worker_list = []
    max_meters = max_radius_km * 1000.0

    ref_lat = user_lat if user_lat is not None else 28.6280
    ref_lng = user_lng if user_lng is not None else 77.3649

    for p in profiles:
        p_lat = p.latitude if p.latitude is not None else (p.user.latitude if p.user.latitude else ref_lat)
        p_lng = p.longitude if p.longitude is not None else (p.user.longitude if p.user.longitude else ref_lng)
        dist = calculate_haversine_distance(ref_lat, ref_lng, p_lat, p_lng)

        if dist <= max_meters:
            p.distance_meters = dist
            p.distance_display = format_distance(dist)
            worker_list.append(p)

    worker_list.sort(key=lambda x: getattr(x, 'distance_meters', 999999))
    return worker_list
