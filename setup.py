from setuptools import setup, find_packages
import os
import subprocess
import codecs
import os.path

depend_links = []

# detect if on raspberry pi, and
# set location to wheel if we are
IS_RASPI = False
try:
    ret = subprocess.call(['grep', '-q', 'BCM', '/proc/cpuinfo'])
    if ret == 0:
        IS_RASPI = True
        os.system("sudo +x INSTALL")
        os.system("sudo ./INSTALL")
except:
    # fine, not a raspi if it don't have grep or cpuinfo
    pass


    # keeping this around for proper packaging later
    # get wheel name
    #external_files = os.listdir(os.path.join(os.getcwd(), 'external'))
    #pyside_wheel = [whl for whl in external_files if whl.endswith('.whl') and whl.startswith("PySide2")][0]
    #depend_links.append(os.path.join(os.getcwd(), 'external', pyside_wheel))

def read(rel_path):
    """
    https://packaging.python.org/guides/single-sourcing-package-version/
    """
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()

def get_version(rel_path):
    """
    https://packaging.python.org/guides/single-sourcing-package-version/
    """
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


setup(
    name="pvp",
    author="pvp team",
    author_email="pvp@vents.com",
    description="some description of how we made a ventilator",
    keywords="vents ventilators etc",
    url="https://ventilator.readthedocs.io",
    version=get_version('pvp/__init__.py'),
    packages=find_packages(),
    install_requires=[
        'numpy',
        'PySide2==5.11.*',
        'pyqtgraph>=0.11.0rc0',
        'pytest-qt',
        'pytest-timeout',
        'pigpio',
        'tables',
        'scipy'
    ],
    package_data={
        "*": ["data/*", "assets/*", ""],
        "pvp": ["external/*",
                "gui/images/*",
                "io/config/*"]
    },
    dependency_links=depend_links,
    python_requires='>=3.7.*,<3.10'
)
