from setuptools import find_packages, setup
from glob import glob

package_name = 'beitian_gps_driver'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
        ('share/' + package_name + '/config', glob('config/*.mvc')),
        ('share/' + package_name + '/launch', glob('launch/*.py')),
    ],
    install_requires=['setuptools', 'pyserial', 'pynmea2', 'chardet'],
    zip_safe=True,
    maintainer='lab1',
    maintainer_email='chencanghao@foxmail.com',
    description='Package for beitian gps driver',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'serial_reader = beitian_gps_driver.serial_reader:main',
            'accuracy_test = beitian_gps_driver.accuracy_test:main',
            'gps_reader = beitian_gps_driver.gps_reader:main',
            'gps_writer = beitian_gps_driver.gps_writer:main',
            'virtual_serial = beitian_gps_driver.virtual_serial:main'
        ],
    },
)
