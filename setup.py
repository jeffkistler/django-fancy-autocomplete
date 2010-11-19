import os
from distutils.core import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = 'django-fancy-autocomplete',
    version = '0.1a1',
    license = 'BSD',
    description = 'A simple AJAX autocomplete helper app for Django projects',
    long_description = read('README'),
    author = 'Jeff Kistler',
    author_email = 'jeff@jeffkistler.com',
    url = 'https://github.com/jeffkistler/django-fancy-autocomplete',
    packages = ['fancy_autocomplete'],
    package_dir = {'': 'src'},
    package_data = {'fancy_autocomplete': ['fixtures/*',]},
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
