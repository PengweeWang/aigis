import os
from dotenv import load_dotenv
from pathlib import Path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api import AmapClient, direction_distence

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

out_dir = Path(__file__).resolve().parent

key = os.getenv("AMAP_API_KEY")

amap_client = AmapClient(key=key)

def test_geocode():
    response = amap_client.geocode("北京市朝阳区阜通东大街6号")
    # beautify the output
    import json
    print(json.dumps(response, indent=4, ensure_ascii=False))
    
def test_reverse_geocode():
    response = amap_client.reverse_geocode("116.603034,39.431568")
    import json
    print(json.dumps(response, indent=4, ensure_ascii=False))
    
def test_route_planning_driving():
    response = amap_client.route_planning_driving("116.481028,39.989643", "116.434446,39.90816")
    # save response to a file
    import json
    with open(out_dir / "route_planning_driving_response.json", "w", encoding="utf-8") as f:
        json.dump(response, f, indent=4, ensure_ascii=False)
        
def test_route_planning_walking():
    response = amap_client.route_planning_walking("116.373509,39.92247", "116.375946,39.919215")
    import json
    with open(out_dir / "route_planning_walking_response.json", "w", encoding="utf-8") as f:
        json.dump(response, f, indent=4, ensure_ascii=False)

def test_route_planning_bicycling():
    response = amap_client.route_planning_bicycling("116.434307,39.90909", "116.434446,39.90816")
    import json
    with open(out_dir / "route_planning_bicycling_response.json", "w", encoding="utf-8") as f:
        json.dump(response, f, indent=4, ensure_ascii=False)
        
def test_direction_distence():
    origin = "114.069694,22.620004"
    destination = "114.069925,22.620028"
    distance = direction_distence(origin, destination)
    print(f"Distance between {origin} and {destination} is {distance} meters.")
    
    
if __name__ == "__main__":
    test_geocode()
    test_reverse_geocode()
    test_route_planning_driving()
    test_route_planning_walking()
    test_route_planning_bicycling()
    test_direction_distence()




