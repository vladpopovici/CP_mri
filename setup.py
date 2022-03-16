#   -*- coding: utf-8 -*-
#
#  --------------------------------------------------------------------
#  Copyright (c) 2022 Vlad Popovici <popovici@bioxlab.org>
#
#  Licensed under the MIT License. See LICENSE file in root folder.
#  --------------------------------------------------------------------

#   -*- coding: utf-8 -*-
#
#  --------------------------------------------------------------------
#  Copyright (c) 2022 Vlad Popovici <popovici@bioxlab.org>
#
#  Licensed under the MIT License. See LICENSE file in root folder.
#  --------------------------------------------------------------------

from setuptools import setup

setup(
    name='cp_mri',
    version='0.2.0',
    description='MultiResolutionImage package for computational pathology (and ComPath).',
    url='https://github.com/vladpopovici/CP_mri',
    author='Vlad Popovici',
    author_email='popovici@bioxlab.org',
    license='MIT',
    packages=['cp_mri'],
    python_requires='>=3.8, <4',
    install_requires=['shapely',
                      'numpy',
                      'zarr',
                      'tifffile',
                      'scikit-image',
                      ],

    classifiers=[
        'Development Status :: 4 - Beta'
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8'
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)
