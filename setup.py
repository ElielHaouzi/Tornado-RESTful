"""
See:
https://packaging.python.org/en/latest/distributing.html
"""
import os
from setuptools import setup, find_packages

# To use a consistent encoding
from codecs import open

here = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='Tornado-RESTful',
    version='0.0.1',
    description='Restful api on Tornado',
    long_description=long_description,
    author='Eliel Haouzi',
    author_email='eliel.haouzi@gmail.com',
    packages=find_packages(),
    install_requires=["tornado"],
    include_package_data=True
)
