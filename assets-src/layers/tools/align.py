import numpy as np
from PIL import Image
def dark(a): return a[...,:3].astype(int).sum(-1)<250
def best(ref,img,rng=12):
    A=dark(ref);B=dark(img);bs=None
    for dy in range(-rng,rng+1):
        for dx in range(-rng,rng+1):
            s=(A&np.roll(np.roll(B,dy,0),dx,1)).sum()/max(1,(A|np.roll(np.roll(B,dy,0),dx,1)).sum())
            if bs is None or s>bs[0]: bs=(s,dx,dy)
    return bs
if __name__=='__main__':
    import sys
    r=np.array(Image.open(sys.argv[1]).convert('RGB'));i=np.array(Image.open(sys.argv[2]).convert('RGB'))
    print(best(r,i))
