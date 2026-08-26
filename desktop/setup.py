# setup.py
from setuptools import setup, find_packages

setup(
    name="CritiCat",
    version="1.0.0",
    description="Система мониторинга критических значений лабораторных исследований",
    author="Your Name",
    author_email="my.lsd25@gmail.com",
    packages=find_packages(),
    install_requires=[
        'PySide6>=6.5.0',
        'requests>=2.28.0',
        'cryptography>=41.0.0',
        'Pillow>=10.0.0',
    ],
    entry_points={
        'console_scripts': [
            'criticat=main:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Healthcare Industry',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    python_requires='>=3.8',
)