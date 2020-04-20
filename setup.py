from setuptools import setup, find_packages
import os

# get wheel name
external_files = os.listdir(os.path.join(os.getcwd(), 'external'))
pyside_wheel = [whl for whl in external_files if whl.endswith('.whl') and whl.startswith("PySide2")][0]

setup(
    name="ventilator",
    author="vent team",
    author_email="vent@vents.com",
    description="some description of how we made a ventilator",
    keywords="vents ventilators etc",
    url="https://ventilator.readthedocs.io",

    version="0.0.2",
    packages=find_packages(),
    install_requires=[
        'numpy',
        'PySide2',
        'pyqtgraph>=0.11.0rc0'
    ],
    dependency_links=[
        os.path.join(os.getcwd(), 'external', pyside_wheel)
    ]
)