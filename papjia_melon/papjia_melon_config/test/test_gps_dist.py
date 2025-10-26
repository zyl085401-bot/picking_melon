from geopy.distance import geodesic

def vincenty(lon1, lat1, lon2, lat2):
    # 创建两个点的经纬度坐标
    point1 = (lat1, lon1)
    point2 = (lat2, lon2)

    # 计算两点之间的距离
    distance = geodesic(point1, point2).kilometers
    return distance

if __name__ == '__main__':
    lon1 = -122.45462694307265
    lat1 = 38.16148295900207
    lon2 = -122.45463018815666
    lat2 = 38.16147895081198
    print(vincenty(lon1, lat1, lon2, lat2) * 1000)