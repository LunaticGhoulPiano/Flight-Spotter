import requests
from bs4 import BeautifulSoup

class ADSB_LOL_API:
    def __init__(self):
        self.base_url = 'https://api.adsb.lol/'
    
    # v0
    def get_airport(self, icao: str):
        # Airports by ICAO
        # Data by https://github.com/vradarserver/standing-data/
        return requests.get(f'{self.base_url}api/0/airport/{icao}').json()
    
    def get_receiver(self):
        # Information about your receiver and global stats
        return requests.get(f'{self.base_url}api/0/me').json()
    
    def get_map(self):
        # My Map redirect based on IP
        return BeautifulSoup(requests.get(f'{self.base_url}api/0/my').text, 'html.parser').prettify()
    
    # v2
    def get_pia(self):
        # Aircrafts with PIA address (Privacy ICAO Address)
        # Returns all aircraft with PIA (https://nbaa.org/aircraft-operations/security/privacy/privacy-icao-address-pia/) address
        return requests.get(f'{self.base_url}v2/pia').json()
    
    def get_military(self):
        # Military registered aircrafts
        # Returns all military registered aircrafts
        return requests.get(f'{self.base_url}v2/mil').json()
    
    def get_ladd(self):
        # Aircrafts on LADD (Limiting Aircraft Data Displayed)
        # Returns all aircrafts on LADD (https://www.faa.gov/pilots/ladd) filter
        return requests.get(f'{self.base_url}v2/ladd').json()
    
    # TODO: mapping up all specific squawk code
    def get_by_squawk(self, squawk: str):
        # Aircrafts with specific squawk
        # Returns aircraft filtered by "squawk" transponder code (https://en.wikipedia.org/wiki/List_of_transponder_codes)
        pass

    # TODO: mapping up all specific aircraft type
    def get_by_aircraft_type(self, aircraft_type: str):
        # Aircrafts of specific type
        # Returns aircraft fitered by aircraft type designator code (https://en.wikipedia.org/wiki/List_of_aircraft_type_designators)
        pass

    def get_by_registration(self, reg: str):
        # Aircrafts with specific registration
        # Returns aircraft filtered by aircraft registration code (https://en.wikipedia.org/wiki/Aircraft_registration)
        return requests.get(f'{self.base_url}v2/registration/{reg}').json()
    
    def get_by_icao_hex(self, icao_hex: str):
        # Aircrafts with specific transponder hex code
        # Returns aircraft filtered by transponder hew code (https://en.wikipedia.org/wiki/Aviation_transponder_interrogation_modes#ICAO_24-bit_address)
        return requests.get(f'{self.base_url}v2/icao/{icao_hex}').json()
    
    def get_by_hex_icao(self, hex_icao: str):
        # Aircrafts with specific transponder hex code
        # Returns aircraft filtered by transponder hex code (https://en.wikipedia.org/wiki/Aviation_transponder_interrogation_modes#ICAO_24-bit_address)
        return requests.get(f'{self.base_url}v2/hex/{hex_icao}').json()
    
    def get_by_callsign(self, callsign: str):
        # Aircrafts with spectific callsign
        # Returns aircraft filtered by callsign (https://en.wikipedia.org/wiki/Aviation_call_signs)
        return requests.get(f'{self.base_url}v2/callsign/{callsign}').json()
    
    def get_by_surrounding(self, latitude: float, longitude: float, radius: int):
        # Aircrafts surrounding a point (lat, lon) up to 250nm
        # Returns aircraft located in a circle described by the latitude and longtidude of its center and its radius
        return requests.get(f'{self.base_url}v2/lat/{latitude}/lon/{longitude}/dist/{radius}').json()
    
    def get_by_surrounding_point(self, latitude: float, longitude: float, radius: int):
        # Aircrafts surrounding a point (lat, lon) up to 250nm
        # Returns aircraft located in a circle described by the latitude and longtidude of its center and its radius
        return requests.get(f'{self.base_url}v2/point/{latitude}/{longitude}/{radius}').json()
    
    def get_closest(self, latitude: float, longitude: float, radius: int):
        # Single aircraft closeset to a point (lat, lon)
        # Returns the closest aircraft to a point described by the latitude and longtidude within a radius up to 250nm
        return requests.get(f'{self.base_url}v2/closest/{latitude}/{longitude}/{radius}').json()