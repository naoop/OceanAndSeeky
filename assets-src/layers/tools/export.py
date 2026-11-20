import numpy as np, json, glob, os
from PIL import Image
T=json.load(open('layers_out/transform.json'))
def down(img, s, tx, ty, opaque_min=0.5, ncol=32):
    """palette-mode downscale: quantize master to ncol colours, then each output pixel takes the
    colour with the largest coverage in its source footprint (transparent if opaque coverage < opaque_min)"""
    w=round(1024*s)
    a=np.array(img);m=a[...,3]>127
    idx=np.full(m.shape,-1,int)
    px=Image.fromarray(a[...,:3][m][None,:,:].astype(np.uint8))
    q=px.quantize(colors=ncol,method=Image.MEDIANCUT,dither=Image.NONE)
    pal=np.array(q.getpalette()[:3*ncol]).reshape(-1,3)
    idx[m]=np.array(q)[0]
    rs=lambda mk: np.array(Image.fromarray((mk*255).astype(np.uint8)).resize((w,w),Image.BOX)).astype(float)/255
    cov_op=rs(m)
    covs=np.stack([rs(idx==k) for k in range(len(pal))],-1)
    best=covs.argmax(-1)
    out=np.zeros((w,w,4),np.uint8);out[...,:3]=pal[best];out[...,3]=(cov_op>=opaque_min)*255
    from scipy import ndimage as nd
    al=out[...,3]>0;lab,n=nd.label(al,structure=np.ones((3,3)))
    if n:
        sz=nd.sum(al,lab,range(1,n+1));out[...,3]=np.isin(lab,[i+1 for i,v in enumerate(sz) if v>2])*255
    canvas=Image.new('RGBA',(364,498));canvas.paste(Image.fromarray(out),(tx,ty));return canvas
def export(ch):
    t=T[ch];md=f'layers_out/{ch}/master';od=f'layers_out/{ch}'
    for f in glob.glob(f'{md}/*.png'):
        n=os.path.basename(f);isfeat=n.startswith('features')
        im=down(Image.open(f).convert('RGBA'),t['scale'],t['tx'],t['ty'],opaque_min=0.33 if isfeat else 0.5,ncol=64 if isfeat else 128)
        im.save(f'{od}/{n}')
if __name__=='__main__':
    for ch in T: export(ch)
