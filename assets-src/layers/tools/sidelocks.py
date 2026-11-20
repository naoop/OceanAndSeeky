import numpy as np
from PIL import Image
from scipy import ndimage as nd
G='/cursor/stores/user/grok-bot/agents/758c58c1-f895-495a-bd45-3bddd65ecc23/assets/f69bdcd31cbd7c3d074a35b024310544cb5a0c7179cf12ea95c21450e41e97d2.jpg'
g=np.array(Image.open(G).convert('RGB')).astype(int)
g=np.roll(np.roll(g,-1,0),-1,1)  # align
comp=np.array(Image.open('pr1/L/composite.png')).astype(int)
H=np.array(Image.open('pr1/L/hair_final.png'));F=np.array(Image.open('pr1/L/face_final.png'))
cw=comp[...,:3]*comp[...,3:]/255+255*(1-comp[...,3:]/255)
d=np.abs(g-cw).sum(-1)
hm=H[...,3]>0
s=g.sum(-1)
hairish=(s<330)|((g[...,0]<150)&(s<420))   # black hair + dark outline
m=(d>90)&hairish&~hm
yy,xx=np.mgrid[:1024,:1024]
region=(yy>430)&(yy<800)&((xx<420)|(xx>600))
m&=region
m=nd.binary_closing(m,iterations=1)&(s<450)
lab,n=nd.label(m);sz=nd.sum(m,lab,range(1,n+1))
m=np.isin(lab,[i+1 for i,v in enumerate(sz) if v>=25])
print('new px',m.sum(),n)
np.save('sl_mask.npy',m)
H2=H.copy();H2[m,:3]=g[m];H2[m,3]=255
Image.fromarray(H2).save('hair_sl.png')
c=Image.new('RGBA',(1024,1024),'white')
for L in [F,np.array(Image.open('pr1/L/features_final.png')),H2,np.array(Image.open('pr1/L/headwear_final.png'))]: c.alpha_composite(Image.fromarray(L))
vis=np.array(c.convert('RGB'));v2=vis.copy();v2[m]=[255,0,0]
S=Image.new('RGB',(724*3,724),'white')
S.paste(Image.open('pr1/ocean_head_ref.png').convert('RGB').resize((662,724)),(0,0))
S.paste(Image.fromarray(vis.astype(np.uint8)).crop((150,60,874,784)),(724,0))
S.paste(Image.fromarray(v2.astype(np.uint8)).crop((150,60,874,784)),(1448,0));S.save('sl_check.png')
