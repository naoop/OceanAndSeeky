from PIL import Image, ImageDraw, ImageFont
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc',20)
for ch,ref in [('Ocean','pr1/ocean_head_ref.png'),('Seeky','seeky_head_ref.png')]:
    md=f'layers_out/{ch}/master';T=300
    L=[('face-default','1 脸+人耳'),('features-default','2 五官'),('hair','3 头发(刘海/阴影/碎发)'),('headwear-ears','4 头饰')]
    S=Image.new('RGB',(T*6,T+40),'white');d=ImageDraw.Draw(S)
    comp=Image.new('RGBA',(1024,1024))
    for i,(f,t) in enumerate(L):
        im=Image.open(f'{md}/{f}.png');comp.alpha_composite(im)
        b=Image.new('RGBA',(1024,1024),(232,240,248,255));b.alpha_composite(im)
        S.paste(b.resize((T,T),Image.NEAREST).convert('RGB'),(i*T,40));d.text((i*T+8,8),t,fill='black',font=font)
    b=Image.new('RGBA',(1024,1024),(255,255,255,255));b.alpha_composite(comp)
    S.paste(b.resize((T,T),Image.LANCZOS).convert('RGB'),(4*T,40));d.text((4*T+8,8),'合成 (1024 母版)',fill='black',font=font)
    r=Image.open(ref).convert('RGB');r.thumbnail((T,T));S.paste(r,(5*T,40));d.text((5*T+8,8),'原 sprite 头部',fill='black',font=font)
    S.save(f'layers_out/{ch}_master_sheet.png')
