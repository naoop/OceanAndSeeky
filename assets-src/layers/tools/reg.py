import numpy as np
from PIL import Image
def dmask(img,thr=200): return np.array(img.convert('RGB')).astype(int).sum(-1)<thr
def register(src_img, dst_img, scales, region=None, step=2, rng=None):
    """find s,tx,ty so that dst(x,y) ~ src((x-tx)/s,(y-ty)/s), i.e. src scaled by s and pasted at (tx,ty)"""
    D=dmask(dst_img)
    if region is not None: D=D&region
    best=None
    for s in scales:
        w,h=round(src_img.width*s),round(src_img.height*s)
        S=dmask(src_img.resize((w,h),Image.NEAREST))
        ys,xs=np.where(S);sb=(xs.min(),ys.min(),xs.max(),ys.max())
        Dy,Dx=np.where(D);db=(Dx.min(),Dy.min(),Dx.max(),Dy.max())
        # coarse align by bbox top-center then refine
        tx0=(db[0]+db[2])/2-(sb[0]+sb[2])/2; ty0=db[1]-sb[1]
        for ty in range(int(ty0)-30,int(ty0)+31,step):
            for tx in range(int(tx0)-30,int(tx0)+31,step):
                can=np.zeros_like(D)
                x0,y0=max(tx,0),max(ty,0);x1,y1=min(tx+w,D.shape[1]),min(ty+h,D.shape[0])
                can[y0:y1,x0:x1]=S[y0-ty:y1-ty,x0-tx:x1-tx]
                if region is not None: can&=region
                iou=(can&D).sum()/max(1,(can|D).sum())
                if best is None or iou>best[0]: best=(iou,s,tx,ty)
    return best
