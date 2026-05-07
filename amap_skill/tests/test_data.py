"""
测试数据 - 用于技能验证和演示

包含各类典型查询场景的输入输出样例，便于开发者快速验证技能功能。
"""

# ============================================================
# POI 搜索类测试数据
# ============================================================

POI_KEYWORD_SEARCH_CASES = [
    {
        "name": "搜索北京咖啡店",
        "input": {"keywords": "咖啡店", "city": "北京"},
        "description": "在城市范围内按关键词搜索POI"
    },
    {
        "name": "搜索上海三甲医院",
        "input": {"keywords": "三甲医院", "city": "上海", "types": "医疗保健服务"},
        "description": "按关键词+类型联合搜索"
    },
    {
        "name": "搜索深圳购物中心",
        "input": {"keywords": "购物中心", "city": "深圳"},
        "description": "搜索特定类型的商业设施"
    },
    {
        "name": "搜索杭州西湖附近酒店",
        "input": {"keywords": "酒店|宾馆", "city": "杭州", "types": "住宿服务"},
        "description": "多关键词搜索"
    },
    {
        "name": "搜索广州加油站",
        "input": {"keywords": "加油站", "city": "广州", "types": "汽车服务"},
        "description": "搜索汽车服务类POI"
    },
]

POI_AROUND_SEARCH_CASES = [
    {
        "name": "天安门附近1公里停车场",
        "input": {"location": "116.397428,39.90923", "radius": 1000, "keywords": "停车场"},
        "description": "以地标为中心搜索周边设施"
    },
    {
        "name": "国贸附近500米餐厅",
        "input": {"location": "116.461447,39.908714", "radius": 500, "types": "餐饮服务"},
        "description": "按类型搜索周边餐饮"
    },
    {
        "name": "中关村附近3公里药店",
        "input": {"location": "116.317984,39.981931", "radius": 3000, "keywords": "药店|药房"},
        "description": "搜索周边医疗设施"
    },
    {
        "name": "陆家嘴附近2公里银行",
        "input": {"location": "121.499718,31.239703", "radius": 2000, "types": "金融保险服务"},
        "description": "搜索周边金融设施"
    },
]

POI_DETAIL_SEARCH_CASES = [
    {
        "name": "查询故宫详情",
        "input": {"poi_id": "B000A8UIN8"},
        "description": "通过POI ID查询详细信息"
    },
]

# ============================================================
# 地理编码类测试数据
# ============================================================

GEOCODE_CASES = [
    {
        "name": "北京朝阳区地址编码",
        "input": {"address": "北京市朝阳区阜通东大街6号", "city": "北京"},
        "description": "标准结构化地址编码"
    },
    {
        "name": "上海浦东地址编码",
        "input": {"address": "上海市浦东新区世纪大道1号"},
        "description": "不指定城市的地址编码"
    },
]

BATCH_GEOCODE_CASES = [
    {
        "name": "批量编码北京地址",
        "input": {
            "addresses": [
                "北京市朝阳区阜通东大街6号",
                "北京市海淀区中关村大街1号",
                "北京市东城区天安门广场",
                "北京市西城区金融街1号",
                "北京市丰台区南三环西路16号"
            ],
            "city": "北京"
        },
        "description": "批量处理多个同城市地址"
    },
    {
        "name": "批量编码不同城市地址",
        "input": {
            "addresses": [
                "北京市天安门广场",
                "上海市东方明珠",
                "广州市广州塔",
                "深圳市世界之窗",
                "杭州市西湖"
            ]
        },
        "description": "批量处理不同城市地址"
    },
]

REVERSE_GEOCODE_CASES = [
    {
        "name": "天安门坐标逆编码",
        "input": {"location": "116.397428,39.90923", "extensions": "all"},
        "description": "坐标转地址，返回周边POI"
    },
]

# ============================================================
# 路径规划类测试数据
# ============================================================

ROUTE_PLANNING_CASES = [
    {
        "name": "天安门到颐和园驾车",
        "input": {
            "origin": "116.397428,39.90923",
            "destination": "116.274722,39.998056",
            "mode": "driving"
        },
        "description": "驾车路径规划"
    },
    {
        "name": "天安门到王府井步行",
        "input": {
            "origin": "116.397428,39.90923",
            "destination": "116.417389,39.914917",
            "mode": "walking"
        },
        "description": "步行路径规划"
    },
    {
        "name": "国贸到中关村骑行",
        "input": {
            "origin": "116.461447,39.908714",
            "destination": "116.317984,39.981931",
            "mode": "cycling"
        },
        "description": "骑行路径规划"
    },
]

PUBLIC_TRANSIT_CASES = [
    {
        "name": "国贸到中关村公交",
        "input": {
            "origin": "116.461447,39.908714",
            "destination": "116.317984,39.981931",
            "city": "北京",
            "strategy": 0
        },
        "description": "最快捷公交方案"
    },
    {
        "name": "人民广场到陆家嘴地铁",
        "input": {
            "origin": "121.473701,31.230416",
            "destination": "121.499718,31.239703",
            "city": "上海",
            "strategy": 2
        },
        "description": "最少换乘公交方案"
    },
    {
        "name": "广州站到广州塔公交",
        "input": {
            "origin": "113.261889,23.150278",
            "destination": "113.324520,23.106440",
            "city": "广州",
            "strategy": 0
        },
        "description": "最快捷公交方案"
    },
]

TRUCK_PLANNING_CASES = [
    {
        "name": "北京货车路线",
        "input": {
            "origin": "116.527428,39.91923",
            "destination": "116.194722,39.998056",
            "truck_type": 3,
            "weight": 8.0,
            "height": 3.8,
            "width": 2.5,
            "load_weight": 12.0,
            "axis": 2
        },
        "description": "中型货车路径规划"
    },
]

LOGISTICS_PLANNING_CASES = [
    {
        "name": "多途径点配送路线",
        "input": {
            "origin": "116.397428,39.90923",
            "destination": "116.397428,39.90923",
            "waypoints": [
                "116.461447,39.908714",
                "116.317984,39.981931",
                "116.353944,39.965639",
                "116.427984,39.941931"
            ],
            "optimize_order": True
        },
        "description": "自动优化途径点顺序的配送路线"
    },
]

# ============================================================
# 地图交互类测试数据
# ============================================================

DISTRICT_SEARCH_CASES = [
    {
        "name": "查询北京下辖区县",
        "input": {"keywords": "北京", "subdistrict": 1, "extensions": "base"},
        "description": "查询直辖市下级行政区"
    },
    {
        "name": "查询上海浦东下级区域",
        "input": {"keywords": "浦东新区", "subdistrict": 2, "extensions": "base"},
        "description": "查询区级下级行政区"
    },
    {
        "name": "查询广东省下级市",
        "input": {"keywords": "广东", "subdistrict": 1, "extensions": "base"},
        "description": "查询省级行政区下的市"
    },
    {
        "name": "查询朝阳区边界",
        "input": {"keywords": "朝阳区", "subdistrict": 0, "extensions": "all", "city": "北京"},
        "description": "获取区域边界坐标用于绘制"
    },
]

WEATHER_SEARCH_CASES = [
    {
        "name": "北京实时天气",
        "input": {"city": "北京", "extensions": "base"},
        "description": "查询当前天气实况"
    },
    {
        "name": "上海天气预报",
        "input": {"city": "上海", "extensions": "all"},
        "description": "查询未来几天天气预报"
    },
    {
        "name": "深圳实时天气",
        "input": {"city": "440300", "extensions": "base"},
        "description": "使用adcode查询天气"
    },
]

COORDINATE_CONVERT_CASES = [
    {
        "name": "GPS坐标转高德坐标",
        "input": {
            "locations": "116.397428,39.90923",
            "coordsys": "gps"
        },
        "description": "WGS84坐标转GCJ-02"
    },
    {
        "name": "百度坐标转高德坐标",
        "input": {
            "locations": "116.404028,39.91523",
            "coordsys": "baidu"
        },
        "description": "BD-09坐标转GCJ-02"
    },
    {
        "name": "批量GPS坐标转换",
        "input": {
            "locations": "116.397428,39.90923|116.461447,39.908714|116.317984,39.981931",
            "coordsys": "gps"
        },
        "description": "批量坐标转换"
    },
]

IP_LOCATION_CASES = [
    {
        "name": "查询IP位置",
        "input": {"ip": "114.247.50.2"},
        "description": "根据IP地址查询地理位置"
    },
]

# ============================================================
# 距离量算测试数据
# ============================================================

DISTANCE_MEASURE_CASES = [
    {
        "name": "天安门到颐和园驾车距离",
        "input": {
            "origin": "116.397428,39.90923",
            "destination": "116.274722,39.998056",
            "mode": "driving"
        },
        "description": "驾车距离量算"
    },
    {
        "name": "国贸到中关村步行距离",
        "input": {
            "origin": "116.461447,39.908714",
            "destination": "116.317984,39.981931",
            "mode": "walking"
        },
        "description": "步行距离量算"
    },
]

# ============================================================
# 用户典型对话场景
# ============================================================

USER_CONVERSATION_SCENARIOS = [
    {
        "category": "POI搜索",
        "scenarios": [
            "帮我找一下北京三里屯附近的咖啡店",
            "我在上海陆家嘴，附近2公里内有没有银行？",
            "深圳南山区的购物中心有哪些？",
            "帮我搜索杭州西湖附近的五星级酒店",
            "广州天河区有什么好吃的餐厅？",
            "成都有哪些景点可以逛？",
            "我想找南京路步行街附近的地铁站",
        ]
    },
    {
        "category": "路径规划",
        "scenarios": [
            "从天安门到颐和园开车怎么走？",
            "我想从国贸骑车到中关村，帮我规划一下路线",
            "从人民广场到外滩走路远吗？",
            "从北京站到西单坐地铁怎么走最快？",
            "从上海虹桥机场到浦东机场怎么走最便宜？",
            "帮我规划一条从家到公司的路线，起点：望京SOHO，终点：国贸",
        ]
    },
    {
        "category": "距离量算",
        "scenarios": [
            "天安门到颐和园有多远？",
            "从北京到上海开车多少公里？",
            "国贸和中关村之间距离多少？",
            "从我家到公司步行多远？起点：望京，终点：国贸",
        ]
    },
    {
        "category": "地理编码",
        "scenarios": [
            "北京市朝阳区阜通东大街6号的经纬度是多少？",
            "经纬度116.397428,39.90923是什么地方？",
            "帮我查一下上海东方明珠的坐标",
            "这些地址对应的经纬度分别是多少：天安门、颐和园、鸟巢",
        ]
    },
    {
        "category": "行政区域",
        "scenarios": [
            "上海市有哪些区？",
            "北京市朝阳区的行政编码是多少？",
            "广东省下面有哪些地级市？",
            "帮我画出海淀区的行政边界",
        ]
    },
    {
        "category": "天气查询",
        "scenarios": [
            "北京今天天气怎么样？",
            "上海明天会下雨吗？",
            "未来三天深圳的天气如何？",
            "广州现在多少度？",
        ]
    },
    {
        "category": "坐标转换",
        "scenarios": [
            "这个GPS坐标116.397,39.909在高德地图上是多少？",
            "百度地图上的坐标怎么转到高德地图？",
        ]
    },
    {
        "category": "综合场景",
        "scenarios": [
            "我要去北京出差，帮我查一下北京明天的天气，还有从北京站到国贸的公交路线",
            "我在上海南京路，帮我找附近1公里内的咖啡店，再帮我规划步行过去的路线",
            "我要从深圳南山发货到福田，货车怎么走？限行吗？",
            "帮我查一下杭州西湖的坐标，然后在地图上标注出来，再查一下杭州明天天气",
        ]
    },
]
