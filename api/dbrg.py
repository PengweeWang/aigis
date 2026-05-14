"""
This module has not been implemented yet. It is an API implementation 
for the internal network dbrg. The specification of the returned results can be referred 
to the README.md file in this directory.
"""

class DbrgClient:
    def __init__(self, key: str):
        self.key = key
        self.base_url = "https://dbrg.internal.api/"

    def geocode(self, address: str) -> dict:
        pass

    def reverse_geocode(self, location: str) -> dict:
        pass

    def route_planning(self, origin: str, destination: str, mode: str) -> dict:
        pass