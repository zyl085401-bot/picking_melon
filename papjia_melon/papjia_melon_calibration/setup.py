from setuptools import find_packages, setup

package_name = 'papjia_melon_calibration'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ygao',
    maintainer_email='695314919@qq.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'handeye_calibration_collector = papjia_melon_calibration.handeye_calibration_data_collector:main',
            'handeye_calibration_from_file = papjia_melon_calibration.handeye_calibration_from_file:main',
        ],
    },
)
