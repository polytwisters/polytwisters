from . import common
from . import soft_polytwisters
from . import hard_polytwisters


def get_polytwister(name):
    normalized_name = common.normalize_polytwister_name(name)
    all_polytwisters = {}
    all_polytwisters.update(soft_polytwisters.get_all_soft_polytwisters())
    all_polytwisters.update(hard_polytwisters.get_all_hard_polytwisters())
    return all_polytwisters[normalized_name]
