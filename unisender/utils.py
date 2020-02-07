import hashlib


def get_string_repr(obj) -> str:

    """
    Combines all object data into one string

    :param obj: list|dict|str, given obj
    :return: str, obj string representation
    """

    result = ''
    if isinstance(obj, list):
        for elem in obj:
            result += get_string_repr(elem)
    elif isinstance(obj, dict):
        for elem in obj.values():
            result += get_string_repr(elem)
    else:
        try:
            result += str(obj)
        except:
            pass
    return result


def get_unique_hash(obj) -> int:

    """
    Create unique id of obj

    :param obj: list|dict|str, given obj
    :return: int
    """

    hash_string = get_string_repr(obj).encode('utf-8')
    return int(hashlib.sha1(hash_string).hexdigest(), 16) % 10 ** 10


def to_camel_case(snake_case_str: str) -> str:

    """ Convert snake_case_str to camelCaseStr """

    parts = snake_case_str.split('_')
    return parts[0] + ''.join(w.capitalize() or '_' for w in parts[1:])
