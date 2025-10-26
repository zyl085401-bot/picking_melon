import serial

ser = serial.Serial('/dev/papjia_gps', 115200)

while True:
    info = ser.readline()
    print(info)