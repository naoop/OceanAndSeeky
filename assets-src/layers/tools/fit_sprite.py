import numpy as np, json
from PIL import Image
def masks(rgba):
    a=rgba[...,3]>127;c=rgba[...,:3].astype(int);s=c.sum(-1)
    dark=a&(s<260)
    skin=a&(c[...,0]>230)&(c[...,1]>190)&(c[...,1]<245)&(c[...,2]>170)
    return dark,skin
def comp(ch):
    md=f'layers_out/{ch}/master';c=Image.new('RGBA',(1024,1024))
    for f in ['face-default','features-default','hair','headwear-ears']: c.alpha_composite(Image.open(f'{md}/{f}.png'))
    return c
res={}
for ch,ylim in [('Ocean',235),('Seeky',235)]:
    sp=np.array(Image.open(f'repo_assets/{ch}-1-1.png').convert('RGBA'))
    sd,ss=masks(sp);sd[ylim:]=0;ss[ylim:]=0
    C=comp(ch);best=None
    for s in np.arange(0.26,0.42,0.004):
        w=round(1024*s);im=np.array(C.resize((w,w),Image.BOX))
        d,k=masks(im)
        ys,xs=np.where(d);yd,xd=np.where(sd)
        tx0=int(round(xd.mean()-xs.mean()));ty0=int(round(yd.mean()-ys.mean()))
        for ty in range(ty0-8,ty0+9):
            for tx in range(tx0-8,tx0+9):
                D=np.zeros(sd.shape,bool);K=np.zeros(sd.shape,bool)
                y0,x0=max(ty,0),max(tx,0);y1,x1=min(ty+w,sd.shape[0]),min(tx+w,sd.shape[1])
                D[y0:y1,x0:x1]=d[y0-ty:y1-ty,x0-tx:x1-tx];K[y0:y1,x0:x1]=k[y0-ty:y1-ty,x0-tx:x1-tx]
                D[ylim:]=0;K[ylim:]=0
                v=(D&sd).sum()/max(1,(D|sd).sum())+(K&ss).sum()/max(1,(K|ss).sum())
                if best is None or v>best[0]: best=(v,float(s),tx,ty)
    print(ch,best);res[ch]=dict(score=best[0],scale=best[1],tx=best[2],ty=best[3])
json.dump(res,open('layers_out/transform.json','w'),indent=1)
