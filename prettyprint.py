from modelstruct import fields as dataclass_fields, is_dataclass

__SENTINEL = object()

def __all_except_last(obj, most, last):
    prev = __SENTINEL
    for v in obj:
        if prev is not __SENTINEL:
            yield most(prev)
        prev = v
    
    if prev is not __SENTINEL:
        yield last(prev)

def __all_except_first(obj, first, others):
    i = iter(obj)
    
    for v in i:
        yield first(v)
        break
    
    for v in i:
        yield others(v)

def __format_list(obj, indent):
    comma = ',' if indent else ', '
    
    for xx in __all_except_last\
    (
        obj,
        lambda x: __all_except_last(__format_recursive(x, indent), lambda y: y, lambda y: y + comma),
        lambda x: __format_recursive(x, indent)
    ):
        yield from xx

def __format_dict_sub(name, obj, indent):
    i = __format_recursive(obj, indent)
    
    skip_newline = False
    if isinstance(obj, (list, set, dict)):
        skip_newline = True
    
    firstline = None
    for v in i:
        firstline = v
        break
    
    for v in i:
        if skip_newline:
            yield name + (": " if not indent else ':')
            yield firstline
        else:
            yield name + ": " + firstline
        yield v
        yield from i
        return
    
    if firstline is not None:
        yield name + ": " + firstline
        return
    
    yield name + ": <error>"

def __format_dict(obj, indent):
    comma = ',' if indent else ', '
    
    for xx in __all_except_last\
    (
        obj,
        lambda i: __all_except_last(__format_dict_sub(repr(i[0]), i[1], indent), lambda y: y, lambda y: y + comma),
        lambda i: __format_dict_sub(repr(i[0]), i[1], indent),
    ):
        yield from xx

def __format_recursive(obj, indent):
    istr = ' ' * indent
    
    if isinstance(obj, list):
        lobj: list = obj # type: ignore
        if not lobj:
            yield '[]'
            return
        
        yield '['
        yield from (istr + x for x in __format_list(lobj, indent))
        yield ']'
    elif isinstance(obj, set):
        lobj: set = obj # type: ignore
        if not lobj:
            yield '{}'
            return
        
        yield '{'
        yield from (istr + x for x in __format_list(lobj, indent))
        yield '}'
    elif isinstance(obj, tuple):
        lobj: tuple = obj # type: ignore
        if not lobj:
            yield '()'
            return
        
        yield '(' + ', '.join(__format_recursive(x, indent) for x in lobj) + ')'
    elif isinstance(obj, dict):
        lobj: dict = obj # type: ignore
        if not lobj:
            yield '{}'
            return
        
        yield '{'
        yield from (istr + x for x in __format_dict(lobj.items(), indent))
        yield '}'
    elif is_dataclass(obj):
        lobj = obj # type: ignore
        
        yield type(lobj).__name__
        yield '('
        yield from (istr + x for x in __format_dict(((field.name, getattr(lobj, field.name)) for field in dataclass_fields(lobj)), indent))
        yield ')'
    else:
        yield repr(obj)

def pp(obj, indent=4):
    return ('\n' if indent else '').join(__format_recursive(obj, indent))

def pp_print(obj, indent=4):
    pps = pp(obj, indent)
    print(pps)
    return pps
