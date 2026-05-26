import requests


class DbrgClient:
    """
    内网 GIS 数据服务客户端。
    接口对齐 amap.py，仅上游 API 不同。
    """

    def __init__(self, key: str = "", base_url: str = "http://192.168.30.11"):
        self.key = key
        self.base_url = base_url.rstrip("/")

    @staticmethod
    def _parse_location(loc: str):
        if not loc:
            return None
        parts = loc.split(",")
        if len(parts) != 2:
            return loc
        return {"lng": float(parts[0]), "lat": float(parts[1])}

    def geocode(self, address: str, city=None):
        """
        获取地址的经纬度信息（通过内网 Gazetteer 服务）

        上游 /hidata/gazetteer/ 响应除 code/message/data 外还返回 count（总数）、area（区域面数据），
        本方法对齐 amap.py 的 geocode 返回格式，不暴露 area 字段。

        :param address: 地址/地名关键词
        :param city: 可选，追加到关键词中缩小范围
        :return: {status, count, geocodes: [{formatted_address, location}]}
        """
        params = {"keywords": address}
        if city:
            params["keywords"] = f"{address} {city}"
        resp = requests.get(f"{self.base_url}/hidata/gazetteer/", params=params)
        data = resp.json()

        geocodes = []
        for item in data.get("data", []):
            geocodes.append({
                "formatted_address": item.get("address"),
                "location": {"lng": item.get("lon"), "lat": item.get("lat")},
            })

        return {
            "status": "1" if data.get("code") == 200 else "0",
            "count": str(len(geocodes)),
            "geocodes": geocodes,
        }

    def reverse_geocode(self, location: str):
        """
        获取经纬度对应的地址信息（通过内网 Gazetteer 服务，以坐标为中心小半径搜索）

        上游 /hidata/gazetteer/ 响应除 code/message/data 外还返回 count（总数）、area（区域面数据），
        本方法对齐 amap.py 的 reverse_geocode 返回格式，不暴露 area/count 字段。

        :param location: 经纬度字符串 "lng,lat"
        :return: {status, formatted_address, location}
        """
        loc = self._parse_location(location)
        if not loc:
            return {
                "status": "0",
                "formatted_address": "",
                "location": location,
            }
        params = {
            "lon": loc["lng"],
            "lat": loc["lat"],
            "radius": 100,
        }
        resp = requests.get(f"{self.base_url}/hidata/gazetteer/", params=params)
        data = resp.json()

        first = data.get("data", [None])[0] if data.get("data") else None
        return {
            "status": "1" if data.get("code") == 200 else "0",
            "formatted_address": first.get("address") if first else "",
            "location": loc,
        }

    def route_planning(self, origin: str, destination: str, mode: str) -> dict:
        raise NotImplementedError("DbrgClient.route_planning 尚未实现")
