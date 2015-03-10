from bw2data import mapping, Database, databases
from ..utils import activity_hash
from ..errors import StrategyError


def link_iterable_by_fields(unlinked, other=None, fields=None, kind=None,
                            internal=False, relink=False):
    """Generic function to link objects in ``unlinked`` to objects in ``other`` using fields ``fields``.

    The database to be linked must have uniqueness for each object for the given ``fields``.

    If ``kind``, limit objects in ``unlinked`` of type ``kind``.

    If ``relink``, link to objects which already have an ``input``. Otherwise, skip already linked objects.

    If ``internal``, linked ``unlinked`` to other objects in ``unlinked``. Each object must have the attributes ``database`` and ``code``."""
    if kind:
        kind = {kind} if isinstance(kind, basestring) else kind
        if relink:
            filter_func = lambda x: x.get('type') in kind
        else:
            filter_func = lambda x: x.get('type') in kind and not x.get('input')
    else:
        if relink:
            filter_func = lambda x: True
        else:
            filter_func = lambda x: not x.get('input')

    if internal:
        other = unlinked

    # Perhaps slightly convoluted, but other can be a generator
    try:
        candidates_list = [
            (activity_hash(ds, fields), (ds['database'], ds['code']))
            for ds in other
        ]
    except KeyError:
        raise StrategyError(u"Not all datasets in database to be linked have "
                            u"``database`` or ``code`` attributes")

    candidates = dict(candidates_list)

    if len(candidates) != len(candidates_list):
        raise StrategyError(u"Not each object in database to be linked is "
                            u"unique with given fields")

    for container in unlinked:
        for obj in filter(filter_func, container.get('exchanges', [])):
            try:
                obj[u'input'] = candidates[activity_hash(obj, fields)]
            except KeyError:
                pass
    return unlinked


def assign_only_product_as_production(db):
    """Assign only product as reference product"""
    for ds in db:
        if ds.get("reference product"):
            continue
        if len(ds['products']) == 1:
            ds[u'name'] = ds['products'][0]['name']
            ds[u'unit'] = ds['products'][0]['unit']
            ds[u'production amount'] = ds['products'][0]['amount']
    return db


def link_technosphere_by_activity_hash(db, external_db_name=None, fields=None):
    """Link technosphere exchanges using ``activity_hash`` function.

    If ``external_db_name``, link against a different database; otherwise link internally.

    If ``fields``, link using only certain fields."""
    TECHNOSPHERE_TYPES = {u"technosphere", u"substitution", u"production"}
    if external_db_name is not None:
        if external_db_name not in databases:
            raise StrategyError(u"Can't find external database {}".format(
                                external_db_name))
        # TODO: Also link to products?
        other = (obj for obj in Database(external_db_name)
                 if obj.get('type', 'process') == 'process')
        internal = False
    else:
        other = None
        internal = True
    return link_iterable_by_fields(db, other, internal=internal, kind=TECHNOSPHERE_TYPES, fields=fields)


def set_code_by_activity_hash(db):
    """Use ``activity_hash`` to set dataset code"""
    for ds in db:
        ds[u'code'] = activity_hash(ds)
    return db


def assign_only_production_with_amount_as_reference_product(db):
    """If a multioutput process has one product with a non-zero amount, assign that product as reference product"""
    for ds in db:
        amounted = [prod for prod in ds['products'] if prod['amount']]
        if len(amounted) == 1:
            ds[u'name'] = ds[u'reference product'] = amounted[0]['name']
            ds[u'unit'] = amounted[0]['unit']
            ds[u'production amount'] = amounted[0]['amount']
    return db
