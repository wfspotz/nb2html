#! /usr/bin/env python
# -*- coding: utf-8 -*-

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
bib      = 'ref.bib'
notebook = 'SimpleCitation.ipynb'
html     = notebook.replace('ipynb','html')
ref_str  = u"Smith, A. (2018) ‘Peculiar effects of a polynational existence’, " \
           u"<em>Journal of Multiculturalism</em>, 97(D12), pp. 12, 771–12, 786."
csl_src       = os.path.join(basedir, 'shared', 'CSL', csl     )
bib_src       = os.path.join(basedir, 'notebooks'    , bib     )
notebook_src  = os.path.join(basedir, 'notebooks'    , notebook)

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
        subprocess.call([sys.executable, script, notebook])

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
        subprocess.call([sys.executable, script, notebook])

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

        # Run the command-line interface
        csl_dir = os.path.join(basedir, 'shared', 'CSL')
        assert os.path.isdir(csl_dir)
        subprocess.call([sys.executable, script, '--append-csl-path', csl_dir,
                         '--csl', csl, notebook])

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

        # Run the command-line interface
        csl_dir = os.path.join(basedir, 'shared', 'CSL')
        assert os.path.isdir(csl_dir)
        subprocess.call([sys.executable, script, '--prepend-csl-path', csl_dir,
                         '--csl', csl, notebook])

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

        # Run the command-line interface
        csl_dir = os.path.join(basedir, 'shared', 'CSL')
        assert os.path.isdir(csl_dir)
        subprocess.call([sys.executable, script, '--replace-csl-path', csl_dir,
                         '--csl', csl, notebook])

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
        subprocess.call([sys.executable, script, '--csl', 'Hahvahd.csl',
                         notebook])

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
                         notebook])

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
        subprocess.call([sys.executable, script, '--bib', bibfile, notebook])

        # Check the results
        check_html()
