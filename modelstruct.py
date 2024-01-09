# type: ignore

from inspect import currentframe

MISSING = object()
CTOR = object()

__KEY_NAME = '__dcls_fields__'

class Field:
    __slots__ = ('name', 'type', 'default', 'default_factory')
    
    name: str
    type: type
    default: 'None|object'
    default_factory: 'None|Any|type'
    
    def __init__(self):
        self.default = MISSING
        self.default_factory = MISSING
    
    def __repr__(self):
        default = self.default
        factory = self.default_factory
        
        extrastr = ''
        
        if default is not MISSING:
            extrastr += ", default=%s" % repr(default)
        if factory is not MISSING:
            extrastr += ', factory=%s' % repr(factory)
        
        
        
        return 'Field(%s: %s%s)' % (self.name, self.type, extrastr)
    
    def get_default(self):
        if self.default is not MISSING:
            return self.default
        elif self.default_factory is not MISSING:
            return self.default_factory()
        
        return None

def dataclass(cls):
    clsdict: dict = cls.__dict__
    clsname: str = cls.__name__
    
    anns: dict[str, 'type|str'] = clsdict['__annotations__']
    
    fields: list[Field] = []
    
    for ann, annv in anns.items():
        field = Field()
        field.name = ann
        field.type = annv
        
        defaultval = clsdict.get(ann, MISSING)
        if defaultval is not MISSING:
            if isinstance(defaultval, Field):
                field.default = defaultval.default
                field.default_factory = defaultval.default_factory
            elif defaultval is CTOR:
                if isinstance(field.type, str):
                    fieldtype: str = field.type
                    
                    assert fieldtype.startswith('list[') and fieldtype.endswith(']'), 'Currently only list type str is supported'
                    
                    field.default_factory = list
                else:
                    field.default_factory = field.type
            else:
                field.default = defaultval
        
        fields.append(field)
    
    if '__init__' not in clsdict:
        def initializer(self, dct: dict = None, **kwargs):
            for field in fields:
                fieldname = field.name
                
                val = MISSING
                if dct is not None:
                    val = dct.get(fieldname, MISSING)
                
                if val is MISSING:
                    val = kwargs.get(fieldname, MISSING)
                    
                    if val is MISSING:
                        val = field.get_default()
                
                setattr(self, fieldname, val)
        
        initializer.__name__ = '__init__'
        setattr(cls, '__init__', initializer)
    
    if '__repr__' not in clsdict:
        def represent(self):
            return '%s(%s)' % (clsname, ', '.join('%s=%s' % (kn, repr(getattr(self, kn))) for kn in anns))
        
        represent.__name__ = '__repr__'
        setattr(cls, '__repr__', represent)
    
    setattr(cls, __KEY_NAME, tuple(fields))
    return cls

def field(*, default=MISSING, default_factory=MISSING) -> Field:
    f = Field()
    f.default = default
    f.default_factory = default_factory
    return f

def fields(cls) -> 'list[Field]':
    return getattr(cls, __KEY_NAME)

def is_dataclass(cls) -> bool:
    return hasattr(cls, __KEY_NAME)

def pydefault(obj):
    return obj.__dict__
