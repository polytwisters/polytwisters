from . import common
from . import soft_polytwisters
from . import hard_polytwisters


def get_all_polytwisters():
    normalized_name = common.normalize_polytwister_name(name)
    result = {}
    result.update(soft_polytwisters.get_all_soft_polytwisters())
    result.update(hard_polytwisters.get_all_hard_polytwisters())
    return result[normalized_name]


def get_polytwister(name):
    return all_polytwisters()[name]