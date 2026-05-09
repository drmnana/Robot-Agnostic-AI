from setuptools import find_packages, setup

package_name = "payload_manager"

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
    description="Payload command gate and state coordinator for ORIMUS.",
    license="Proprietary",
    entry_points={
        "console_scripts": [
            "payload_manager_node = payload_manager.payload_manager_node:main",
        ],
    },
)

