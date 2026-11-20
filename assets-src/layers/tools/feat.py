import numpy as np, json, sys
from PIL import Image
from scipy import ndimage as nd
from align import best
A='/cursor/stores/user/grok-bot/agents/758c58c1-f895-495a-bd45-3bddd65ecc23/assets/'
def keep(m,mn):
    lab,n=nd.label(m)
    if n==0: return m
    sz=nd.sum(m,lab,range(1,n+1));return np.isin(lab,[i+1 for i,s in enumerate(sz) if s>=mn])
def extract(genpath, blank, face_a, hair_a, T=42):
    g=np.array(Image.open(genpath).convert('RGB')).astype(int)
    from reg2 import fit,warp
    v,sc,tx,ty=fit(blank,g)
    g=warp(g,sc,tx,ty)
    s,dx,dy=v,(sc,tx),ty
    dist=nd.distance_transform_edt(face_a)
    region=(dist>24)&~nd.binary_dilation(hair_a,iterations=2)
    d=np.abs(g-blank.astype(int)).sum(-1)
    m=(d>T)&region
    m=nd.binary_closing(m,iterations=1)&region&(d>T*0.6)
    m=keep(m,20)
    m=nd.binary_fill_holes(m)&region   # fill eye interiors (whites)
    out=np.zeros((1024,1024,4),np.uint8);out[...,:3]=g;out[...,3]=m*255
    return out,(s,dx,dy)

def postproc(out, cx=512):
    a=out[...,3]>0
    lab,n=nd.label(a)
    if n:
        sz=nd.sum(a,lab,range(1,n+1))
        big=np.isin(lab,[i+1 for i,s in enumerate(sz) if s>=200])
        near=nd.binary_dilation(big,iterations=15)
        keepids=[]
        for i,s in enumerate(sz):
            c=lab==i+1
            ys,xs=np.where(c)
            mc=out[...,:3][c].astype(int)
            light=(mc.min(-1)>185).mean()>0.6
            if light and s<200: continue
            if s>=60 or (c&near).any() or abs(xs.mean()-cx)<30: keepids.append(i+1)
        a=np.isin(lab,keepids)
    rgb=out[...,:3].astype(int)
    dark=a&(rgb.sum(-1)<260)
    # brow band = dark pixels above the eyes: take dark components whose top is in the upper 30% of feature bbox
    ys,xs=np.where(a);top,bot=ys.min(),ys.max()
    band=np.zeros_like(a);band[top-2:top+int((bot-top)*0.28)]=True
    bd=dark&band
    st=np.ones((5,15),bool)
    closed=nd.binary_closing(bd,structure=st)&band
    add=closed&~a
    if add.any():
        _,ind=nd.distance_transform_edt(~bd,return_indices=True)
        out=out.copy();out[add,:3]=out[ind[0][add],ind[1][add],:3];a=a|add
    out=out.copy();out[...,3]=a*255
    return out

def postproc2(out, cx=None):
    """drop side junk outside eye span, clean brows (horizontal strokes only) and make them continuous"""
    o=out.copy();a=o[...,3]>0;rgb=o[...,:3].astype(int)
    # drop thin line junk (stray hair strokes) in the upper 65% of the feature area
    lab,n=nd.label(a);fy0,fy1=np.where(a)[0].min(),np.where(a)[0].max()
    for i in range(1,n+1):
        c=lab==i;yy,xx=np.where(c)
        if yy.mean()<fy0+0.65*(fy1-fy0) and c.sum()<600:
            if nd.binary_erosion(c).sum()<0.12*c.sum(): a[c]=False
    lab,n=nd.label(a);sz=nd.sum(a,lab,range(1,n+1))
    dark=a&(rgb.sum(-1)<300)
    # eyes = two largest components
    darkids=[i+1 for i in range(n) if sz[i]>=300 and rgb[lab==i+1].sum(-1).mean()<400]
    em=np.isin(lab,darkids);ys,xs=np.where(em)
    ex0,ex1=xs.min(),xs.max()
    # eye top: top of the two largest dark comps that are not in the lowest third (mouth)
    mid=(ex0+ex1)/2;eyes=[]
    for side in (-1,1):
        lat=[i for i in darkids if (np.where(lab==i)[1].mean()-mid)*side>40]
        if not lat: continue
        mx=max(sz[i-1] for i in lat)
        big=[i for i in lat if sz[i-1]>=0.5*mx]
        eyes.append(max(big,key=lambda i:np.where(lab==i)[0].mean()))
    ey0=min(np.where(lab==i)[0].min() for i in eyes)
    exs=np.concatenate([np.where(lab==i)[1] for i in eyes]);ex0,ex1=exs.min(),exs.max()
    if cx is None: cx=(ex0+ex1)/2
    keepids=[]
    for i in range(1,n+1):
        c=lab==i;yy,xx=np.where(c);mx=xx.mean()
        if mx<ex0-12 or mx>ex1+12: continue
        keepids.append(i)
    a=np.isin(lab,keepids)
    # brow region: above eyes' top
    band=np.zeros_like(a);band[:ey0-1]=True
    br=a&band
    brd=br&(rgb.sum(-1)<330)
    clean=nd.binary_opening(brd,structure=np.ones((3,7),bool))
    clean=nd.binary_dilation(clean,iterations=1)&brd
    cl,cn=nd.label(clean);kk=[]
    for j in range(1,cn+1):
        yy,xx=np.where(cl==j)
        if len(xx)>=60 and (np.ptp(xx)+1)>=1.5*(np.ptp(yy)+1): kk.append(j)
    clean=np.isin(cl,kk)
    a&=~(br&~clean)
    # continuity: per side interpolate top/bottom edges
    add=np.zeros_like(a)
    for side in (0,1):
        m=clean.copy()
        if side==0: m[:,int(cx):]=False
        else: m[:,:int(cx)]=False
        ys2,xs2=np.where(m)
        if len(xs2)<20: continue
        cols=np.unique(xs2);tops=np.array([ys2[xs2==c].min() for c in cols]);bots=np.array([ys2[xs2==c].max() for c in cols])
        allc=np.arange(cols.min(),cols.max()+1)
        ti=np.round(np.interp(allc,cols,tops)).astype(int);bi=np.round(np.interp(allc,cols,bots)).astype(int)
        for c,t,b in zip(allc,ti,bi):
            if c in set(cols): continue
            add[t:b+1,c]=True
    add&=~a
    if add.any():
        col=np.median(rgb[clean],axis=0).astype(np.uint8)
        o[add,:3]=col;a|=add
    brow=clean|add
    if brow.any():
        yb,xb=np.where(brow);cols=np.unique(xb)
        bots=np.array([yb[xb==c].max() for c in cols])
        allx=np.arange(a.shape[1]);bb=np.interp(allx,cols,bots)
        yy=np.arange(a.shape[0])[:,None]
        junk=a&band&~brow&(yy<bb[None,:]+1)
        a&=~junk
    # prune 1-px spurs/lines in the upper part
    fy0,fy1=np.where(a)[0].min(),np.where(a)[0].max();lim=int(fy0+0.6*(fy1-fy0))
    k=np.ones((3,3));k[1,1]=0
    for _ in range(40):
        nb=nd.convolve(a.astype(int),k,mode='constant')
        sp=a&(nb<=2);sp[lim:]=False
        if not sp.any(): break
        a&=~sp
    lab,n=nd.label(a)
    if n:
        sz=nd.sum(a,lab,range(1,n+1));a=np.isin(lab,[i+1 for i,v in enumerate(sz) if v>=12])
    o[...,3]=a*255
    return o

def despeck(out, cx, minsz=40):
    o=out.copy();a=o[...,3]>0;lab,n=nd.label(a)
    if n==0: return o
    sz=nd.sum(a,lab,range(1,n+1));k=[]
    for i,s in enumerate(sz):
        yy,xx=np.where(lab==i+1)
        if s>=minsz or abs(xx.mean()-cx)<25: k.append(i+1)
    o[...,3]=np.isin(lab,k)*255;return o
def blush_stamp(feat, ymin, ymax, cx, half=60):
    r,g,b=[feat[...,i].astype(int) for i in range(3)]
    m=(feat[...,3]>0)&(r>200)&(r-g>25)&(g>150)
    m[:ymin]=0;m[ymax:]=0;m[:,int(cx-half):int(cx+half)]=0
    lab,n=nd.label(m);sz=nd.sum(m,lab,range(1,n+1))
    m=np.isin(lab,[i+1 for i,s in enumerate(sz) if s>=300])
    st=np.zeros_like(feat);st[m]=feat[m];return st
def apply_blush(feat, stamp):
    o=feat.copy();a=o[...,3]>0
    protect=nd.binary_dilation(a&(o[...,:3].astype(int).sum(-1)<400),iterations=3)
    s=(stamp[...,3]>0)&~a&~protect
    o[s]=stamp[s];return o
