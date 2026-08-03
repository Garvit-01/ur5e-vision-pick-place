from setuptools import find_packages, setup

package_name = 'my_first_robot'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/robot.launch.py']),
        ('share/' + package_name + '/urdf', ['urdf/my_robot.urdf','urdf/ur5e_robotiq.urdf.xacro']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ubuntu',
    maintainer_email='garvitkatyal2@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
    'console_scripts': [
        'publisher = my_first_robot.publisher:main',
        'subscriber = my_first_robot.subscriber:main',
        'publisher_cube = my_first_robot.publisher_cube:main',
        'subscriber_cube = my_first_robot.subscriber_cube:main',
        'gripper_service = my_first_robot.gripper_service:main',
        'gripper_client = my_first_robot.gripper_service_client:main',
        'move_action_server = my_first_robot.move_action_server:main',
        'move_action_client = my_first_robot.move_action_client:main',
        'moveit_commander = my_first_robot.moveit_commander:main',
        'moveit_cartesian = my_first_robot.moveit_cartesian:main',
        'pick_place = my_first_robot.pick_place:main',
        'pick_place_second = my_first_robot.pick_place_second:main',
        'ur5e_moveit_commander = my_first_robot.ur5e_moveit_commander:main',
        'ur5e_moveit_cartesian = my_first_robot.ur5e_moveit_cartesian:main',
        'ur5e_pick_place_second = my_first_robot.ur5e_pick_place_second:main',

    ]
},
)
