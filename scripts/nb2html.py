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
import os
import sys

################################################################################

# NBREF import
import nbref

################################################################################

# Aliases and global variables
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
    defaultAddCitation = nbref.AddCitationsPreprocessor()
    defaultExecute     = nbref.VerboseExecutePreprocessor()
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
            nbref.convert(filename, options)
        else:
            try:
                nbref.convert(filename, options)
            except Exception as e:
                print("Error: %s" % str(e))
        if options.verbose:
            print(sep)
