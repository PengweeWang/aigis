import requests

class AmapClient:
    def __init__(self, key: str):
        self.key = key
        self.base_url = "https://restapi.amap.com/"
        
    def geocode(self, address: str, city=None):
        """
        获取地址的经纬度信息
        :param address: 地址字符串
        :param city: 可选参数，指定城市的中文/中文全拼/citycode/adcode，
                     不支持县级市。当指定城市查询内容为空时，会进行全国范围内的地址转换检索。
        :return: 包含经纬度信息的JSON响应
        """
        url = f"{self.base_url}v3/geocode/geo"
        params = {
            "key": self.key,
            "address": address
        }
        if city:
            params["city"] = city
        response = requests.get(url, params=params)
        data = response.json()
        # Build minimal result: count, status, and for each geocode only formatted_address and location
        result = {
            "status": data.get("status"),
            "count": data.get("count"),
            "geocodes": []
        }
        for g in data.get("geocodes", []):
            result["geocodes"].append({
                "formatted_address": g.get("formatted_address"),
                "location": g.get("location")
            })
        return result
        
    
    def reverse_geocode(self, location: str):
        """
        获取经纬度对应的地址信息
        :param location: 经纬度字符串，经度在前，纬度在后，经纬度间以“,”分割，经纬度小数点后不要超过 6 位。
        :return: 包含地址信息的JSON响应
        """
        url = f"{self.base_url}v3/geocode/regeo"
        params = {
            "key": self.key,
            "location": location
        }
        response = requests.get(url, params=params)
        data = response.json()
        result = {
            "status": data.get("status"),
            "formatted_address": data.get("regeocode", {}).get("formatted_address"),
        }
        return result
    
    def _parse_route_result(self, data):
        result_paths = []

        for path in data.get("route", {}).get("paths", []):
            instructions = []
            polyline_points = []

            for step in path.get("steps", []):
                instructions.append(step.get("instruction"))

                polyline = step.get("polyline")
                if polyline:
                    polyline_points.extend(polyline.split(";"))

            result_paths.append({
                "instruction": instructions,
                "polyline": polyline_points
            })

        return {
            "status": data.get("status"),
            "count": data.get("count"),
            "paths": result_paths
        }
        
    
    def route_planning_driving(self, origin: str, destination: str, strategy=0):
        """
        获取路径规划信息
        :param origin: 起点经纬度字符串，经度在前，纬度在后，经纬度间以“,”分割，经纬度小数点后不要超过 6 位。
        :param destination: 终点经纬度字符串，经度在前，纬度在后，经纬度间以“,”分割，经纬度小数点后不要超过 6 位。
        :param strategy: 路径规划策略，默认为0（速度优先）
        :return: 包含路径规划信息的JSON响应
        """
        url = f"{self.base_url}v3/direction/driving"
        params = {
            "key": self.key,
            "origin": origin,
            "destination": destination,
            "strategy": strategy
        }
        response = requests.get(url, params=params)
        data = response.json()
        return self._parse_route_result(data)
    
    def route_planning_walking(self, origin: str, destination: str):
        """
        获取路径规划信息
        :param origin: 起点经纬度字符串，经度在前，纬度在后，经纬度间以“,”分割，经纬度小数点后不要超过 6 位。
        :param destination: 终点经纬度字符串，经度在前，纬度在后，经纬度间以“,”分割，经纬度小数点后不要超过 6 位。
        :return: 包含路径规划信息的JSON响应
        """
        url = f"{self.base_url}v3/direction/walking"
        params = {
            "key": self.key,
            "origin": origin,
            "destination": destination
        }
        response = requests.get(url, params=params)
        data = response.json()
        return self._parse_route_result(data)
    
    def route_planning_bicycling(self, origin: str, destination: str):
        """
        获取路径规划信息
        :param origin: 起点经纬度字符串，经度在前，纬度在后，经纬度间以“,”分割，经纬度小数点后不要超过 6 位。
        :param destination: 终点经纬度字符串，经度在前，纬度在后，经纬度间以“,”分割，经纬度小数点后不要超过 6 位。
        :return: 包含路径规划信息的JSON响应
        """
        url = f"{self.base_url}v4/direction/bicycling"
        params = {
            "key": self.key,
            "origin": origin,
            "destination": destination
        }
        response = requests.get(url, params=params)
        data = response.json()
        # unwrap wrapper if present
        inner = data.get("data") if isinstance(data.get("data"), dict) else data

        # find paths (support several possible shapes)
        paths = inner.get("paths") or inner.get("route", {}).get("paths") or []

        # build status: map errcode==0 -> "1" as success, else try existing status
        if "errcode" in data:
            status = "1" if data.get("errcode") == 0 else str(data.get("errcode"))
        else:
            status = inner.get("status") or data.get("status")

        # count: prefer explicit count, otherwise use number of paths
        count = inner.get("count") or data.get("count") or str(len(paths))

        norm = {
            "status": status,
            "count": count,
            "route": {"paths": paths}
        }

        return self._parse_route_result(norm)
    
    def route_planing(self, origin: str, destination: str, mode="driving", strategy=0):
        """
        获取路径规划信息
        :param origin: 起点经纬度字符串，经度在前，纬度在后，经纬度间以“,”分割，经纬度小数点后不要超过 6 位。
        :param destination: 终点经纬度字符串，经度在前，纬度在后，经纬度间以“,”分割，经纬度小数点后不要超过 6 位。
        :param mode: 路径规划模式，支持"driving"（驾车）、"walking"（步行）、"bicycling"（骑行）
        :param strategy: 路径规划策略，默认为0（速度优先），仅对驾车模式有效
        :return: 包含路径规划信息的JSON响应
        """
        if mode == "driving":
            return self.route_planning_driving(origin, destination, strategy)
        elif mode == "walking":
            return self.route_planning_walking(origin, destination)
        elif mode == "bicycling":
            return self.route_planning_bicycling(origin, destination)
        else:
            raise ValueError("Unsupported mode. Use 'driving', 'walking', or 'bicycling'.")
