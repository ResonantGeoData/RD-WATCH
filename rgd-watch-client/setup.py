from pathlib import Path

from setuptools import find_packages, setup

base_dir = Path(__file__).parent
readme_file = base_dir / 'README.md'
if readme_file.exists():
    with readme_file.open() as f:
        long_description = f.read()
else:
    # When this is first installed in development Docker, README.md is not available
    long_description = ''

__version__ = '0.0.1'

setup(
    name='rgd-watch-client',
    version=__version__,
    description='Make web requests to a Resonant GeoData WATCH instance.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='Apache 2.0',
    author='Kitware, Inc.',
    author_email='rgd@kitware.com',
    url='https://github.com/ResonantGeoData/RD-WATCH',
    keywords='',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python',
    ],
    python_requires='>=3.8',
    packages=find_packages(),
    install_requires=['rgd_client==0.2.13'],
    extras_require={'dev': ['ipython']},
    entry_points={'rgd_client.plugin': ['rgd_watch_client = rgd_watch_client:WATCHClient']},
)
