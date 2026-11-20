import numpy as np, glob, os, json
from PIL import Image
from scipy import ndimage as nd
rep={}
for ch in ['Ocean','Seeky']:
    od=f'layers_out/{ch}'
    F=np.array(Image.open(f'{od}/face-default.png'));fa=F[...,3]>0
    for f in sorted(glob.glob(f'{od}/*.png')):
        a=np.array(Image.open(f));m=a[...,3]>0;c=a[...,:3].astype(int)
        green=(m&(c[...,1]>c[...,0]+15)&(c[...,1]>c[...,2]+15)).sum()
        lab,n=nd.label(m,structure=np.ones((3,3)));sz=nd.sum(m,lab,range(1,n+1)) if n else []
        specks=int(sum(1 for s in sz if s<=2))
        r={'px':int(m.sum()),'green_px':int(green),'specks<=2px':specks,'components':int(n)}
        n_=os.path.basename(f)
        if n_.startswith('features'):
            r['outside_face_px']=int((m&~fa).sum())
            # brows: dark comps above eye level, per side
            ys,xs=np.where(m);cx=(np.where(fa)[1].min()+np.where(fa)[1].max())/2
            dark=m&(c.sum(-1)<300)
            dl,dn=nd.label(dark,structure=np.ones((3,3)))
            r['dark_components']=int(dn)
        if n_=='face-default.png':
            inner=nd.binary_erosion(fa,iterations=3)
            skin=np.median(c[inner],axis=0)
            r['face_nonskin_inner_px']=int((inner&(np.abs(c-skin).sum(-1)>60)).sum())
        rep[f'{ch}/{n_}']=r
json.dump(rep,open('layers_out/qa_report.json','w'),indent=1,ensure_ascii=False)
for k,v in rep.items(): print(k,v)
