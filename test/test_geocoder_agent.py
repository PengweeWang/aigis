#!/usr/bin/env python3
"""
Test script for geocoder sub-agent functionality.
Tests the geocode and geodecode MCP tools directly.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

from api import AmapClient

# Initialize the client
key = os.getenv("AMAP_API_KEY")
if not key:
    raise RuntimeError("AMAP_API_KEY not found in environment or .env file")

client = AmapClient(key=key)

def test_geocode():
    """Test geocoding - address to coordinates"""
    print("=" * 60)
    print("TEST 1: Geocoding (address → coordinates)")
    print("=" * 60)
    
    test_addresses = [
        ("北京市朝阳区阜通东大街6号", None),
        ("上海市浦东新区世纪大道100号", None),
        ("广州市天河区珠江新城", "广州"),
        ("深圳市南山区科技园", "深圳"),
    ]
    
    for address, city in test_addresses:
        print(f"\nAddress: {address}" + (f" (City: {city})" if city else ""))
        print("-" * 40)
        
        try:
            result = client.geocode(address, city)
            geocodes = result.get("geocodes", [])
            
            if geocodes:
                print(f"✓ Found {len(geocodes)} result(s)")
                for i, geo in enumerate(geocodes, 1):
                    location = geo.get("location", "N/A")
                    formatted_address = geo.get("formatted_address", "N/A")
                    print(f"  {i}. Location: {location}")
                    print(f"     Address: {formatted_address}")
            else:
                print("✗ No results found")
                
        except Exception as e:
            print(f"✗ Error: {e}")

def test_reverse_geocode():
    """Test reverse geocoding - coordinates to address"""
    print("\n" + "=" * 60)
    print("TEST 2: Reverse geocoding (coordinates → address)")
    print("=" * 60)
    
    test_locations = [
        ("116.603034,39.431568", "Beijing area"),
        ("121.473701,31.230416", "Shanghai area"),
        ("113.324520,23.091015", "Guangzhou area"),
    ]
    
    for location, description in test_locations:
        print(f"\nLocation: {location} ({description})")
        print("-" * 40)
        
        try:
            result = client.reverse_geocode(location)
            formatted_address = result.get("formatted_address", "N/A")
            
            print(f"✓ Address: {formatted_address}")
            
            # Show additional details if available
            address_component = result.get("addressComponent", {})
            if address_component:
                province = address_component.get("province", "N/A")
                city = address_component.get("city", "N/A")
                district = address_component.get("district", "N/A")
                print(f"  Province: {province}")
                print(f"  City: {city}")
                print(f"  District: {district}")
                
        except Exception as e:
            print(f"✗ Error: {e}")

def test_mcp_tool_simulation():
    """Simulate MCP tool calls"""
    print("\n" + "=" * 60)
    print("TEST 3: Simulate MCP tool calls")
    print("=" * 60)
    
    # Simulate geocode tool call
    print("\nSimulating geocode tool call:")
    print("-" * 40)
    
    address = "北京市朝阳区阜通东大街6号"
    print(f"Tool: geocode")
    print(f"Parameters: address='{address}', city=None")
    
    try:
        result = client.geocode(address)
        print(f"Result: {json.dumps(result, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Simulate geodecode tool call
    print("\nSimulating geodecode tool call:")
    print("-" * 40)
    
    location = "116.603034,39.431568"
    print(f"Tool: geodecode")
    print(f"Parameters: location='{location}'")
    
    try:
        result = client.reverse_geocode(location)
        print(f"Result: {json.dumps(result, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n" + "=" * 60)
    print("TEST 4: Edge cases and error handling")
    print("=" * 60)
    
    # Test empty address
    print("\nTest 4.1: Empty address")
    print("-" * 40)
    try:
        result = client.geocode("")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error (expected): {type(e).__name__}: {e}")
    
    # Test invalid location format
    print("\nTest 4.2: Invalid location format")
    print("-" * 40)
    try:
        result = client.reverse_geocode("invalid,format")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error (expected): {type(e).__name__}: {e}")
    
    # Test nonexistent address
    print("\nTest 4.3: Nonexistent address")
    print("-" * 40)
    try:
        result = client.geocode("这是一个不存在的地址XYZ123")
        geocodes = result.get("geocodes", [])
        if geocodes:
            print(f"Found {len(geocodes)} result(s)")
        else:
            print("No results found (expected)")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Geocoder Sub-Agent Test Suite")
    print("=" * 60)
    
    test_geocode()
    test_reverse_geocode()
    test_mcp_tool_simulation()
    test_edge_cases()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)