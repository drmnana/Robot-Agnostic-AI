from setuptools import find_packages, setup

package_name = "mission_api_bridge"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="DrMnana",
    maintainer_email="103401387+drmnana@users.noreply.github.com",
    description="ROS-aware HTTP API bridge for ORIMUS mission commands.",
    license="Proprietary",
    entry_points={
        "console_scripts": [
            "mission_api_bridge_node = mission_api_bridge.mission_api_bridge_node:main",
        ],
    },
)

