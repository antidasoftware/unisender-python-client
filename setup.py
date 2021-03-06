import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="unisender-python-client",
    version="0.0.1",
    author="Azat Zakirov",
    author_email="zakirmalay@gmail.com",
    description="python client for unisender API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/python-unisender",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        'requests'
    ],

)