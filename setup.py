from setuptools import setup, find_packages

setup(
    name="evanai-client",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'evanai-client=evanai_client.main:cli',
        ],
    },
    install_requires=[
        "anthropic>=0.39.0",
        "websocket-client>=1.6.0",
        "asyncio>=3.4.3",
        "aiohttp>=3.9.0",
        "click>=8.1.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
        "colorama>=0.4.6",
        "requests>=2.31.0",
    ],
    python_requires=">=3.8",
)