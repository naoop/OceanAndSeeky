import numpy as np, os, shutil, glob
from PIL import Image
from feat import despeck, blush_stamp, apply_blush
cfg={
 'Ocean':dict(face='pr1/L/face_final.png',hair='pr1/L/hair_final.png',ears='pr1/L/headwear_final.png',
   feats={'default':'pr1/L/features_final.png',**{k:f'oc_feat/features-{k}.png' for k in ['grimace-0','grimace-1','grimace-2','grimace-3','grimace-4','ocean-hammer-1','ocean-hammer-2','ocean-hammer-3','ocean-hammer-4']}},
   blush=('grimace-0',630,690)),
 'Seeky':dict(face='sk/face_final.png',hair='sk/hair_final.png',ears='sk/headwear_final.png',
   feats={k:f'sk_feat/features-{k}.png' for k in ['default','hammer-0','hammer-1','hammer-2','hammer-3','hammer-4','soft-0','soft-1','soft-2','soft-3']},
   blush=('hammer-4',515,575)),
}
for ch,c in cfg.items():
    md=f'layers_out/{ch}/master';os.makedirs(md,exist_ok=True)
    F=np.array(Image.open(c['face']));ys,xs=np.where(F[...,3]>0);cx=(xs.min()+xs.max())/2
    shutil.copy(c['face'],f'{md}/face-default.png');shutil.copy(c['hair'],f'{md}/hair.png');shutil.copy(c['ears'],f'{md}/headwear-ears.png')
    bk,y0,y1=c['blush'];stamp=blush_stamp(np.array(Image.open(c['feats'][bk])),y0,y1,cx)
    print(ch,'stamp px',(stamp[...,3]>0).sum())
    for k,p in c['feats'].items():
        f=np.array(Image.open(p));f=despeck(f,cx);f=apply_blush(f,stamp)
        Image.fromarray(f).save(f'{md}/features-{k}.png')
