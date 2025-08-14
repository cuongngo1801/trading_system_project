"""Setup configuration for trading system package."""

import os

from setuptools import find_packages, setup

# Read the README file
current_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(current_dir, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# Read requirements
with open(os.path.join(current_dir, "requirements.txt"), encoding="utf-8") as f:
    requirements = [
        line.strip() for line in f if line.strip() and not line.startswith("#")
    ]

setup(
    name="trading-system",
    version="1.0.0",
    author="Trading Team",
    author_email="trading@company.com",
    description="Production-Grade Session-Based Trend Continuation Trading System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/trading-system-project",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
        ],
        "monitoring": [
            "prometheus-client>=0.16.0",
            "grafana-api>=1.0.3",
        ],
    },
    entry_points={
        "console_scripts": [
            "trading-system=trading_system.cli:main",
            "backtest=trading_system.backtest.cli:main",
            "live-trading=trading_system.execution.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "trading_system": [
            "config/*.yaml",
            "config/*.yml",
            "templates/*.j2",
        ],
    },
    zip_safe=False,
)
