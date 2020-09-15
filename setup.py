import subprocess
import pathlib
from setuptools import setup
from setuptools.command.build_ext import build_ext


class checkout_submodule(build_ext):
    def run(self):
        build_temp = pathlib.Path(self.build_temp)
        build_temp.mkdir(parents=True, exist_ok=True)
        subprocess.check_call(['git', 'submodule', 'update', '--init'], cwd=self.build_temp)

setup(
    name='depthai_builder',
    version='0.0.1',
    description='The tool that allows you to build DepthAI pipeline using Python',
    url='https://github.com/luxonis/depthai-builder',
    author='Luxonis',
    author_email='support@luxonis.com',
    license='MIT',
    packages=['depthai_builder'],
    zip_safe=False,
    cmdclass={
        'build_ext': checkout_submodule
    },
)