from setuptools import setup, find_packages

setup(

    name='graypy',
    version='0.1',
    description="Python logging handler that sends messages in GELF (Graylog Extended Log Format).",
    long_description=open('README').read(),
    keywords='logging gelf graylog2 graylog udp',
    author='Sever Banesiu',
    author_email='banesiu.sever@gmail.com',
    url='http://bitbucket.org/severb/graypy',
    license='BSD',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,

)
