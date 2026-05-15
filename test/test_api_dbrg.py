import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api import DbrgClient

dbrg_client = DbrgClient(key="")


def test_geocode():
    response = dbrg_client.geocode("四方坪地铁站")
    import json
    print("=== geocode ===")
    print(json.dumps(response, indent=4, ensure_ascii=False))


def test_geocode_with_city():
    response = dbrg_client.geocode("四方坪", city="长沙")
    import json
    print("=== geocode (with city) ===")
    print(json.dumps(response, indent=4, ensure_ascii=False))


def test_reverse_geocode():
    response = dbrg_client.reverse_geocode("112.998917,28.230730")
    import json
    print("=== reverse_geocode ===")
    print(json.dumps(response, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    test_geocode()
    test_geocode_with_city()
    test_reverse_geocode()
