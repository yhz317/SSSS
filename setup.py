#!/usr/bin/env python

import setuptools
from codecs import open
import os

here = os.path.abspath(os.path.dirname(__file__))
metadata = {}

with open(os.path.join(here, '__version__.py'), 'r', encoding='utf-8') as f:
    exec(f.read(), metadata)

with open('README.md', 'r', 'utf-8') as f:
    readme = f.read()

setuptools.setup(
    name=metadata['__name__'],
    version=metadata['__version__'],
    author=metadata['__author__'],
    author_email=metadata['__author_email__'],
    description=metadata['__description__'],
    long_description=readme,
    long_description_content_type='text/markdown',
    url=metadata['__url__'],
    packages=setuptools.find_packages(),
    install_requires=[
        # 'SSSS@git+ssh://git@github.com/lz356/SSSS.git@master',
        'beautifulsoup4',
        'numpy',
        'pandas',
        'requests',
        'tqdm'
    ],
    extras_require={
        'visualization': [
            'matplotlib',
            'wordcloud'
        ],
        'dev': [
            'pytest',
            'autopep8<2',
            'codecov',
            'flake8==5.0.4',
            'coverage',
            'pdoc3',
            'awscli'
        ]
    }
)
