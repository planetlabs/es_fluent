#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = []

test_requirements = [
    'sphinx_rtd_theme',
    'mock'
]

setup(
    name='es-fluent',
    version='0.0.2',
    description="Fluent API for generating elastic queries.",
    long_description=readme + '\n\n' + history,
    author="Jacob Straszynski",
    author_email='jacob.straszynski@planet.com',
    url='https://github.com/planetlabs/es_fluent',
    packages=[
        'es_fluent',
    ],
    package_dir={'es_fluent':
                 'es_fluent'},
    include_package_data=True,
    install_requires=requirements,
    license="Apache 2",
    zip_safe=False,
    keywords='es_fluent',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
