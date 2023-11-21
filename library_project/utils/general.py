def keys_values_to_dict(keys:list|tuple, values:list|tuple) ->dict:
    if len(keys) != len(values):
        raise ValueError("Length of keys must be the same as values")
    ret = {}
    for k, v in zip(keys, values):
        ret[k] = v

    return ret