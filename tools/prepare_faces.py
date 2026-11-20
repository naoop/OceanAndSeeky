"""Register facial details from the animation frames to the fixed portrait heads."""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter


# Eye centers and mouth center in each 364 x 498 source frame. Separate mouth
# sampling avoids copying fingers, sleeves or the hammer into the resting pose.
FACES = {
    "Ocean": [
        ("grimace-0", "浅笑", (153,191), (206,191), (181,211), (24,13)),
        ("grimace-1", "挑眉笑", (153,190), (206,190), (181,211), (32,17)),
        ("grimace-2", "张嘴", (152,189), (206,189), (180,213), (28,21)),
        ("grimace-3", "吐舌", (151,189), (204,189), (179,216), (35,27)),
        ("grimace-4", "闭眼大笑", (154,190), (209,190), (182,211), (34,23)),
        ("ocean-hammer-1", "咧嘴笑", (174,200), (218,208), (194,221), (25,15)),
        ("ocean-hammer-2", "使劲笑", (188,202), (230,212), (205,222), (23,15)),
        ("ocean-hammer-3", "开心张嘴", (161,197), (211,193), (188,216), (22,18)),
        ("ocean-hammer-4", "眯眼微笑", (159,193), (213,192), (186,210), (23,12)),
    ],
    "Seeky": [
        ("hammer-0", "平静", (160,193), (211,193), (186,213), (23,12)),
        ("hammer-1", "抿嘴笑", (175,209), (218,214), (196,227), (23,14)),
        ("hammer-2", "用力", (192,210), (237,222), (211,231), (20,11)),
        ("hammer-3", "开心张嘴", (162,191), (210,188), (187,212), (24,17)),
        ("hammer-4", "眯眼笑", (161,194), (213,193), (188,211), (24,13)),
        ("soft-0", "认真", (164,195), (212,195), (190,215), (21,12)),
        ("soft-1", "歪头微笑", (175,195), (223,209), (194,219), (23,13)),
        ("soft-2", "轻笑", (176,193), (224,193), (202,213), (21,12)),
        ("soft-3", "闭眼微笑", (167,196), (217,196), (192,217), (23,13)),
    ],
}


def clean_skin(base, actor, reference):
    """Align the supplied faceless head using hair, jaw and cheek contours."""
    sample = np.asarray(Image.open(reference).convert("RGB"))
    original = np.asarray(base)
    y, x = np.mgrid[145:233:2, 122:241:2]
    stable = (y < 164) | (y > 219) | (x < 137) | (x > 224)
    y, x = y[stable], x[stable]
    target = original[y, x, :3].astype(float)
    # The references have different padding but share the same chin position
    # within each character's pair. Register only the central face area.
    cx, cy = ((520, 744) if actor == "Ocean" else (524, 628))
    def loss(pos):
        scale, ox, oy = pos
        sx = np.rint((x-181)*scale+ox).astype(int)
        sy = np.rint((y-227)*scale+oy).astype(int)
        return np.abs(sample[sy,sx].astype(float)-target).mean()
    coarse = min(((s, cx+dx, cy+dy) for s in np.arange(2.8,4.5,.1)
                  for dx in range(-32,33,4) for dy in range(-36,37,4)), key=loss)
    s,x0,y0 = coarse
    s,x0,y0 = min(((s+ds,x0+dx,y0+dy) for ds in (-.06,-.03,0,.03,.06)
                   for dx in range(-3,4) for dy in range(-3,4)), key=loss)
    aligned = Image.fromarray(sample).transform(base.size, Image.Transform.AFFINE,
        (s,0,x0-181*s,0,s,y0-227*s), resample=Image.Resampling.BILINEAR)
    rgb = np.asarray(aligned).astype(int)
    yy,xx = np.indices(rgb.shape[:2])
    interior = ((xx >= 124) & (xx <= 236) & (yy >= 143) & (yy <= 228))
    skin = interior & (rgb[:,:,0] > 201) & (rgb[:,:,1] > 148) & (rgb[:,:,2] > 140)
    connected = Image.fromarray(np.uint8(skin)*255).copy()
    ImageDraw.floodfill(connected, (181,202), 128)
    if connected.histogram()[128] < 1000:
        raise ValueError(f"Faceless reference registration failed: {reference.name}")
    # Reuse the portrait skin tone to avoid introducing a JPEG-coloured seam.
    color = base.getpixel((182,202))
    layer = Image.new("RGBA", base.size, color)
    # Preserve the original cheek/jaw outline even where JPEG registration is
    # a pixel wider than the outfit drawing. Feather only the skin transition.
    cheek = Image.new("L",base.size)
    ImageDraw.Draw(cheek).polygon([(133,159),(226,159),(226,198),(220,207),
        (211,213),(197,220),(181,223),(162,219),(147,213),(136,206),(132,196)],fill=255)
    layer.putalpha(ImageChops.multiply(connected.point(lambda v: 255 if v == 128 else 0),
                                       cheek.filter(ImageFilter.GaussianBlur(1))))
    return layer


def feature_ink(aligned, mask, light_lips=False):
    """Keep ink and painted facial detail, discarding pale source skin."""
    rgba = np.array(aligned)
    r,g,b = (rgba[:,:,i].astype(int) for i in range(3))
    ink = (r < 207) | (g < 143) | ((r-g > 66) & (b < 191))
    if light_lips:
        ink |= (r < 235) | (g < 211)
    marked = Image.fromarray(np.uint8(ink & (np.asarray(mask)>0) & (rgba[:,:,3]>0))*255)
    bounds = marked.getbbox()
    if bounds:
        detail = marked.crop(bounds)
        # Reject isolated flecks, keeping connected strokes and fine lip lines.
        for y,x in np.argwhere(np.asarray(detail)>0):
            if detail.getpixel((int(x),int(y))) == 255:
                ImageDraw.floodfill(detail, (int(x),int(y)), 128)
                size = detail.histogram()[128]
                ImageDraw.floodfill(detail, (int(x),int(y)), 127 if size >= 4 else 0)
        marked.paste(detail.point(lambda v: 255 if v else 0), bounds)
        # Keep enclosed highlights and teeth in their original colours.
        holes = Image.new("L", (detail.width+2, detail.height+2))
        holes.paste(marked.crop(bounds),(1,1))
        ImageDraw.floodfill(holes,(0,0),128)
        marked.paste(holes.crop((1,1,detail.width+1,detail.height+1)).point(
            lambda v: 0 if v == 128 else 255),bounds)
    rgba[:,:,3] = np.asarray(marked)
    return Image.fromarray(rgba)


def prepare_faces(dest):
    catalog = {}
    for actor, faces in FACES.items():
        base = Image.open(dest / f"{actor}-4-3.png").convert("RGBA")
        target_x, target_y = (153, 191) if actor == "Ocean" else (155, 194)
        root = Path(__file__).resolve().parents[1]
        stem = "Ocean" if actor == "Ocean" else "seeky"
        skins = [clean_skin(base, actor, root / f"{stem}0{i}.jpg") for i in (1,2)]
        entries = []
        for key, label, left, right, mouth, mouth_size in faces:
            source = Image.open(dest / f"{key}.png").convert("RGBA")
            dx, dy = right[0]-left[0], right[1]-left[1]
            slope_x, slope_y = dx/54, dy/54
            affine = (slope_x, -slope_y, left[0]-slope_x*target_x+slope_y*target_y,
                      slope_y, slope_x, left[1]-slope_y*target_x-slope_x*target_y)
            aligned = source.transform(base.size, Image.Transform.AFFINE, affine)
            mask = Image.new("L", base.size)
            draw = ImageDraw.Draw(mask)
            # Trace eyes independently of the brow, fringe and pointing fingers.
            for x in (target_x, target_x+54):
                eye_top = target_y-13
                eye_bottom = target_y+10
                draw.polygon([(x-16,target_y-3),(x-13,eye_top+3),
                              (x-7,eye_top),(x+8,eye_top),(x+16,eye_top+6),
                              (x+16,target_y+1),(x+10,eye_bottom),
                              (x-9,eye_bottom),(x-14,target_y+3)], fill=255)
            if actor == "Ocean":
                brow = [(141,170),(146,166),(157,165),(167,169),(169,174),(157,171),(142,172)]
                if key == "grimace-1":
                    brow = [(141,167),(145,166),(165,172),(170,175),(168,178),(144,171)]
                elif key == "grimace-2":
                    brow = [(142,172),(146,169),(165,167),(168,164),(168,170),(160,173)]
            else:
                brow = [(144,174),(147,172),(162,172),(169,174),(171,178),(163,176),(144,176)]
                if key == "hammer-2":
                    brow = [(144,171),(147,170),(167,178),(173,180),(170,182),(147,174)]
            draw.polygon(brow,fill=255)
            draw.polygon([(2*(target_x+27)-x,y) for x,y in brow],fill=255)
            if key in ("grimace-2","grimace-3"):
                for x in (target_x,target_x+54):
                    sign = 1 if x == target_x else -1
                    draw.polygon([(x-17*sign,194),(x-7*sign,196),(x-4*sign,201),
                                  (x-17*sign,204)],fill=0)
            overlay = feature_ink(aligned, mask)
            mw, mh = mouth_size
            level = source.rotate(math.degrees(math.atan2(dy, dx)), center=mouth)
            mx, my = mouth
            patch = level.crop((mx-mw//2,my-mh//2,mx-mw//2+mw,my-mh//2+mh))
            patch.thumbnail((34,20), Image.Resampling.NEAREST)
            # Keep a skin margin around the replacement so the resting mouth is covered.
            lip_mask = Image.new("L", patch.size)
            ImageDraw.Draw(lip_mask).ellipse((0,0,patch.width-1,patch.height-1), fill=255)
            center = (181,212) if actor == "Ocean" else (181,214)
            patch = feature_ink(patch, lip_mask, light_lips=key.startswith("ocean-hammer-"))
            overlay.alpha_composite(patch, (center[0]-patch.width//2,center[1]-patch.height//2))
            prefix = "face-" + key
            for skin, suffix in zip(skins, ("", "-plain")):
                Image.alpha_composite(skin, overlay).save(dest / (prefix+suffix+".png"))
            preview = Image.alpha_composite(Image.alpha_composite(base, skins[0]), overlay)
            preview.crop((110,133,253,241)).save(dest / (prefix+"-icon.png"))
            entries.append({"prefix":prefix,"label":label})
        catalog[actor] = entries
    (dest / "faces.js").write_text("const faceCatalog = " +
        json.dumps(catalog, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")
