import numpy as np, json, glob, os
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as nd
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc',16)
labels={}
import re
js=open('repo_assets/faces.js').read()
for p,l in re.findall(r'"prefix": "face-([^"]+)",\s*"label": "([^"]+)"',js): labels[p]=l
labels['default']='默认'
def body(ch):
    sp=np.array(Image.open(f'repo_assets/{ch}-1-1.png').convert('RGBA'))
    od=f'layers_out/{ch}'
    F=np.array(Image.open(f'{od}/face-default.png'))[...,3]>0
    U=F.copy()
    for f in ['hair','headwear-ears']: U|=np.array(Image.open(f'{od}/{f}.png'))[...,3]>0
    chin=np.where(F)[0].max()
    kill=np.zeros(F.shape,bool);kill[:chin-6]=True
    kill|=nd.binary_dilation(U,iterations=2)
    if ch=='Seeky':
        # remove the sprite's own lop-ear pixels (light pink) left/right of the torso
        c=sp[...,:3].astype(int)
        pink=(c[...,0]>225)&(c[...,1]>170)&(c[...,2]>180)&(c[...,0]-c[...,1]>10)
        E=np.array(Image.open(f'{od}/headwear-ears.png'))[...,3]>0
        ys,xs=np.where(E);ear_bot=ys.max()
        zone=np.zeros_like(kill);zone[:ear_bot+3]=True
        lab,n=nd.label(sp[...,3]>0)
        kill|=zone&nd.binary_dilation(pink&zone,iterations=0)&~nd.binary_dilation(np.zeros_like(kill),iterations=1)&(np.abs(np.arange(364)[None,:]-182)>55)
    b=sp.copy();b[kill,3]=0
    return Image.fromarray(b),Image.fromarray(sp)
def comp(ch,feat,bg=(255,255,255,255),with_body=True):
    od=f'layers_out/{ch}';c=Image.new('RGBA',(364,498),bg)
    if with_body: c.alpha_composite(body(ch)[0])
    for f in ['face-default',f'features-{feat}','hair','headwear-ears']: c.alpha_composite(Image.open(f'{od}/{f}.png'))
    return c
def sheet(ch):
    od=f'layers_out/{ch}';L=json.load(open(f'{od}/layers.json'))
    exprs=list(L['expressions'].keys())
    Z=2;crop=(60,0,304,300) # head+shoulders
    cw,chh=(crop[2]-crop[0])*Z,(crop[3]-crop[1])*Z
    # row 1: layers
    layers=[('face-default','脸+人耳'),('features-default','五官(默认)'),('hair','头发(含刘海/阴影/碎发)'),('headwear-ears','头饰(耳朵)')]
    bodyimg,orig=body(ch)
    cols=6;rows=2+(len(exprs)+cols-1)//cols
    W=cols*cw;H=rows*(chh+30)+40
    S=Image.new('RGB',(W,H),'white');d=ImageDraw.Draw(S)
    d.text((8,8),f'{ch} 头部分层 · 364x498 工程尺寸 · 2x 放大 (NEAREST)',fill='black',font=font)
    y=40
    def tile(im,x,y,t,bg=(232,240,248,255)):
        b=Image.new('RGBA',(364,498),bg);b.alpha_composite(im)
        S.paste(b.crop(crop).resize((cw,chh),Image.NEAREST).convert('RGB'),(x,y+26));d.text((x+6,y+4),t,fill='black',font=font)
    for i,(f,t) in enumerate(layers): tile(Image.open(f'{od}/{f}.png'),i*cw,y,t)
    tile(bodyimg,4*cw,y,'身体(去头, 仅QA用)')
    tile(comp(ch,'default'),5*cw,y,'合成(默认)',bg=(255,255,255,255))
    y+=chh+30
    tile(orig,0,y,'原 sprite',bg=(255,255,255,255));tile(comp(ch,'default'),cw,y,'新分层合成',bg=(255,255,255,255))
    # overlay difference
    o=Image.new('RGBA',(364,498),(255,255,255,255));o.alpha_composite(orig);n=comp(ch,'default')
    blend=Image.blend(o.convert('RGB'),n.convert('RGB'),0.5).convert('RGBA');tile(blend,2*cw,y,'50% 叠加对位',bg=(255,255,255,255))
    y+=chh+30
    for i,e in enumerate(exprs):
        x=(i%cols)*cw;yy=y+(i//cols)*(chh+30)
        tile(comp(ch,L['expressions'][e]['features'].replace('features-','').replace('.png','')),x,yy,f'{e} {labels.get(e,"")}',bg=(255,255,255,255))
    S.save(f'layers_out/{ch}_sheet.png')
    # side by side vs original (3x, head)
    sb=Image.new('RGB',(364*3*2+20,300*3),'white')
    sb.paste(o.convert('RGB').crop((0,0,364,300)).resize((364*3,900),Image.NEAREST),(0,0))
    sb.paste(n.convert('RGB').crop((0,0,364,300)).resize((364*3,900),Image.NEAREST),(364*3+20,0))
    sb.save(f'layers_out/{ch}_vs_original.png')
