import numpy as np
from PIL import Image
from scipy import ndimage as nd
def keep(m,mn):
    lab,n=nd.label(m)
    if n==0: return m
    sz=nd.sum(m,lab,range(1,n+1));return np.isin(lab,[i+1 for i,s in enumerate(sz) if s>=mn])
rd=lambda f:np.array(Image.open(f).convert('RGB')).astype(int)
base=rd('sk/base.jpg');hair=np.roll(rd('sk/hair_gen.jpg'),1,0);fg=rd('sk/face_gen.jpg')
green=lambda a:(a[...,1]>120)&(a[...,1]-a[...,0]>50)&(a[...,1]-a[...,2]>50)
white=base.min(-1)>232
bnw=keep(~white,2000)
hm=keep(~green(hair),200)
s=base.sum(-1)
skinlike=(base[...,0]>200)&(base[...,1]>170)
# hair mask: gen hair mask snapped to base: dilate 2, within base nonwhite, not skin-like
hm2=nd.binary_dilation(hm,iterations=2)&bnw&~skinlike
hm2=keep(hm2,200)
# face visible = rest of base object
fv=bnw&~hm2
fv=keep(fv,2000)
# recover missing hair strands (dark base px not in hair, touching hair, not face outline)
dark=s<330
outlinezone=fv&~nd.binary_erosion(fv,iterations=4)
miss=dark&~hm2&bnw&~nd.binary_erosion(fv,iterations=3)
lab,n=nd.label(keep(miss,8));t=np.unique(lab[nd.binary_dilation(hm2,iterations=2)&(lab>0)]);miss=np.isin(lab,t[t>0])&~outlinezone
hm2|=miss; fv&=~hm2
print('hair',hm2.sum(),'fv',fv.sum(),'miss',miss.sum())
ys,xs=np.where(fv);print('fv bbox',xs.min(),ys.min(),xs.max(),ys.max())
# face layer: gen oval scaled to fv width, aligned at chin/center
g=~green(fg);g=keep(g,5000);gy,gx=np.where(g);gb=(gx.min(),gy.min(),gx.max(),gy.max())
sc=(xs.max()-xs.min())/(gb[2]-gb[0])
gi=Image.fromarray(np.dstack([fg,g*255]).astype(np.uint8)).crop((gb[0],gb[1],gb[2]+1,gb[3]+1))
gi=gi.resize((round(gi.width*sc),round(gi.height*sc)),Image.NEAREST)
F=Image.new('RGBA',(1024,1024));F.paste(gi,(xs.min(),ys.max()-gi.height+1),gi);F=np.array(F)
print('scale',sc)
fvtop=np.where(fv)[0].min()
allow=np.zeros_like(fv);allow[:fvtop+3]=True
allow|=nd.binary_dilation(hm2,iterations=1)
F[~allow,3]=0
F[fv,:3]=base[fv];F[fv,3]=255
F[...,3]=keep(F[...,3]>0,3000)*255
fa0=F[...,3]>0
fa1=nd.binary_fill_holes(nd.binary_closing(fa0,iterations=6)|fa0)
newp=fa1&~fa0
F[newp,:3]=[255,231,224];F[newp,3]=255
skin=np.median(base[fv&~nd.binary_dilation(hm2,iterations=8)&(base[...,0]>230)],axis=0).astype(np.uint8);print('skin',skin)
fa=F[...,3]>0
inner=nd.binary_erosion(fa,iterations=8)
F[hm2&inner,:3]=skin            # under hair: flat skin
dd=np.abs(F[...,:3].astype(int)-skin.astype(int)).sum(-1)
F[inner&(dd<40),:3]=skin
# forehead/bang shadow: non-skin pixels in face near hair, above ear-line -> hair layer
H=np.zeros((1024,1024,4),np.uint8);H[...,:3]=base;H[...,3]=hm2*255
# use gen hair colours where base pixel isn't hair-ish (shouldn't happen much)
diff=np.abs(F[...,:3].astype(int)-skin).sum(-1)
near=nd.binary_dilation(hm2,iterations=60)
fvy=np.where(fv)[0]
earline=int(np.percentile(np.where(fv&inner)[0],45))
sh=inner&near&(diff>18)&~hm2&(np.arange(1024)[:,None]<earline)
# don't treat the face's own outline as shadow
sh&=nd.binary_erosion(fa,iterations=6)
print('shadow px',sh.sum(),'earline',earline)
H[sh,:3]=F[sh,:3];H[sh,3]=255;F[sh,:3]=skin
# remove green fringe from hair
a=H[...,:3].astype(int);gr=(H[...,3]>0)&(a[...,1]>a[...,0]+15)&(a[...,1]>a[...,2]+15);H[gr,3]=0
Image.fromarray(F).save('sk/face_final.png');Image.fromarray(H).save('sk/hair_final.png')
# blank composite on white
c=Image.new('RGBA',(1024,1024),'white');c.alpha_composite(Image.fromarray(F));c.alpha_composite(Image.fromarray(H));c.convert('RGB').save('sk/blank_white.png')
# ears
eared=rd('sk/eared.jpg')
d=np.abs(eared-base).sum(-1)
nonw=eared.min(-1)<244
em=(d>40)&nonw
em=keep(em,300)
em=nd.binary_closing(em,iterations=2)&nonw
em=nd.binary_opening(em,iterations=1)
em=keep(em,3000)
# ears must not eat hair pixels that exist in base
em&=~(hm2&(np.abs(eared-base).sum(-1)<60))
em=keep(em,3000)
E=np.zeros((1024,1024,4),np.uint8);E[...,:3]=eared;E[...,3]=em*255
Image.fromarray(E).save('sk/headwear_final.png');print('ears',em.sum())
