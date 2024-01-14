import os
import shutil
from typing import Any
from distutils.command.clean import clean
from setuptools import Extension
from setuptools import find_namespace_packages
from setuptools import setup
from setuptools.command.build_ext import build_ext
import pathlib
import subprocess
from glob import glob

# Assuming your shared object files are in the '_mlir_libs' directory
# and that the CMake directory you've built into is called 'build'
# TODO(fzakaria): Consider using the CMake extension module
# similar to https://github.com/makslevental/mlir-wheels/blob/2a74f388d987bb62f832660a975b51168e30d04f/setup.py#L15
lib_dir = os.path.normpath(
    '../../../build/python_packages/stablehlo/mlir/_mlir_libs')


class CMakeExtension(Extension):
  def __init__(self, name):
    # don't invoke the original build_ext for this special extension
    super().__init__(name, sources=[])


class CMakeBuild(build_ext):
  """This is a fake build_ext that doesn't do any building. It expects that the
  shared object files have already been built externally and are available at
  the lib_dir variable above. It then copies them into the extension directory."""
  def build_extension(self, ext: Any) -> None:
    # copy _ml_ir_libs into extension directory
    # self.get_ext_fullpath('xxx') gives you something like:
    # build/lib.linux-x86_64-cpython-311/xxx.cpython-311-x86_64-linux-gnu.so
    # we then take the parent directory and copy the contents of the
    # real _mlir_libs directory into the parent.
    # we make sure to also recreate the mlir/_mlir_libs directory
    ext_dir = pathlib.Path(self.get_ext_fullpath('ignored'))
    target_dir = ext_dir.parent / 'mlir' / '_mlir_libs'
    shutil.copytree(lib_dir, target_dir, dirs_exist_ok=True)


class CleanCommand(clean):
  """
    Custom implementation of ``clean`` setuptools command.
    """

  def run(self):
    """After calling the super class implementation, this function removes
        the dist directory if it exists and any egg files."""
    self.all = True  # --all by default when cleaning
    super().run()
    shutil.rmtree("dist", ignore_errors=True)
    for egg in glob('*.egg-info'):
      shutil.rmtree(egg, ignore_errors=True)

def get_version():
  # get the latest tag without the leading v
  latest_tag = subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"], text=True).strip('v').strip()
  latest_commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
  return f"{latest_tag}+{latest_commit}"

# TODO(fzakaria): The distribution (wheel) of this package is not manylinux
# conformant. Consider also running auditwheel similar to
# https://github.com/makslevental/mlir-wheels to make it a smoother installation
# experience.
setup(
    name='stablehlo',
    packages=find_namespace_packages(
        os.path.normpath("../../build/python_packages/stablehlo")),
    package_dir={
        "": os.path.normpath("../../../build/python_packages/stablehlo")},

    # Define extensions if your package needs to compile anything
    ext_modules=[CMakeExtension(name="_mlir_libs")],
    cmdclass={"build_ext": CMakeBuild, "clean": CleanCommand},

    author='Your Name',
    author_email='your.email@example.com',
    description='Backward compatible ML compute opset inspired by HLO/MHLO',
    url='https://github.com/openxla/stablehlo',
    # TODO(fzakaria): Figure out how to get version same as code; os.environ ?
    version = get_version()
)
