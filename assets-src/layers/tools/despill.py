import numpy as np, glob
from PIL import Image
from scipy import ndimage as nd
for f in glob.glob('layers_out/*/master/*.png'):
    a=np.array(Image.open(f));m=a[...,3]>0;c=a[...,:3].astype(int)
    g=m&(c[...,1]>np.maximum(c[...,0],c[...,2])+10)
    if not g.any(): continue
    edge=m&~nd.binary_erosion(m,iterations=3)
    a[g&edge,3]=0
    rest=g&~edge
    a[rest,1]=np.maximum(c[rest,0],c[rest,2]).clip(0,255)  # clamp green
    print(f,int(g.sum()),int((g&edge).sum()))
    Image.fromarray(a).save(f)
