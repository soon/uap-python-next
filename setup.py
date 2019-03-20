#!/usr/bin/env python
import os
from distutils import log
from distutils.core import Command
from distutils.command.build import build as _build
from setuptools import setup
from setuptools.command.develop import develop as _develop
from setuptools.command.sdist import sdist as _sdist
from setuptools.command.install import install as _install

import ua_parser_next


def check_output(*args, **kwargs):
    from subprocess import Popen
    proc = Popen(*args, **kwargs)
    output, _ = proc.communicate()
    rv = proc.poll()
    assert rv == 0, output


class build_regexes(Command):
    description = 'build supporting regular expressions from uap-core'
    user_options = [
        ('work-path=', 'w',
         "The working directory for source files. Defaults to ."),
        ('build-lib=', 'b',
         "directory for script runtime modules"),
        ('inplace', 'i',
         "ignore build-lib and put compiled javascript files into the source " +
         "directory alongside your pure Python modules"),
        ('force', 'f',
         "Force rebuilding of static content. Defaults to rebuilding on version "
         "change detection."),
    ]
    boolean_options = ['force']

    def initialize_options(self):
        self.build_lib = None
        self.force = None
        self.work_path = None
        self.inplace = None

    def finalize_options(self):
        install = self.distribution.get_command_obj('install')
        sdist = self.distribution.get_command_obj('sdist')
        build_ext = self.distribution.get_command_obj('build_ext')

        if self.inplace is None:
            self.inplace = (build_ext.inplace or install.finalized
                            or sdist.finalized) and 1 or 0

        if self.inplace:
            self.build_lib = '.'
        else:
            self.set_undefined_options('build',
                                       ('build_lib', 'build_lib'))
        if self.work_path is None:
            self.work_path = os.path.realpath(os.path.join(os.path.dirname(__file__)))

    def run(self):
        work_path = self.work_path
        if not os.path.exists(os.path.join(work_path, '.git')):
            return

        log.info('initializing git submodules')
        check_output(['git', 'submodule', 'init'], cwd=work_path)
        check_output(['git', 'submodule', 'update'], cwd=work_path)

        yaml_src = os.path.join(work_path, 'uap-core', 'regexes.yaml')
        if not os.path.exists(yaml_src):
            raise RuntimeError(
                'Unable to find regexes.yaml, should be at %r' % yaml_src)

        def force_bytes(text):
            if text is None:
                return text
            return text.encode('utf8')

        import yaml
        py_dest = os.path.join(self.build_lib, 'ua_parser_next', '_regexes.py')

        log.info('compiling regexes.yaml -> _regexes.py')
        with open(yaml_src, 'rb') as fp:
            regexes = yaml.safe_load(fp)
        with open(py_dest, 'wb') as fp:
            fp.write(b'# -*- coding: utf-8 -*-\n')
            fp.write(b'############################################\n')
            fp.write(b'# NOTICE: This file is autogenerated from  #\n')
            fp.write(b'# regexes.yaml. Do not edit by hand,       #\n')
            fp.write(b'# instead, re-run `setup.py build_regexes` #\n')
            fp.write(b'############################################\n')
            fp.write(b'\n')
            fp.write(b'from __future__ import absolute_import, unicode_literals\n')
            fp.write(b'from .user_agent_parser import (\n')
            fp.write(b'    UserAgentParser, DeviceParser, OSParser,\n')
            fp.write(b')\n')
            fp.write(b'\n')
            fp.write(b'__all__ = (\n')
            fp.write(b'    \'USER_AGENT_PARSERS\', \'DEVICE_PARSERS\', \'OS_PARSERS\',\n')
            fp.write(b')\n')
            fp.write(b'\n')
            fp.write(b'USER_AGENT_PARSERS = [\n')
            for device_parser in regexes['user_agent_parsers']:
                fp.write(b'    UserAgentParser(\n')
                fp.write(force_bytes('        %r,\n' % device_parser['regex']))
                fp.write(force_bytes('        %r,\n' % device_parser.get('family_replacement')))
                fp.write(force_bytes('        %r,\n' % device_parser.get('v1_replacement')))
                fp.write(force_bytes('        %r,\n' % device_parser.get('v2_replacement')))
                fp.write(b'    ),\n')
            fp.write(b']\n')
            fp.write(b'\n')
            fp.write(b'DEVICE_PARSERS = [\n')
            for device_parser in regexes['device_parsers']:
                fp.write(b'    DeviceParser(\n')
                fp.write(force_bytes('        %r,\n' % device_parser['regex']))
                fp.write(force_bytes('        %r,\n' % device_parser.get('regex_flag')))
                fp.write(force_bytes('        %r,\n' % device_parser.get('device_replacement')))
                fp.write(force_bytes('        %r,\n' % device_parser.get('brand_replacement')))
                fp.write(force_bytes('        %r,\n' % device_parser.get('model_replacement')))
                fp.write(b'    ),\n')
            fp.write(b']\n')
            fp.write(b'\n')
            fp.write(b'OS_PARSERS = [\n')
            for device_parser in regexes['os_parsers']:
                fp.write(b'    OSParser(\n')
                fp.write(force_bytes('        %r,\n' % device_parser['regex']))
                fp.write(force_bytes('        %r,\n' % device_parser.get('os_replacement')))
                fp.write(force_bytes('        %r,\n' % device_parser.get('os_v1_replacement')))
                fp.write(force_bytes('        %r,\n' % device_parser.get('os_v2_replacement')))
                fp.write(force_bytes('        %r,\n' % device_parser.get('os_v3_replacement')))
                fp.write(force_bytes('        %r,\n' % device_parser.get('os_v4_replacement')))
                fp.write(b'    ),\n')
            fp.write(b']\n')

        self.update_manifest()

    def update_manifest(self):
        sdist = self.distribution.get_command_obj('sdist')
        if not sdist.finalized:
            return

        sdist.filelist.files.append('ua_parser_next/_regexes.py')


class develop(_develop):
    def run(self):
        self.run_command('build_regexes')
        _develop.run(self)


class install(_install):
    def run(self):
        self.run_command('build_regexes')
        _install.run(self)


class build(_build):
    def run(self):
        self.run_command('build_regexes')
        _build.run(self)


class sdist(_sdist):
    sub_commands = _sdist.sub_commands + [('build_regexes', None)]


cmdclass = {
    'sdist': sdist,
    'develop': develop,
    'build': build,
    'install': install,
    'build_regexes': build_regexes,
}


setup(
    name='ua-parser-next',
    version=ua_parser_next.__version__,
    description="Python port of Browserscope's user agent parser",
    author='PBS',
    author_email='no-reply@pbs.org',
    packages=['ua_parser_next'],
    package_dir={'': '.'},
    license='Apache 2.0',
    zip_safe=False,
    url='https://github.com/soon/uap-python-next',
    include_package_data=True,
    setup_requires=['pyyaml'],
    install_requires=[],
    cmdclass=cmdclass,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
)
