import json,re
js=open('repo_assets/faces.js').read()
cat={}
for ch in ['Ocean','Seeky']:
    blk=js[js.index(f'"{ch}"'):];blk=blk[:blk.index(']')]
    items=re.findall(r'"prefix": "face-([^"]+)",\s*"label": "([^"]+)"',blk)
    T=json.load(open('layers_out/transform.json'))[ch]
    ex={'default':{'label':'默认','face':'face-default.png','features':'features-default.png'}}
    for p,l in items: ex[p]={'label':l,'face':'face-default.png','features':f'features-{p}.png','sourcePrefix':f'face-{p}'}
    d={'character':ch,'canvas':[364,498],
       'stack':['face','features','hair','headwear'],
       'layers':{'face':'face-default.png','hair':'hair.png','headwear':{'ears':'headwear-ears.png'}},
       'faceShapes':{'default':'face-default.png'},
       'expressions':ex,
       'master':{'canvas':[1024,1024],'dir':'master/','toSprite':{'scale':T['scale'],'offset':[T['tx'],T['ty']],'note':'sprite_xy = master_xy*scale + offset; downscale = palette-quantize then per-pixel majority colour (pixel-art friendly)'}}}
    json.dump(d,open(f'layers_out/{ch}/layers.json','w'),ensure_ascii=False,indent=1)
    print(ch,len(ex))
