import numpy as np,sys,glob,os
from PIL import Image,ImageDraw
from feat import *
ch=sys.argv[1]
if ch=='Ocean':
    F=np.array(Image.open('pr1/L/face_final.png'));H=np.array(Image.open('pr1/L/hair_final.png'))
    blank=np.array(Image.open('ocean_blank_white.png').convert('RGB'))
    gens={'grimace-0':'36e2f89e','grimace-1':'0791179c','grimace-2':'6e6c1443','grimace-3':'9c123895','grimace-4':'fc3feb8d','ocean-hammer-1':'160ecb37','ocean-hammer-2':'8a8a43c2','ocean-hammer-3':'af1a54d0','ocean-hammer-4':'e5d225fe'}
    od='oc_feat'
else:
    F=np.array(Image.open('sk/face_final.png'));H=np.array(Image.open('sk/hair_final.png'))
    blank=np.array(Image.open('sk/blank_white.png').convert('RGB'))
    gens={'default':'d131cb23','hammer-0':'645e0274','hammer-1':'0840f3f0','hammer-2':'3364184e','hammer-3':'4c0d7871','hammer-4':'94ea7683','soft-0':'a4a41cc6','soft-1':'fcd1c46b','soft-2':'5c616910','soft-3':'eac0ac0f'}
    od='sk_feat'
only=sys.argv[2:] 
os.makedirs(od,exist_ok=True);tiles=[]
for k,v in gens.items():
    if only and k not in only: 
        out=np.array(Image.open(f'{od}/features-{k}.png'))
    else:
        p=glob.glob(A+v+'*')[0]
        out,al=extract(p,blank,F[...,3]>0,H[...,3]>0); out=postproc2(postproc(out))
        Image.fromarray(out).save(f'{od}/features-{k}.png');print(k,al,(out[...,3]>0).sum())
    ys,xs=np.where(F[...,3]>0);cx=(xs.min()+xs.max())//2;cy=int(ys.max()-0.33*(ys.max()-ys.min()))
    box=(cx-220,cy-170,cx+220,cy+130)
    c=Image.new('RGBA',(1024,1024),(255,255,255,255))
    for L in (F,out,H): c.alpha_composite(Image.fromarray(L))
    fo=Image.new('RGBA',(1024,1024),(200,230,255,255));fo.alpha_composite(Image.fromarray(out))
    tiles.append((k,fo.crop(box),c.crop(box)))
S=Image.new('RGB',(880*3,330*((len(tiles)+2)//3)),'white');d=ImageDraw.Draw(S)
for i,(k,a,b) in enumerate(tiles):
    x,y=(i%3)*880,(i//3)*330;S.paste(a.convert('RGB'),(x,y+25));S.paste(b.convert('RGB'),(x+440,y+25));d.text((x+5,y+5),k,fill='black')
S.save(f'{od}_check.png')
