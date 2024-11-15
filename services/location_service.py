import requests

def get_location_info(lat, lng):
    """Get location information from coordinates using Nominatim API"""
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        address = data.get('address', {})
        location_info = {
            'city': address.get('city'),
            'state': address.get('state'),
            'country': address.get('country'),
            'natural': address.get('natural'),
        }
        
        return location_info
    except Exception as e:
        return {'error': str(e)}
