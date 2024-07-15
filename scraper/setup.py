from setuptools import setup, find_packages

setup(
    name='scraper',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        urllib3<2.0
        bs4>=0.0.1
        psutil>=5.8.0
        requests>=2.25.0
        selenium>=4.0.0
        webdriver-manager>=3.5.0
    ],
)