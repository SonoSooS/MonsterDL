import os
from pathlib import Path
import json

from util.prettyprint import pp_print as pp, pp as pp_format
from util.json_to_dataclass import parse as json_to_obj, add_module
from util.modelstruct import pydefault
from util.webparser import WebJSONExtractor

import zipfile
import glob

import requests
try:
    from progress.bar import Bar as ProgressBar # type: ignore
except:
    try:
        from pip._vendor.progress.bar import Bar as ProgressBar # type: ignore
    except:
        from pip._vendor.rich.progress import Bar as ProgressBar # type: ignore


import model
add_module(model)

FILEPATH = "local/"

def parse_website_recursive(obj):
    if not isinstance(obj, dict):
        return None
    
    if 'provider' in obj:
        return obj
    
    for v in obj.values():
        ret = parse_website_recursive(v)
        if ret is not None:
            return ret
    
    return None

def parse_website(content):
    extractor = WebJSONExtractor()
    extractor.feed(content)
    assert extractor.content is not None
    data = extractor.content or None
    
    if data is None:
        return None
    
    data = json.loads(data)
    return parse_website_recursive(data)

def download_pack_meta(url: 'str|None'):
    if url:
        with requests.get(url) as req:
            req.raise_for_status()
            if not req.encoding:
                req.encoding = 'utf-8'
            ctype = req.headers['Content-Type']
            data = req.text
            
            if ctype == "application/json":
                data = json.loads(data)
            elif ctype.startswith("text/html"):
                data = parse_website(data)
            else:
                raise ValueError("Webpage provided is invalid (modpack platform not supported?)")
    else:
        with open(FILEPATH + "pack.html", 'r', encoding='utf-8') as fi:
            data = fi.read()
        
        data = parse_website(data)
    
    if data is None:
        with open(FILEPATH + "api_119.json", 'r') as fi:
        #with open(FILEPATH + "api_119_11441.json", 'r') as fi:
        #with open(FILEPATH + "api_119_11441_mods.json", 'r') as fi:
            data = json.load(fi)
    
    return data

def build_pack_version_url(provider: str, pack: int, version: int):
    #return 'file://./local/api_%u_%u.json' % (pack, version)
    
    if not provider.startswith("api."):
        provider = 'api.' + provider
    
    return 'https://%s/public/modpack/%u/%u' % (provider, pack, version)

def download_pack_version(url: str):
    with requests.get(url) as req:
        req.raise_for_status()
        if not req.encoding:
            req.encoding = 'utf-8'
        data = req.text
        data = json.loads(data)
    
    return data


def main():
    print("Enter *full* website URL to download modpack from")
    print("(URL should look like https://<website>/modpacks/<modpack name>)")
    url = input('> ')
    
    data = download_pack_meta(url)
    smeta: model.CHModpackMeta = json_to_obj(data, model.CHModpackMeta) # type: ignore
    
    #TODO: version picker UI
    max_verion = max(smeta.versions, default=None, key=lambda x:x.id)
    assert max_verion is not None
    
    version_url = build_pack_version_url(smeta.provider, smeta.id, max_verion.id)
    data = download_pack_version(version_url)
    sver: model.CHVersionMetadata = json_to_obj(data, model.CHVersionMetadata) # type: ignore
    
    print("Parsing...")
    
    res = model.CFManifest()
    
    #TODO: parse /id  JSON too, not just /id/version
    res.name = "Modpack Converter example modpack"
    res.version = "1.0.0"
    res.author = "Modpack Converter"
    
    if smeta:
        res.name = smeta.name
        res.version = max_verion.name
        #HACK: no author field, not sure what to put there
    
    #FIXME: security issue, sanitize paths and stuff
    
    for target in sver.targets:
        if target.type == 'game':
            assert target.name == 'minecraft'
            assert not res.minecraft.version
            res.minecraft.version = target.version
        elif target.type == 'modloader':
            ml = model.CFModLoader()
            ml.primary = not res.minecraft.modLoaders
            ml.id = "%s-%s" % (target.name, target.version) # best guess
            res.minecraft.modLoaders.append(ml)
    
    to_download: dict[str, str] = dict()
    
    #TODO: do not hardcode paths
    
    for file in sver.files:
        if file.serveronly:
            continue
        
        if file.curseforge:
            assert file.type == 'mod', "Only mods can be downloaded via CF (%s)" % pp_format(file, 0)
            
            cfmod = model.CFMod(projectID=file.curseforge.project, fileID=file.curseforge.file, required= not file.optional) # type: ignore
            res.files.append(cfmod)
        else:
            assert file.url, "File that can not be downloaded (%s)" % (pp_format(file, 0))
            folder = '%s/%s' % ('out/overrides', file.path)
            os.makedirs(folder, exist_ok=True)
            path = '%s/%s' % (folder, file.name)
            to_download[path] = file.url
    
    print("Writing manifest...")
    
    with open('out/manifest.json', 'w') as fo:
        json.dump(res, fo, ensure_ascii=False, default=pydefault, indent=4)
    
    print("TODO: download files")
    
    if True:
        with requests.Session() as sess:
            i = 0
            ni = len(to_download)
            for target, url in to_download.items():
                i += 1
                with open(target, 'wb') as fo:
                    with sess.get(url, stream=True) as req:
                        req.raise_for_status()
                        clen = 0
                        try:
                            clen_str = req.headers['Content-Length']
                            clen = int(clen_str, 10)
                        except:
                            pass
                        
                        with ProgressBar(message="Downloading %4u/%4u" % (i, ni), suffix='[%(elapsed_td)s / %(eta_td)s] %(max)d <-- %(index)d', max=clen) as progress:
                            
                            for chunk in req.iter_content(None):
                                fo.write(chunk)
                                progress.next(len(chunk))
    else:
        #pp(to_download, 4)
        pass
    
    
    print("Compressing...")
    
    with zipfile.ZipFile('out/out.zip', 'w', allowZip64=False) as zip:
        outfiles = glob.iglob('out/**', recursive=True)
        for file in outfiles:
            p = Path(file)
            print(p)
            if file.endswith('out.zip'):
                continue
            if not p.is_file():
                continue
            
            fn = file[4:]
            with zip.open(fn, 'w') as fo:
                with open(file, 'rb') as fi:
                    while True:
                        buf = fi.read(1024)
                        if not buf:
                            break
                        fo.write(buf)
            
    

if __name__ == '__main__':
    main()
