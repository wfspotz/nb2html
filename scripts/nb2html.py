#! /usr/bin/env python

"""
Convert a Jupyter notebook to HTML, by executing the notebook and then
processing any references to publications to generate citations in the text and
a bibliography section at the end of the notebook
"""

################################################################################

# Module imports
import argparse
import glob
import nbconvert
import nbformat
import os
import pypandoc
import sys

################################################################################

# Object imports
from traitlets        import Bool
from traitlets        import List
from traitlets        import Unicode
from traitlets.config import Config

################################################################################

# Aliases and global variables
HTMLExporter         = nbconvert.HTMLExporter
Preprocessor         = nbconvert.preprocessors.Preprocessor
ExecutePreprocessor  = nbconvert.preprocessors.ExecutePreprocessor
FilesWriter          = nbconvert.writers.FilesWriter
NotebookNode         = nbformat.notebooknode.NotebookNode
python_version_major = str(sys.version_info.major)

################################################################################

def print_notebook(nb):
    """
    Print the ASCII contents of a notebook, cell by cell, limiting lines to 160
    characters.
    """
    numcells = len(nb.cells)
    for c in range(numcells):
        output = "%d: %s" % (c, str(nb.cells[c]))
        output = output.encode('ascii', 'ignore')
        if len(output) > 160:
            output = output[:157] + "..."
        print(output)

################################################################################

class VerboseExecutePreprocessor(ExecutePreprocessor):
    """
    Simple extension of ExecutePreprocessor that optionally prints when it is
    executing the notebook. It has the following configurable attributes:

        verbose      - Boolean that determines whether output to stdout is
                       turned on (default False)

        Inherited from ExecuteProcess:

            kernel_name  - The name of the kernel for executing the
                           notebook. Either 'python2' or 'python3'
            timeout      - Execution time before quitting
    """

    verbose = Bool(False,
                   help='Determines whether to provide output to stdout',
                   config=True)

    ############################################################################

    def preprocess(self, nb, resources):
        if self.verbose:
            print('    Executing notebook...')
        return ExecutePreprocessor.preprocess(self, nb, resources)

################################################################################

class AddCitationsExporter(HTMLExporter):
    """
    Add the AddCitationsPreprocessor class to the Preprocessor configuration.
    """
    @property
    def default_config(self):
        c = Config({
            'AddCitationsPreprocessor': {'enabled':True}
            })
        c.merge(super(HTMLExporter,self).default_config)
        return c

################################################################################

class AddCitationsPreprocessor(Preprocessor):
    """
    An nbconvert.preprocessors.Preprocessor class that adds citations to a
    Jupyter notebook. In the notebook, citations should be indicated with
    `[@bibtex_key]` syntax, where @bibtex_key refers to a BibTeX key to a
    bibliographic entry in a .bib file. This class has the following
    configurable attributes:

        header       - The name of the bibliography section appended to the end
                       of the notebook (default "References")
        bibliography - The name of the BibTeX bibliography file (default
                       "ref.bib")
        csl          - The name of the Citation Style Language file (default
                       "Harvard.csl")
        csl_path     - The list of pathnames to search for CSL files (default
                       ['.', <location-of-this-script>/CSL])
        verbose      - Boolean that determines whether output to stdout is
                       turned on (default False) 

    This preprocessor converts each citation instance with the appropriate text
    for the citation as defined by the CSL file. It also adds two cells to the
    end of the notebook: a header, defaulting to "References", and a list of all
    of the cited references. In addition, any empty cells are removed from the
    notebook.
    """

    header       = Unicode(u'References',
                           help='Header name for the references section',
                           config=True)
    bibliography = Unicode(u'ref.bib',
                           help='Name of the BibTeX bibliography file',
                           config=True)
    csl          = Unicode(u'Harvard.csl',
                           help='Name of the Citation Style Language file',
                           config=True)
    csl_dir      = os.path.normpath(os.path.join(os.path.dirname(
                                    os.path.abspath(__file__)), u'..',
                                    u'shared', u'CSL'))
    csl_path     = List(   [u'.', csl_dir],
                           help='A list of paths to search for CSL files',
                           config=True)
    verbose      = Bool(   False,
                           help='Determines whether to provide output to stdout',
                           config=True)

    ############################################################################

    def _is_cell_empty(self, cell):
        """
        Return True if the given cell is empty
        """
        if cell.cell_type == u'code':
            if cell.source == u'':
                return True
        return False

    ############################################################################

    def _clear_empty_cells(self, nb):
        """
        Remove any empty cells from the given notebook
        """
        new_list = []
        for cell in nb.cells:
            if not self._is_cell_empty(cell):
                new_list.append(cell)
        nb.cells = new_list

    ############################################################################

    def _is_index_in_ranges(self, index, ranges):
        """
        Return True if the given index is within any of the given ranges
        """
        for range in ranges:
            if index >= range[0] and index < range[1]:
                return True
        return False

    ############################################################################

    def _extract_citations(self, nb):
        """
        Return a list of all the citations in the given notebook, in the order
        in which they first appear. Each citation will appear only once
        """
        citations = []
        for cell in nb.cells:
            ranges = []
            source = cell.source
            start = source.find('@',0)
            end = 0
            while start >= 0:
                if start == 0 or source[start-1] in ['[',' ','-']:
                    index = source.rfind('[',end,start)
                    if not (index == -1 or self._is_index_in_ranges(index, ranges)):
                        start = index
                        end = source.find(']',start) + 1
                    else:
                        end1 = source.find(' ', start)
                        end2 = source.find(',', start)
                        end3 = source.find('.', start)
                        if end1 == -1: end1 = len(source)
                        if end2 == -1: end2 = len(source)
                        if end3 == -1: end3 = len(source)
                        end = min(end1, end2, end3)
                    citation = source[start:end]
                    if citation not in citations:
                        citations.append(citation)
                    ranges.append((start,end))
                else:
                    end = start + 1
                start = source.find('@',end)
        return citations

    ############################################################################

    def _find_csl_file(self):
        """
        Given the CSL path (csl_path) and the CSL file name (csl), return the
        full filename of the CSL file.
        """
        for path in self.csl_path:
            candidate = os.path.join(path, self.csl)
            if os.path.isfile(candidate):
                return candidate
        raise IOError('Could not find "%s"' % self.csl)

    ############################################################################

    def _process_citations(self, nb):
        """
        Query the given notebook, and return a dictionary of substitutions and a
        string representing the formatted references in HTML. The substitution
        dictionary consist of keys that represent the citation keys
        ([@bibtex_key]) and values that represent the corresponding citation
        text, formatted according to the preprocessor's CSL file. The
        substitution dictionary returned by this method is suitable as input to
        the _substitute_citations() method, and the references returned by this
        method is suitable as input to the _add_references() method.
        """

        # Initialize the return arguments
        substitutions = {}
        references    = ""

        # Extract and check the number of citations
        citations = self._extract_citations(nb)
        num_citations = len(citations)
        if self.verbose:
            if num_citations== 1:
                print('    1 citation found')
            else:
                print('    %d citations found' % num_citations)
        if num_citations == 0:
            return (substitutions, references)

        # Build a markdown text field with citations only
        body = ""
        for citation in citations:
            body += citation + "\n\n"

        # Run the markdown text through pandoc with the pandoc-citeproc filter
        csl_file = self._find_csl_file()
        if self.verbose:
            print('    Citation Style Language = "%s"' % csl_file         )
            print('    BibTeX reference file   = "%s"' % self.bibliography)
        if not os.path.isfile(self.bibliography):
            raise IOError('Could not find "%s"' % self.bibliography)
        filters = ['pandoc-citeproc']
        extra_args = ['--bibliography="%s"' % self.bibliography,
                      '--csl="%s"' % csl_file]
        body = pypandoc.convert_text(body,
                                     'html',
                                     'md',
                                     filters=filters,
                                     extra_args=extra_args)
        body = body.split('\n')

        # Extract the citation substitutions and the references section from the
        # resulting HTML text
        for i in range(num_citations):
            substitutions[citations[i]] = body[i][26:-11]
        references = "\n<p></p>\n".join(body[num_citations:])
        return (substitutions, references)

    ############################################################################

    def _substitute_citations(self, nb, substitutions):
        """
        Given a substitutions dictionary, as provided by the
        _process_citations() method, substitute the formatted citation text for
        every instance of a citation key found in the notebook.
        """
        keys = list(substitutions.keys())
        # As we loop over the substitution keys, we want to process [@key]
        # before @key, which sorting and reversing will ensure
        keys.sort()
        keys.reverse()
        for cell in nb.cells:
            source = cell.source
            for old in keys:
                new = substitutions[old]
                source = source.replace(old, new)
            cell.source = source

    ############################################################################

    def _add_references(self, nb, references):
        """
        Add a references header cell and a references text cell to the end of
        the notebook. If references is the empty string, do nothing. If a
        references section already exists in the notebook, overwrite the
        existing references text cell.
        """
        if references:
            header_text = u'## ' + self.header
            if nb.cells[-2].source == header_text:
                nb.cells[-1].source = references
            else:
                new_cells = [NotebookNode({u'source': header_text,
                                           u'cell_type': u'markdown',
                                           u'metadata': {}}),
                             NotebookNode({u'source': references,
                                           u'cell_type': u'markdown',
                                           u'metadata': {}})]
                nb.cells.extend(new_cells)

    ############################################################################

    def preprocess(self, nb, resources):
        """
        Preprocess the given notebook by removing all empty cells, substituting
        all citation keys with citation text formatted according to the CSL
        file, and adding a references section to the end of the notebook.
        """
        self._clear_empty_cells(nb)
        (subs, refs) = self._process_citations(nb)
        if refs != "":
            self._substitute_citations(nb, subs)
            self._add_references(nb, refs)
        return (nb, resources)

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

########################################################################

class replace_list(argparse.Action):
    """
    Define an ArgumentParser action that will replace the destination list with
    the given arguments. This should act like the 'store' action, except that the
    given arguments will be a comma-separated list that will replace the
    destination list.
    """

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        """
        Constructor. Call the base class (argparse.Action) constructor.
        """
        argparse.Action.__init__(self, option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Perform the replace action
        """
        setattr(namespace, self.dest, values.split(','))

########################################################################

class append_list(argparse.Action):
    """
    Define an ArgumentParser action that will append the given arguments to a
    destination list. This should act like the 'append' action, except that the
    given arguments will be a comma-separated list that will be appended to the
    end of the list.
    """

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        """
        Constructor. Call the base class (argparse.Action) constructor.
        """
        argparse.Action.__init__(self, option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Perform the append action
        """
        pathlist = getattr(namespace, self.dest)
        setattr(namespace, self.dest, pathlist + values.split(','))

########################################################################

class prepend_list(argparse.Action):
    """
    Define an ArgumentParser action that will prepend the given arguments to a
    destination list. This should act like the append_list Action class, except
    that the given arguments will be a comma-separated list that will be
    inserted into the beginning of the list.
    """

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        """
        Constructor. Call the base class (argparse.Action) constructor.
        """
        argparse.Action.__init__(self, option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Perform the prepend action
        """
        pathlist = getattr(namespace, self.dest)
        setattr(namespace, self.dest, values.split(',') + pathlist)

########################################################################

if __name__ == "__main__":

    # Set up the command-line argument processor
    defaultAddCitation = AddCitationsPreprocessor()
    defaultExecute     = VerboseExecutePreprocessor()
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('files',
                        metavar='FILE',
                        type=str,
                        nargs='*',
                        help='Jupyter notebook filename(s) to be processed')
    parser.add_argument('--kernel',
                        dest='kernel',
                        choices=['python2','python3'],
                        default='python' + python_version_major,
                        help='notebook execution kernel')
    parser.add_argument('-t',
                        '--timeout',
                        dest='timeout',
                        type=int,
                        default=defaultExecute.timeout,
                        help='defines maximum time (in seconds) each notebook cell is allowed to run')
    parser.add_argument('--header',
                        dest='header',
                        type=str,
                        default=defaultAddCitation.header,
                        help='provide the title of the bibliography section')
    parser.add_argument('-b',
                        '--bib',
                        dest='bib',
                        type=str,
                        default=defaultAddCitation.bibliography,
                        help='specify the BibTeX bibliography database')
    parser.add_argument('--csl',
                        dest='csl',
                        type=str,
                        default=defaultAddCitation.csl,
                        help='specify the Citation Style Language file')
    parser.add_argument('--list-csl',
                        dest='list_csl',
                        action='store_true',
                        default=False,
                        help='list the available CSL files and exit')
    parser.add_argument('--list-csl-path',
                        dest='list_csl_path',
                        action='store_true',
                        default=False,
                        help='list the CSL path names and exit')
    parser.add_argument('--replace-csl-path',
                        dest='csl_path',
                        action=replace_list,
                        default=defaultAddCitation.csl_path,
                        help='replace the list of CSL path names')
    parser.add_argument('--prepend-csl-path',
                        dest='csl_path',
                        action=prepend_list,
                        help='prepend a comma-separated list of path names to the CSL path name list')
    parser.add_argument('--append-csl-path',
                        dest='csl_path',
                        action=append_list,
                        help='append a comma-separated list of path names to the CSL path name list')
    parser.add_argument('--debug',
                        dest='debug',
                        action='store_true',
                        default=False,
                        help='provide full stack trace for errors')
    parser.add_argument('-v',
                        '--verbose',
                        dest='verbose',
                        action='store_true',
                        default=False,
                        help='provide verbose output')
    parser.add_argument('-q',
                        '--quiet',
                        dest='verbose',
                        action='store_false',
                        default=False,
                        help='set verbose to False')

    # Parse the command-line arguments
    options = parser.parse_args()

    # Process the options
    if options.list_csl:
        msg = ""
        for path in options.csl_path:
            msg += "CSL files in '%s':\n" % path
            os.chdir(path)
            filenames = glob.glob("*.csl")
            if len(filenames) == 0:
                msg += "    None\n"
            else:
                for filename in filenames:
                    msg += "    %s\n" % filename
        parser.exit(0, msg)
    if options.list_csl_path:
        msg = "List of CSL path names:\n"
        for path in options.csl_path:
            msg += "    %s\n" % path
        parser.exit(0, msg)
    sep = '----------------'
    if options.verbose:
        print(sep)

    # Check for no specified filenames. We allow len(options.files) == 0 up to
    # this point so that we can execute the --list-csl or --list-csl-path
    # options if requested.
    if len(options.files) == 0:
        parser.error("too few arguments")

    # Process the files
    for filename in options.files:
        if options.debug:
            convert(filename, options)
        else:
            try:
                convert(filename, options)
            except Exception as e:
                print("Error: %s" % str(e))
        if options.verbose:
            print(sep)
