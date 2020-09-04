#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import codecs
from setuptools import setup, find_packages
import os.path as osp


def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding='utf-8').read()


# Add your dependencies here
requirements = []
with open(osp.join('requirements', 'default.txt')) as f:
    for line in f:
        splitted = line.split("#")
        stripped = splitted[0].strip()
        if len(stripped) > 0:
            requirements.append(stripped)


setup(
    name='napari-svg',
    version='0.1.4',
    author='Nicholas Sofroniew',
    author_email='sofroniewn@gmail.com',
    maintainer='Nicholas Sofroniew',
    maintainer_email='sofroniewn@gmail.com',
    license='BSD-3',
    url='https://github.com/napari/napari-svg',
    description='A plugin for reading and writing svg files with napari',
    long_description=read('README.rst'),
    packages=find_packages(),
    python_requires='>=3.6',
    install_requires=requirements,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: BSD License',
    ],
    entry_points={
        'napari.plugin': [
            'svg = napari_svg',
        ],
    },
)
