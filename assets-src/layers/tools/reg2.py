import numpy as np
from PIL import Image
def dm(a): return a.astype(int).sum(-1)<250
def iou_at(D,S,tx,ty):
    h,w=S.shape;can=np.zeros_like(D)
    x0,y0=max(tx,0),max(ty,0);x1,y1=min(tx+w,D.shape[1]),min(ty+h,D.shape[0])
    if x1<=x0 or y1<=y0: return 0
    can[y0:y1,x0:x1]=S[y0-ty:y1-ty,x0-tx:x1-tx]
    return (can&D).sum()/max(1,(can|D).sum())
def fit(blank, gen):
    """returns s,tx,ty: gen resized by s placed at (tx,ty) matches blank"""
    D=dm(blank);G=Image.fromarray(gen.astype(np.uint8))
    f=4;Ds=D[::f,::f];best=None
    for s in np.arange(0.85,1.16,0.01):
        S=dm(np.array(G.resize((round(1024*s/f),round(1024*s/f)),Image.NEAREST)))
        # coarse centering by bbox
        ys,xs=np.where(S);yd,xd=np.where(Ds)
        tx0=int(round(xd.mean()-xs.mean()));ty0=int(round(yd.min()-ys.min()))
        for ty in range(ty0-6,ty0+7):
            for tx in range(tx0-6,tx0+7):
                v=iou_at(Ds,S,tx,ty)
                if best is None or v>best[0]: best=(v,s,tx*f,ty*f)
    v,s0,tx0,ty0=best;best=None
    for s in np.arange(s0-0.012,s0+0.0121,0.003):
        S=dm(np.array(G.resize((round(1024*s),round(1024*s)),Image.NEAREST)))
        for ty in range(ty0-6,ty0+7):
            for tx in range(tx0-6,tx0+7):
                v=iou_at(D,S,tx,ty)
                if best is None or v>best[0]: best=(v,s,tx,ty)
    return best
def warp(gen,s,tx,ty,bg=255):
    G=Image.fromarray(gen.astype(np.uint8)).resize((round(1024*s),round(1024*s)),Image.LANCZOS)
    out=Image.new('RGB',(1024,1024),(bg,bg,bg));out.paste(G,(tx,ty));return np.array(out).astype(int)
