from . import common
from . import soft_polytwisters
from . import hard_polytwisters


def get_all_polytwisters():
    result = {}
    result.update(soft_polytwisters.get_all_soft_polytwisters())
    result.update(hard_polytwisters.get_all_hard_polytwisters())
    return result


def get_polytwister(name):
    return get_all_polytwisters()[name]