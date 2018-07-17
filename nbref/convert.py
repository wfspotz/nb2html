
################################################################################

# Module imports
import nbconvert
import nbformat
import os

################################################################################

# Object imports
from traitlets.config import Config

################################################################################

# Local imports
from .AddCitationsPreprocessor   import AddCitationsPreprocessor
from .VerboseExecutePreprocessor import VerboseExecutePreprocessor

################################################################################

# Aliases and global variables
HTMLExporter = nbconvert.HTMLExporter
FilesWriter  = nbconvert.writers.FilesWriter

################################################################################

def convert(filename, options):
    """
    Take as input a filename for a Jupyter Notebook (and a variety of options)
    and write an HTML file that is a representation of that notebook.
    """

    # Open the Jupyter notebook
    (basename, ext) = os.path.splitext(filename)
    response = open(filename,"r").read()
    if options.verbose:
        print('Reading "%s"' % filename)
    notebook = nbformat.reads(response, as_version=4)

    # Configure the HTMLExporter to use the preprocessors
    cfg = Config()
    cfg.ExecutePreprocessor.enabled           = True
    cfg.ExecutePreprocessor.kernel_name       = options.kernel
    cfg.ExecutePreprocessor.timeout           = options.timeout
    cfg.VerboseExecutePreprocessor.enabled    = True
    cfg.VerboseExecutePreprocessor.verbose    = options.verbose
    cfg.AddCitationsPreprocessor.enabled      = True
    cfg.AddCitationsPreprocessor.verbose      = options.verbose
    cfg.AddCitationsPreprocessor.csl          = options.csl
    cfg.AddCitationsPreprocessor.csl_path     = options.csl_path
    cfg.AddCitationsPreprocessor.bibliography = options.bib
    cfg.AddCitationsPreprocessor.header       = options.header
    cfg.HTMLExporter.preprocessors = [VerboseExecutePreprocessor(config=cfg),
                                      AddCitationsPreprocessor(config=cfg)]

    # Convert the notebook to HTML
    html_exporter = HTMLExporter(config=cfg)
    if options.verbose:
        print('Converting "%s" to HTML' % filename)
    (body, resources) = html_exporter.from_notebook_node(notebook)

    # Output
    writer = FilesWriter()
    if options.verbose:
        print('Writing "%s.html"' % basename)
    writer.write(body, resources, notebook_name=basename)

