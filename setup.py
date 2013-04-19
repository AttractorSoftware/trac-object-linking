from setuptools import setup

PACKAGE = 'ObjectLinking'
VERSION = '0.2'

setup(
    name=PACKAGE,
    version=VERSION,
    description='Generic object linking plugin for trac, with extract ticket functionality.',
    author="WorksForWeb",
    author_email="info@worksforweb.com",
    license='',
    url='',
    packages = ['objectlinking'],
    entry_points = {
        'trac.plugins': [
            'objectlinking.main = objectlinking.main',
            'objectlinking.environment = objectlinking.environment',
        ]
    },
    package_data = {
        'objectlinking': [
            'htdocs/*.css',
            'htdocs/*.js',
            'templates/*.html',
        ],
    }
)
