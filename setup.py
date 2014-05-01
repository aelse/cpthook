# This file is part of the cpthook library.
#
# cpthook is free software released under the BSD License.
# Please see the LICENSE file included in this distribution for
# terms of use. This LICENSE is also available at
# https://github.com/aelse/cpthook/blob/master/LICENSE

from setuptools import setup

__long_desc__ = """If you use a central repository manager such as gitolite
or gitosis you probably have at least a few repositories using custom git
hooks.

Managing the hooks in all your repositories by hand, is time consuming
and prone to error. If you need to take advantage of the functionality
provided by more than one hook script you are left to do it yourself.

cpthook allows you to run more than one hook in each repo and manage
them all in one location."""

setup(
    name='cpthook',
    license='BSD',
    py_modules=['cpthook'],
    scripts=['cpthook'],
    version='1.0.2',
    install_requires=[],

    description='Centrally manage hooks for git repositories',
    long_description=__long_desc__,

    author='Alexander Else',
    author_email='aelse@else.id.au',
    url='https://github.com/aelse/cpthook',

    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: Other/Proprietary License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Topic :: Software Development",
        "Topic :: System :: Systems Administration",
    ]
)
