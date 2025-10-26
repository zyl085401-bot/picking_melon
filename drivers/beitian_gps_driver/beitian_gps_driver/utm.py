import pyproj


def get_utm_zone(latitude, longitude):
    """
    根据给定的纬度和经度自动选择 UTM 带号.

    :param latitude: 纬度 (Decimal degrees)
    :param longitude: 经度 (Decimal degrees)
    :return: 选择的 UTM 带号 (例如: "33N" 或 "33S")
    """
    # 计算 UTM 带号，带区编号从 1 到 60
    zone_number = int((longitude + 180) / 6) + 1

    # 根据纬度确定南半球或北半球
    hemisphere = "N" if latitude >= 0 else "S"

    return f"{zone_number}{hemisphere}"


def latlon_to_utm(latitude, longitude):
    """
    将给定的经纬度转换为 UTM 坐标.

    :param latitude: 纬度 (Decimal degrees)
    :param longitude: 经度 (Decimal degrees)
    :return: UTM 坐标 (X 和 Y)
    """
    # 获取自动选择的 UTM 带号
    utm_zone = get_utm_zone(latitude, longitude)

    # 创建 WGS84 坐标系 (经纬度坐标系)
    wgs84 = pyproj.CRS("EPSG:4326")

    # 根据 UTM 带号创建 UTM 坐标系 (例如: EPSG:32633 代表 UTM 33N)
    zone_number = int(utm_zone[:-1])  # 带号 (如 33)
    hemisphere = utm_zone[-1]  # N 或 S
    utm_crs_code = f"EPSG:326{zone_number}" if hemisphere == "N" else f"EPSG:327{zone_number}"
    utm_crs = pyproj.CRS(utm_crs_code)

    # 创建转换器
    transformer = pyproj.Transformer.from_crs(wgs84, utm_crs)

    # 转换为 UTM 坐标
    utm_x, utm_y = transformer.transform(latitude, longitude)

    return utm_x, utm_y, utm_zone


# # 示例使用
# latitude = 40.748817
# longitude = -73.985428
# utm_x, utm_y, utm_zone = latlon_to_utm(latitude, longitude)

# print(f"自动选择的 UTM 带号: {utm_zone}")
# print(f"UTM 坐标: X = {utm_x} m, Y = {utm_y} m")
