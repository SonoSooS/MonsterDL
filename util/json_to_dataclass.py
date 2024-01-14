# type: ignore

from .modelstruct import fields as dataclass_fields, MISSING, is_dataclass

__BASICTYPES = (int, str, float, bool, list, dict, set, tuple, object)
__conversion_cache: 'dict[type, Any]' = dict()


def get_sanitized_converter(name: str):
    conv = __conversion_cache.get(name)
    if conv is not None:
        return conv
    
    sanitized = name
    innertypes = None
    idx = name.find('[')
    if idx > 0:
        sanitized = name[0:idx]
        assert name[-1] == ']'
        
        innertype = name[idx+1:-1]
        #TODO: hell
        assert '[' not in innertype, 'Recursive generics not supported yet'
        innertypes = [make_converter(t.strip()) for t in innertype.split(',')]
    
    found = None
    for k in __conversion_cache:
        if isinstance(k, str):
            kname = k
        else:
            kname = k.__name__
            
        if kname != sanitized:
            continue
        
        if found is not None:
            raise ValueError("Duplicate entry for '%s' ('%s' is colliding with '%s')" % (name, repr(found), repr(k)))
        
        found = __conversion_cache.get(k)
    
    if not found:
        raise KeyError(name)
    
    if sanitized in {'set', 'list'}:
        assert len(innertypes) == 1, "Invalid collection generics"
        
        innertype = innertypes[0]
        assert innertype, "what the fuck %s" % name
        def conv(jsonobj):
            if jsonobj is None:
                return None
            
            return found(innertype(x) for x in jsonobj)
    elif innertypes:
        if len(innertypes) == 1:
            innertype = innertypes[0]
            
            def conv(jsonobj):
                return found(innertype(jsonobj))
        else:
            assert False, "What the fuck"
            def conv(jsonobj):
                return found(*(v(k) for k,v in zip(jsonobj, innertypes)))
    else:
        conv = found
    
    
    __conversion_cache[name] = conv
    return conv

def make_converter(cls: type):
    conv = __conversion_cache.get(cls)
    if conv is None:
        if cls == 'None':
            def conv(jsonobj):
                raise NotImplementedError("Can't convert to None")
        elif cls in __BASICTYPES:
            def conv(jsonobj):
                try:
                    return cls(jsonobj)
                except:
                    return jsonobj
        elif isinstance(cls, str):
            classes = [get_sanitized_converter(x.strip()) for x in cls.split('|')]
            if not all(classes):
                raise KeyError(cls)
            
            if len(classes) == 1:
                conv = classes[0]
            else:
                def conv(jsonobj):
                    for ctr in classes:
                        try:
                            return ctr(jsonobj)
                        except:
                            pass
                    
                    raise ValueError("Failed to construct type '%s' due to invalid JSON input" % cls)
        else:
            convfields = dataclass_fields(cls)
            
            converters: 'dict[str, Any]' = dict()
            
            for field in convfields:
                converters[field.name] = make_converter(field.type)
            
            def conv(jsonobj: dict):
                ret = cls()
                
                for k, v in converters.items():
                    val = jsonobj.get(k, MISSING)
                    if val is not MISSING:
                        setattr(ret, k, v(val))
                
                return ret
        
        __conversion_cache[cls] = conv
    
    return conv

def add_class(cls):
    make_converter(cls)

def add_module(module):
    types = []
    
    for k in dir(module):
        if k.startswith('_'):
            continue
        
        v = getattr(module, k)
        if isinstance(v, type) and is_dataclass(v):
            types.append(v)
    
    prev_len = len(types)
    last_e = None
    while prev_len:
        for i in range(prev_len):
            try:
                add_class(types[i])
                types.pop(i)
                break
            except Exception as e:
                last_e = e
                continue
        
        newlen = len(types)
        if newlen != prev_len:
            prev_len = newlen
            last_e = None
            continue
        
        raise Exception('Unresolved dependency: %s (%s)' % (repr(types), repr(last_e)))

def parse(jsonobj: dict, cls: type):
    return (make_converter(cls))(jsonobj)


for k in __BASICTYPES:
    add_class(k)
add_class('None')
