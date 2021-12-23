import pandas as pd
import numpy as np
import os
import re
import collections
import matplotlib.pyplot as plt
from PIL import Image
from IIIFpres import iiifpapi3

##
## Functionalities
##
def file_paths(root, x):
    x = [p for p in x if str(p) != 'nan']
    if len(x) == 0:
        return []
    x = [os.path.join(root, str(p)) for p in x]
    return x
    
def add_ext(x):
    for i in range(len(x)):
        if os.path.splitext(x[i])[1] == ".jpg":
            x[i] = x[i]
        else:
            x[i] = "%s.jpg" % str(x[i])
    return x

def ls_image_dim(file):
    w = np.nan
    h = np.nan
    if(os.path.exists(file)):
        try:
            im = Image.open(file)
            w, h = im.size
        except:
            print("An exception occurred %s" % file)
    return {"width": w, "height": h}
    
##
## Functionalities
##    
settings               = {"root": "C:\\Users\\Jan\\Desktop\\Brugse Vrije"}
settings["metadata"]   = os.path.join(settings["root"], 'Brugse Vrije', 'Crimboecken_Brugse_Vrije.xlsx')
settings["folder_img"] = os.path.join(settings["root"], 'Brugse Vrije')
settings["metadata_fields"] = ['SUBJECT NR', 'EEUW', 'SET', 'ARCHIEF', 'INVENTARIS', 'INVENTARISNUMMER', 'STAD-PLATTELAND', 'TAAL', 'DATUM_VERHOOR', 'FAMILIENAAM', 'VOORNAAM', 'ROL ', 'GESLACHT', "PAGINA'S"]

metadata                   = pd.read_excel(settings["metadata"], index_col = None)
settings["columns_images"] = list(metadata.columns)
settings["columns_images"] = list(filter(re.compile("NAAM_IMAGE").match, settings["columns_images"])) 

metadata["files"] = [file_paths(settings["folder_img"], metadata[settings["columns_images"]].iloc[i]) for i in range(len(metadata.index))]
metadata["files"] = [add_ext(p) for p in metadata["files"]]
metadata["label"] = ["Subject %s" %p for p in metadata["SUBJECT NR"]]

## Check if files are there
paths        = [p for getuigenis in metadata["files"] for p in getuigenis]
paths_exists = [os.path.exists(f) for f in paths]
collections.Counter(paths_exists)
np.array(paths)[np.where(np.logical_not(paths_exists))]

## width/height of files
images = pd.DataFrame(
    {"path":        [p for getuigenis in metadata["files"] for p in getuigenis], 
     "metadata_id": [metadata_id for p, metadata_id in zip(metadata["files"], metadata["SUBJECT NR"]) for i in range(len(p))]})
images["resource"]    = [os.path.basename(p) for p in images["path"]]
images["file_exists"] = [os.path.exists(p) for p in images["path"]]
images["width"]       = [ls_image_dim(p)["width"] for p in images["path"]]
images["height"]      = [ls_image_dim(p)["height"] for p in images["path"]]
images                = images[images["file_exists"] == True]

collections.Counter(images["file_exists"])

plt.figure()
n, bins, patches = plt.hist(x=images["width"], bins='auto', color='#607c8e', alpha=0.7, rwidth=0.85)
plt.show()
plt.figure()
n, bins, patches = plt.hist(x=images["height"], bins='auto', color='#607c8e', alpha=0.7, rwidth=0.85)
plt.show()

##################################################################################################
## Build IIIF 
## 
##################################################################################################
images["path_iiif_service"]   = ["https://iiif.datatailor.be/brugse-vrije/images/%s" % str(p) for p in images["resource"]]
images["path_iiif"]           = ["https://iiif.datatailor.be/brugse-vrije/images/%s/full/max/0/default.jpg" % str(p) for p in images["resource"]]
images["path_iiif_thumbnail"] = ["https://iiif.datatailor.be/brugse-vrije/images/%s/full/80,100/0/default.jpg" % str(p) for p in images["resource"]]

#Voorbeeld in versie 2 formaat
#https://iiif.ghentcdh.ugent.be/iiif/collections/getuigenissen:brugse_vrije 
#https://iiif.ghentcdh.ugent.be/iiif/manifests/getuigenissen:brugse_vrije:RABrugge_I15_16999_V01 aanmaken

#https://iiif.datatailor.be/voorbeeld/example.png/10,40,100,30/max/0/default.png
#https://iiif.datatailor.be/brugse-vrije/images/513_0592_000_17026_000_0_0138.jpg/10,40,100,30/max/0/default.png
#https://iiif.datatailor.be/brugse-vrije/images/RABrugge_I15_16999_V10_01.jpg/!160,200/max/0/default.png

metadata
i = 0
idx = i + 1

img = images[images['metadata_id'].isin([idx])]
img = img.copy(deep=True)
img["label"] = ["Page %s" % str(page_nr + 1) for page_nr in range(len(img['path']))]

iiifpapi3.BASE_URL = "https://iiif.datatailor.be/brugse-vrije/manifests/subject-%s/" % str(idx).zfill(4)
manifest = iiifpapi3.Manifest()
manifest.set_id(extendbase_url = "manifest.json")
manifest.add_label(language = "nl", text = metadata["label"][i])
manifest.add_behavior(behavior = "paged")
thumb = manifest.add_thumbnail()
thumb.set_id(img['path_iiif_thumbnail'][0])
s = thumb.add_service()
s.set_id(img["path_iiif_service"][0])
s.set_type("ImageService3")
for feat in settings["metadata_fields"]:
    if(not(metadata[feat][i] == None)):
        manifest.add_metadata(label = feat, value = str(metadata[feat][i]))


for page_idx in range(len(img["path_iiif"])):
#for page_idx in range(2):
    page_nr = page_idx + 1
    ## Canvas (one image)
    canvas = manifest.add_canvas_to_items()
    canvas.set_id(extendbase_url = "canvas/page-%s" % page_nr) # in this case we use the base url
    thumb = canvas.add_thumbnail()
    thumb.set_id(img['path_iiif_thumbnail'][page_idx])
    canvas.set_height(height = img["height"][page_idx])
    canvas.set_width(width = img["width"][page_idx])
    canvas.add_label(language = "nl", text = img["label"][page_idx])
    annopage = canvas.add_annotationpage_to_items()
    annopage.set_id(extendbase_url="page/page-%s/1" %page_nr)
    annotation = annopage.add_annotation_to_items(target = canvas.id)
    annotation.set_id(extendbase_url = "annotation/p%s-image" % str(page_nr).zfill(4))
    annotation.set_motivation("painting")
    annotation.body.set_id(img["path_iiif"][page_idx])
    annotation.body.set_type("Image")
    annotation.body.set_format("image/jpeg")
    annotation.body.set_width(img["width"][page_idx])
    annotation.body.set_height(img["height"][page_idx])
    s = annotation.body.add_service()
    s.set_id(img["path_iiif_service"][page_idx])
    s.set_type("ImageService3")
    s.set_profile("level1")
    
manifest.json_save("manifest.json")

manifest.inspect()
manifest.show_errors_in_browser()

#https://uv-v4.netlify.app/#?manifest=https://raw.githubusercontent.com/DIGI-VUB/IIIF/master/brugse-vrije/dev/manifest.json
    
