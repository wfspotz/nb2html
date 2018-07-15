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
script   = 'nb2html.py'
csl      = 'Harvard.csl'
bib      = 'ref.bib'
notebook = 'SimpleCitation.ipynb'
html     = notebook.replace('ipynb','html')
ref_str  = u"Smith, A. (2018) ‘Peculiar effects of a polynational existence’, " \
           u"<em>Journal of Multiculturalism</em>, 97(D12), pp. 12, 771–12, 786."
script_src    = os.path.join(basedir, 'scripts'  , script  )
csl_src       = os.path.join(basedir, 'CSL'      , csl     )
bib_src       = os.path.join(basedir, 'scripts'  , bib     )
notebook_src  = os.path.join(basedir, 'notebooks', notebook)

@contextmanager
def temp_working_dir():
    testdir = tempfile.mkdtemp()
    curdir = os.getcwd()
    os.chdir(testdir)
    yield testdir
    os.chdir(curdir)
    shutil.rmtree(testdir)

def test_cli():
    # Create temporary directory as a context manager
    with temp_working_dir() as testdir:

        # Copy files to temporary directory
        script_dest   = os.path.join(testdir, script  )
        csl_dest      = os.path.join(testdir, csl     )
        bib_dest      = os.path.join(testdir, bib     )
        notebook_dest = os.path.join(testdir, notebook)
        shutil.copyfile(script_src  , script_dest  )
        shutil.copyfile(csl_src     , csl_dest     )
        shutil.copyfile(bib_src     , bib_dest     )
        shutil.copyfile(notebook_src, notebook_dest)

        # Show the directory
        print(testdir)
        for f in os.listdir(testdir):
            print('   ', f)

        subprocess.call([sys.executable, script, '--csl', csl, notebook])
        assert os.path.isfile(html)

def test_html():
    # Create temporary directory as a context manager
    with temp_working_dir() as testdir:

        # Copy files to temporary directory
        script_dest   = os.path.join(testdir, script  )
        csl_dest      = os.path.join(testdir, csl     )
        bib_dest      = os.path.join(testdir, bib     )
        notebook_dest = os.path.join(testdir, notebook)
        shutil.copyfile(script_src  , script_dest  )
        shutil.copyfile(csl_src     , csl_dest     )
        shutil.copyfile(bib_src     , bib_dest     )
        shutil.copyfile(notebook_src, notebook_dest)

        # Show the directory
        print(testdir)
        for f in os.listdir(testdir):
            print('   ', f)

        subprocess.call([sys.executable, script, '--csl', csl, notebook])

        with io.open(html,'r') as html_file:
            assert ref_str in html_file.read()
