#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Imports
import io
import os
import shutil
import subprocess
import sys
from contextlib import contextmanager
import tempfile

# Find resources
thisdir  = os.path.dirname(os.path.abspath(__file__))
basedir  = os.path.normpath(os.path.join(thisdir, '..'))
script   = os.path.join(basedir, 'scripts', 'nb2html.py')
csl      = 'Harvard.csl'
csl_new  = 'Hahvahd.csl'
bib      = 'ref.bib'
notebook = 'SimpleCitation.ipynb'
html     = notebook.replace('ipynb','html')
ref_str  = u"Smith, A. (2018) ‘Peculiar effects of a polynational existence’, " \
           u"<em>Journal of Multiculturalism</em>, 97(D12), pp. 12, 771–12, 786."
csl_src       = os.path.join(basedir, 'shared', 'CSL', csl     )
bib_src       = os.path.join(basedir, 'notebooks'    , bib     )
notebook_src  = os.path.join(basedir, 'notebooks'    , notebook)

# Make sure that the nb2html.py script can find the nbref package
env = os.environ
python_path = env.get("PYTHONPATH", '').split(':')
if basedir not in python_path:
    python_path.insert(0, basedir)
env["PYTHONPATH"] = ':'.join(python_path)

################################################################################

@contextmanager
def temp_working_dir():
    testdir = tempfile.mkdtemp()
    curdir = os.getcwd()
    os.chdir(testdir)
    yield testdir
    os.chdir(curdir)
    shutil.rmtree(testdir)

################################################################################

def check_html():
    with io.open(html,'r') as html_file:
        assert ref_str in html_file.read()

################################################################################

def test_cli():
    # Create temporary directory as a context manager
    with temp_working_dir() as testdir:

        # Copy files to temporary directory
        bib_dest      = os.path.join(testdir, bib     )
        notebook_dest = os.path.join(testdir, notebook)
        shutil.copyfile(bib_src     , bib_dest     )
        shutil.copyfile(notebook_src, notebook_dest)

        # Run the command-line interface
        subprocess.call([sys.executable, script, notebook], env=env)

        # Check the results
        assert os.path.isfile(html)

################################################################################

def test_html():
    # Create temporary directory as a context manager
    with temp_working_dir() as testdir:

        # Copy files to temporary directory
        bib_dest      = os.path.join(testdir, bib     )
        notebook_dest = os.path.join(testdir, notebook)
        shutil.copyfile(bib_src     , bib_dest     )
        shutil.copyfile(notebook_src, notebook_dest)

        # Run the command-line interface
        subprocess.call([sys.executable, script, notebook], env=env)

        # Check the results
        check_html()

################################################################################

def test_append_csl_path():
    # Create temporary directory as a context manager
    with temp_working_dir() as testdir:

        # Copy files to temporary directory
        bib_dest      = os.path.join(testdir, bib     )
        notebook_dest = os.path.join(testdir, notebook)
        shutil.copyfile(bib_src     , bib_dest     )
        shutil.copyfile(notebook_src, notebook_dest)

        # Make a new CSL directory
        csl_dir = os.path.join(testdir, 'CSL')
        os.mkdir(csl_dir)
        csl_dest = os.path.join(csl_dir, csl_new)
        shutil.copyfile(csl_src, csl_dest)

        # Run the command-line interface
        assert os.path.isdir(csl_dir)
        subprocess.call([sys.executable, script, '--append-csl-path', csl_dir,
                         '--csl', csl_new, notebook], env=env)

        # Check the results
        check_html()

################################################################################

def test_prepend_csl_path():
    # Create temporary directory as a context manager
    with temp_working_dir() as testdir:

        # Copy files to temporary directory
        bib_dest      = os.path.join(testdir, bib     )
        notebook_dest = os.path.join(testdir, notebook)
        shutil.copyfile(bib_src     , bib_dest     )
        shutil.copyfile(notebook_src, notebook_dest)

        # Make a new CSL directory
        csl_dir = os.path.join(testdir, 'CSL')
        os.mkdir(csl_dir)
        csl_dest = os.path.join(csl_dir, csl_new)
        shutil.copyfile(csl_src, csl_dest)

        # Run the command-line interface
        assert os.path.isdir(csl_dir)
        subprocess.call([sys.executable, script, '--prepend-csl-path', csl_dir,
                         '--csl', csl_new, notebook], env=env)

        # Check the results
        check_html()

################################################################################

def test_replace_csl_path():
    # Create temporary directory as a context manager
    with temp_working_dir() as testdir:

        # Copy files to temporary directory
        bib_dest      = os.path.join(testdir, bib          )
        notebook_dest = os.path.join(testdir, notebook     )
        shutil.copyfile(bib_src     , bib_dest     )
        shutil.copyfile(notebook_src, notebook_dest)

        # Make a new CSL directory
        csl_dir = os.path.join(testdir, 'CSL')
        os.mkdir(csl_dir)
        csl_dest = os.path.join(csl_dir, csl_new)
        shutil.copyfile(csl_src, csl_dest)

        # Run the command-line interface
        assert os.path.isdir(csl_dir)
        subprocess.call([sys.executable, script, '--replace-csl-path', csl_dir,
                         '--csl', csl_new, notebook], env=env)

        # Check the results
        check_html()

################################################################################

def test_csl():
    # Create temporary directory as a context manager
    with temp_working_dir() as testdir:

        # Copy files to temporary directory
        csl_dest      = os.path.join(testdir, "Hahvahd.csl")
        bib_dest      = os.path.join(testdir, bib          )
        notebook_dest = os.path.join(testdir, notebook     )
        shutil.copyfile(csl_src     , csl_dest     )
        shutil.copyfile(bib_src     , bib_dest     )
        shutil.copyfile(notebook_src, notebook_dest)

        # Run the command-line interface
        subprocess.call([sys.executable, script, '--csl', csl_new, notebook],
                        env=env)

        # Check the results
        check_html()

################################################################################

def test_header():
    # Create temporary directory as a context manager
    with temp_working_dir() as testdir:

        # Copy files to temporary directory
        bib_dest      = os.path.join(testdir, bib     )
        notebook_dest = os.path.join(testdir, notebook)
        shutil.copyfile(bib_src     , bib_dest     )
        shutil.copyfile(notebook_src, notebook_dest)

        # Run the command-line interface
        new_header = 'Bibliography'
        subprocess.call([sys.executable, script, '--header', new_header,
                         notebook], env=env)

        # Check the results
        with io.open(html,'r') as html_file:
            assert new_header in html_file.read()

################################################################################

def test_bib():
    # Create temporary directory as a context manager
    with temp_working_dir() as testdir:

        # Copy files to temporary directory
        notebook_dest = os.path.join(testdir, notebook)
        shutil.copyfile(notebook_src, notebook_dest)

        # Run the command-line interface
        bibfile = os.path.join(basedir, 'notebooks', 'ref.bib')
        subprocess.call([sys.executable, script, '--bib', bibfile, notebook],
                        env=env)

        # Check the results
        check_html()
