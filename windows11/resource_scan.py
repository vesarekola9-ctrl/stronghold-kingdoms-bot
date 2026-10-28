"""Load real color PNG templates from windows11/resources and find candidates in screenshots."""
from pathlib import Path
import cv2

RESOURCE_DIR=Path(__file__).resolve().parent/'resources'

def load_templates():
    result={}
    for path in sorted(RESOURCE_DIR.glob('*.png')):
        image=cv2.imread(str(path),cv2.IMREAD_COLOR)
        if image is not None and image.size:result[path.stem]=image
    return result

def detect(image,threshold=.84):
    found=[]
    for name,template in load_templates().items():
        h,w=template.shape[:2]
        if h>image.shape[0] or w>image.shape[1]:continue
        scores=cv2.matchTemplate(image,template,cv2.TM_CCOEFF_NORMED)
        for _ in range(80):
            _,score,_,pos=cv2.minMaxLoc(scores)
            if score<threshold:break
            x,y=pos
            found.append((name,x+w//2,y+h//2,round(score,3)))
            cv2.rectangle(scores,(max(0,x-w//2),max(0,y-h//2)),(min(scores.shape[1]-1,x+w//2),min(scores.shape[0]-1,y+h//2)),-1,-1)
    return found
