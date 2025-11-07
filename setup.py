"""
Setup script for LVFontConv
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_file(filename):
    filepath = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return ''

# Read version from __init__.py
def get_version():
    init_file = os.path.join(os.path.dirname(__file__), 'src', '__init__.py')
    with open(init_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"\'')
    return '0.1.0'

setup(
    name='lvfontconv',
    version=get_version(),
    author='LVFontConv Development Team',
    author_email='',
    description='A PyQt6-based font converter for LVGL with preview capabilities',
    long_description=read_file('README.md'),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/lvfontconv',
    packages=find_packages(),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        'PyQt6>=6.4.0',
        'fontTools>=4.38.0',
        'freetype-py>=2.3.0',
        'Pillow>=9.3.0',
        'numpy>=1.24.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.2.0',
            'pytest-qt>=4.2.0',
            'pytest-cov>=4.0.0',
            'black>=23.1.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'lvfontconv=main:main',
        ],
        'gui_scripts': [
            'lvfontconv-gui=main:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
        'Environment :: X11 Applications :: Qt',
    ],
    python_requires='>=3.9',
    keywords='font converter lvgl embedded bitmap ttf otf woff',
    project_urls={
        'Documentation': 'https://github.com/yourusername/lvfontconv/docs',
        'Source': 'https://github.com/yourusername/lvfontconv',
        'Tracker': 'https://github.com/yourusername/lvfontconv/issues',
    },
)
