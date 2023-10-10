from setuptools import setup, find_packages

# Read requirements.txt and remove any comments
with open('requirements.txt') as f:
    requirements = f.read().splitlines()
    requirements = [r for r in requirements if not r.startswith('#')]

# Read dev-requirements.txt for development dependencies
with open('dev-requirements.txt') as f:
    dev_requirements = f.read().splitlines()
    dev_requirements = [r for r in dev_requirements if not r.startswith('#')]

setup(
    name='quirk',
    version='0.1.0',
    url='https://github.com/KPrasch/quirk',
    author='Kieran Prasch',
    author_email='kieranprasch@gmail.com',
    description='A [discord] bot for relaying Web3 events',
    packages=find_packages(),
    install_requires=requirements,
    extras_require={
        'dev': dev_requirements,  # Include development dependencies under 'dev' extras
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.9',
    ],
)
