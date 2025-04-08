from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="hivemind-python",
    version="1.0.1",
    author="ValyrianTech",
    description="A Condorcet-style Ranked Choice Voting System that stores all data on IPFS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ValyrianTech/hivemind-python",
    license="MIT",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    # Add package mapping to make imports clearer
    py_modules=[],
    package_data={"hivemind": ["py.typed"]},  # Add py.typed marker file for type hints
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.10",
    install_requires=[
        "ipfs-dict-chain>=1.1.0",
        "python-bitcoinlib>=0.12.2",
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
        ],
    },
)
