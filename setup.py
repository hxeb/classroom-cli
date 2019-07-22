from setuptools import setup

with open('requirements.txt') as f:
    dependencies = f.read().split('\n')

setup(
    name='HXEBClass',
    version='0.1',
    py_modules=['hxeb_class'],
    install_requires=dependencies,
    entry_points='''
        [console_scripts]
        hxebclass=hxeb_class:cli
    '''
)
