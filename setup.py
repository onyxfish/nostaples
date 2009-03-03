#!/usr/bin/env python

from distutils.core import setup

setup(name='nostaples',
      version='0.3.0',
      description='GNOME Document Scanning Application',
      author='Christopher Groskopf',
      author_email='staringmonkey@gmail.com',
      url='http://www.etlafins.com/nostaples',
      license='GPL',
      packages=['nostaples', 'nostaples.controllers', 'nostaples.models', 'nostaples.utils', 'nostaples.views', 'nostaples.unittests', 'nostaples.sane'],
      package_dir={'nostaples' : ''},
      package_data={'nostaples' : ['logging.config', 'gui/*.glade']},
      scripts = ['nostaples'],
      data_files=[('share/applications', ['data/nostaples.desktop'])]
     )

