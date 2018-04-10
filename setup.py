from setuptools import setup
from setuptools.command.install import install
import os



class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        usr = os.path.expanduser("~")
        if not os.path.isdir(os.path.join(usr, 'YAP')):
            os.mkdir(os.path.join(usr, 'YAP'))
        with open(os.path.join(usr, 'YAP', 'sstvProxy.py'), "wb") as file:
            # get request
            from requests import get
            response = get("https://raw.githubusercontent.com/vorghahn/sstvProxy/master/sstvProxy.py")
            # write to file
            file.write(response.content)


setup(
  name = 'YAPSSTV',
  version = '1.1',
  cmdclass = {'install': PostInstallCommand},
  description = 'Yet Another Proxy',
  python_requires = '>=3.5',
  install_requires=[
          'requests',
          'flask',
          'flask-login',
          'flask-SQLAlchemy'
  ]
)