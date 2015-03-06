from bw2data import Database
from .base_lci import LCIImporter
from ..extractors import Ecospold1DataExtractor
from ..strategies import (
    assign_only_product_as_production,
    clean_integer_codes,
    drop_unspecified_subcategories,
    es1_allocate_multioutput,
    link_technosphere_by_activity_hash,
    link_iterable_by_fields,
    normalize_biosphere_categories,
    normalize_biosphere_names,
    set_code_by_activity_hash,
    strip_biosphere_exc_locations,
)
from bw2data import config
from time import time
import functools


class SingleOutputEcospold1Importer(LCIImporter):
    """Import and process single-output datasets in the ecospold 1 format.

    Applies the following strategies:
    #. If only one exchange is a production exchange, that is the reference product
    #. Delete (unreliable) integer codes from extracted data
    #. Drop ``unspecified`` subcategories from biosphere flows
    #. Normalize biosphere flow categories to ecoinvent 3.1 standard
    #. Normalize biosphere flow names to ecoinvent 3.1 standard
    #. Remove locations from biosphere exchanges
    #. Create a ``code`` from the activity hash of the dataset
    #. Link biosphere exchanges to the default biosphere database
    #. Link internal technosphere exchanges

    Args:
        * *filepath*: Either a file or directory.
        * *db_name*: Name of database to create.

    """
    strategies = [
        assign_only_product_as_production,
        clean_integer_codes,
        drop_unspecified_subcategories,
        normalize_biosphere_categories,
        normalize_biosphere_names,
        strip_biosphere_exc_locations,
        set_code_by_activity_hash,
        functools.partial(link_iterable_by_fields,
            other=Database(config.biosphere),
            kind='biosphere'
        ),
        link_technosphere_by_activity_hash,
    ]
    format = u"Ecospold1"

    def __init__(self, filepath, db_name):
        self.db_name = db_name
        start = time()
        self.data = Ecospold1DataExtractor.extract(filepath, db_name)
        print(u"Extracted {} datasets in {:.2f} seconds".format(
              len(self.data), time() - start))


class MultiOutputEcospold1Importer(SingleOutputEcospold1Importer):
    """Import and process mutli-output datasets in the ecospold 1 format.

    Works the same as the single-output importer, but first allocates multioutput datasets."""
    def __init__(self, *args, **kwargs):
        self.strategies.insert(0, es1_allocate_multioutput)
        super(MultiOutputEcospold1Importer, self).__init__(*args, **kwargs)