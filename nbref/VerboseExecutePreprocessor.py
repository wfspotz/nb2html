
# Module imports
import nbconvert
ExecutePreprocessor = nbconvert.preprocessors.ExecutePreprocessor

# Object imports
from traitlets import Bool

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
