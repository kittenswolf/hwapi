from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='hwapi',
    version='0.1.3',

    description='Happy Wheels API Wrapper',
    long_description=long_description,
    long_description_content_type='text/markdown',

    url='https://github.com/kittenswolf/hwapi',
    author='kittenswolf',

    packages=find_packages(),
    install_requires=[
        "cachetools",
        "xmltodict",
        "aiohttp>3",
        "beautifulsoup4>4, <5"
    ],
    python_requires='>=3.6.0',
    project_urls={
        'Bug Reports': 'https://github.com/kittenswolf/hwapi/issues',
        'Source': 'https://github.com/kittenswolf/hwapi/'
    },
)
