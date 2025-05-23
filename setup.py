from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="knocodex",
    version="0.4.0",
    author="Knocodex Contributors",
    author_email="support@kno2gether.com",
    description="An open-source Python library for autonomous coding with AI agents with self improvement capabilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/avijeett007/knocodex",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "click>=8.0.0",
        "redis>=4.0.0",
        "rq>=2.3.3",               # Specific version to ensure compatibility with Connection usage
        "rq-dashboard>=0.6.0",
        "requests>=2.25.0",
        "colorama>=0.4.4",
        "tabulate>=0.8.9",
        "fastapi>=0.100.0",
        "uvicorn>=0.20.0",
        "sse-starlette>=1.6.0",
        "pydantic>=2.0.0",
        "python-multipart>=0.0.6",  # Required for form data handling in FastAPI
        "psutil>=5.9.0",
        "prometheus-client>=0.16.0",
        "anyio>=3.6.2",            # Required for SSE and async functionality
        "starlette>=0.40.0",       # Required for FastAPI
        "httpx>=0.24.0",           # Required for API client testing
    ],
    entry_points={
        "console_scripts": [
            "knocodex=knocodex.cli:main",
            "create-knocodex-project=knocodex.scripts.create_knocodex_project:main",
        ],
    },
    package_data={
        "knocodex": ["templates/**/*"],
    },
)
