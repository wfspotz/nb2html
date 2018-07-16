
# Module imports
import nbconvert
HTMLExporter = nbconvert.HTMLExporter

# Object imports
from traitlets.config import Config

################################################################################

class AddCitationsExporter(HTMLExporter):
    """
    Add the AddCitationsPreprocessor class to the Preprocessor configuration.
    """
    @property
    def default_config(self):
        cfg = Config({
                      'AddCitationsPreprocessor': {'enabled':True}
                      })
        cfg.merge(super(HTMLExporter,self).default_config)
        return cfg
