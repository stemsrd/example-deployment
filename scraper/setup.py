from setuptools import setup, find_packages

setup(
    name='scraper',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'bs4>=0.0.1',
        'requests>=2.25.0',
        'selenium>=4.0.0',
        'webdriver-manager>=3.5.0',
    ],
)