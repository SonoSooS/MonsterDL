import os
from pathlib import Path
import json

from util.prettyprint import pp_print as pp, pp as pp_format
from util.json_to_dataclass import parse as json_to_obj, add_module
from util.modelstruct import pydefault

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

FILEPATH = "C:\\Downloads\\"

def main():
    #with open(FILEPATH + "api_119.json", 'r') as fi:
    with open(FILEPATH + "api_119_11441.json", 'r') as fi:
    #with open(FILEPATH + "api_119_11441_mods.json", 'r') as fi:
        data = json.load(fi)
    
    #pp(data, 4)
    
    #smeta: model.CHModpackMeta = json_to_obj(data, model.CHModpackMeta) # type: ignore
    sver: model.CHVersionMetadata = json_to_obj(data, model.CHVersionMetadata) # type: ignore
    
    #pp(smeta, 4)
    #pp(sver, 4)
    
    print("Parsing...")
    
    res = model.CFManifest()
    
    #TODO: parse /id  JSON too, not just /id/version
    res.name = "Modpack Converter example modpack"
    res.version = "1.0.0"
    res.author = "Modpack Converter"
    
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
    
    #pp(to_download, 4)
    
    if False:
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
