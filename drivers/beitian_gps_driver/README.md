# GPS数据处理包（未完成）

利用pynmea2读取串口数据,
使用前请安装`pip install pynmea2`

`/beitian_gps_driver/serial_reader` 是从串口读取数据并发布数据的节点，发布两个话题：`/gps/fix`和`/gps/pose`，格式分别为：`NavSatFix`和`Pose2D`。

`/launch/gps.launch.py`是主启动文件，读取数据、发布话题、坐标转换、启动mapviz
