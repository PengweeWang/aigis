import math

def direction_distence(loc1: str, loc2: str) -> float:
    """
    计算两个经纬度之间的距离，单位为米
    :param loc1: 第一个经纬度字符串，经度在前，纬度在后，经纬度间以“,”分割。
    :param loc2: 第二个经纬度字符串，经度在前，纬度在后，经纬度间以“,”分割。
    :return: 两个经纬度之间的距离，单位为米
    """
    lon1, lat1 = map(float, loc1.split(","))
    lon2, lat2 = map(float, loc2.split(","))
    
    # 将经纬度转换为弧度
    lon1_rad = math.radians(lon1)
    lat1_rad = math.radians(lat1)
    lon2_rad = math.radians(lon2)
    lat2_rad = math.radians(lat2)
    
    # 地球半径，单位为米
    R = 6371000
    
    # 计算两点之间的距离
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    distance = R * c
    return distance