""" A setupools based setup module. """

from setuptools import setup

setup(name='structer',
      version='0.0.5',
      description='Interpret packed binary data using named attributes',
      url='https://github.com/wackrat/structer',
      author='Eirik Fuller',
      author_email='wackrat@gmail.com',
      license='MIT',
      classifiers=[
          'Development Status :: 3 - Alpha',

          'Intended Audience :: Developers',
          'Topic :: Software Development :: Libraries :: Python Modules',

          'License :: OSI Approved :: MIT License',

          'Programming Language :: Python :: 3.5',
      ],
      packages=['structer', 'structer.elf'],
      entry_points={
          'console_scripts': [
              'build_ids = structer.build_ids:main',
              ]
          }
     )
