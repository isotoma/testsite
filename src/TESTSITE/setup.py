from setuptools import setup, find_packages

version = '0.0.1'

setup(
    name = 'testsite',
    version = version,
    description = "",
    long_description = "",
    author = "",
    author_email = "",
    url = "",
    license = "",
    packages = find_packages(),
    include_package_data = True,
    zip_safe = False,
    
    install_requires = [
        'south'
        ]
    )
