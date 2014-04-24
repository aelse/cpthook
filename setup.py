from setuptools import setup
import os.path
__dir__ = os.path.dirname(os.path.abspath(__file__))

setup(
    name='cpthook',
    license='BSD',
    py_modules=['cpthook'],
    scripts=['cpthook'],
    version='1.0.0',
    install_requires=[],

    description='Centrally manage hooks for git repositories',
    long_description=open(os.path.join(__dir__, 'README.rst')).read(),

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
