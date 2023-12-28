from setuptools import setup
from pathlib import Path

def get_install_requires():
    """Returns requirements.txt parsed to a list"""
    fname = Path(__file__).parent / 'requirements.txt'
    targets = []
    if fname.exists():
        with open(fname, 'r') as f:
            targets = f.read().splitlines()
    return targets 

setup(
    name='semgrep',
    version='0.1',
    description='Semantic search for local files',
    author='ridulfo',
    packages=['semgrep'],
    install_requires=get_install_requires(),
    entry_points={
        'console_scripts': [
            'semgrep = semgrep:main'
        ]
    }
)
