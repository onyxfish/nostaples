#!/usr/bin/env python

from distutils.core import setup

setup(name='nostaples',
      version='0.1.0',
      description='GNOME Document Scanning Application',
      author='Christopher Groskopf',
      author_email='staringmonkey@gmail.com',
      url='http://www.etlafins.com/nostaples',
      license='GPL',
      packages=['nostaples'],
      package_dir={'nostaples' : ''},
      scripts = ['nostaples'],
      data_files=[('', ['logging.config', 'nostaples.glade']),
                  ('share/applications', ['data/nostaples.desktop'])]
     )

