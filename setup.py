import os

from setuptools import setup, find_packages

setup(
    name='release_notes_generator',
    version='0.1.0',
    description='A tool to generate release notes for GitHub projects.',
    long_description=open('README.md').read() if os.path.exists('README.md') else '',
    long_description_content_type='text/markdown',
    author='Miroslav Pojer',
    author_email='miroslav.pojer@absa.africa',
    url='https://github.com/AbsaOSS/generate-release-notes',
    packages=find_packages(),
    install_requires=[
        'PyGithub',
    ],
    python_requires='>=3.11',
    entry_points={
        'console_scripts': [
            'generate-release-notes=release_notes_generator.generator:run',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Version Control :: Git',
        'License :: OSI Approved :: Apache 2.0 License',
        'Programming Language :: Python :: 3.11',
    ],
)
