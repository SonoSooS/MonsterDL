from util.modelstruct import dataclass, field


#region CF Manifest

@dataclass
class CFMod:
    projectID: int
    fileID: int
    required: bool = True

@dataclass
class CFModLoader:
    id: str
    primary: bool = True

@dataclass
class CFMinecraft:
    version: str
    modLoaders: 'list[CFModLoader]' = field(default_factory=list) # type: ignore

@dataclass
class CFManifest:
    minecraft: CFMinecraft = field(default_factory=CFMinecraft) # type: ignore
    name: str
    author: str
    version: str
    files: 'list[CFMod]' = field(default_factory=list) # type: ignore
    
    manifestType: str = "minecraftModpack"
    manifestVersion: int = 1
    overrides: str = "overrides"

#endregion

#region CH Generic

@dataclass
class CHVersionTarget:
    id: int
    version: str
    name: str
    type: str
    
    updated: 'int|None' = None

#endregion

#region CH /<id>/<version>

@dataclass
class CHCFDescriptor:
    project: int
    file: int

@dataclass
class CHVersionMetadataFile:
    id: int
    name: str
    type: str
    
    path: str
    url: str
    size: int
    sha1: str
    updated: int 
    
    clientonly: bool = False
    serveronly: bool = False
    optional: bool = False
    
    curseforge: 'CHCFDescriptor|None' = None

@dataclass
class CHVersionMetadata:
    files: 'list[CHVersionMetadataFile]'
    targets: 'list[CHVersionTarget]'

#endregion

#region CH /<id>

@dataclass
class CHModpackMetaVersion:
    id: int
    name: str
    type: str
    updated: int
    private: bool
    targets: 'list[CHVersionTarget]'
    
@dataclass
class CHModpackMeta:
    id: int
    name: str
    provider: str
    versions: 'list[CHModpackMetaVersion]'

#endregion
