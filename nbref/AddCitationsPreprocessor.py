
################################################################################

# Module imports
import nbconvert
import nbformat
import os
import pypandoc

################################################################################
# Aliases and global variables
Preprocessor = nbconvert.preprocessors.Preprocessor
NotebookNode = nbformat.notebooknode.NotebookNode

################################################################################

# Object imports
from traitlets        import Bool
from traitlets        import List
from traitlets        import Unicode
from traitlets.config import Config

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
