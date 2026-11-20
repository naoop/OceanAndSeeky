"""Rebuild the local studio's ready-to-display images from the approved drawings."""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from prepare_faces import prepare_faces

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "SeekyOcean妆造定稿"
DEST = ROOT / "studio-assets"
ACTORS = ("Ocean", "Seeky")
ORIGINAL_HEADS = (4, 1, 2, 3, 1, 1)
NEAREST = Image.Resampling.NEAREST


def cutout(source):
    image = source.convert("RGBA")
    ImageDraw.floodfill(image, (0, 0), (255, 255, 255, 0), thresh=12)
    return image


def head_position(body, head):
    """Register drawn hair and face pixels to the full-size original."""
    sample = np.asarray(head)
    ys, xs = np.where((sample[:, :, 3] == 255) & (sample[:, :, 0] < 130))
    ys, xs = ys[::137], xs[::137]
    pixels = np.asarray(body)
    def error(offset):
        dx, dy = offset
        return np.abs(pixels[ys + dy, xs + dx, :3].astype(int)
                      - sample[ys, xs, :3]).mean()
    coarse = min(((x, y) for x in range(-18, 40, 4)
                  for y in range(-22, 110, 4)), key=error)
    cx, cy = coarse
    return min(((x, y) for x in range(cx-4, cx+5)
                for y in range(cy-4, cy+5)), key=error)


def prepare_actor(actor):
    heads = {}
    for index in range(1, 5):
        path = next((ART / "头部").glob(f"{index}_*_{actor}.png"))
        head = cutout(Image.open(path))
        heads[index] = head
        icon = head.crop(head.getbbox())
        icon.thumbnail((110, 110), NEAREST)
        icon.save(DEST / f"{actor}-head-{index}.png")
    for outfit, original in enumerate(ORIGINAL_HEADS, 1):
        path = next((ART / "造型").glob(f"{outfit:02}_*_{actor}.png"))
        body = cutout(Image.open(path))
        xy = head_position(body, heads[original])
        bare = body.copy()
        bare.paste((0, 0, 0, 0), xy + (xy[0]+928, xy[1]+904),
                   heads[original].getchannel("A"))
        # Clear enclosed background islands left between flowers and hair.
        bare.paste((0, 0, 0, 0), (0, 0, bare.width, xy[1] + 650))
        for index, head in heads.items():
            result = body if index == original else bare.copy()
            if index != original:
                result.alpha_composite(head, dest=xy)
            canvas = Image.new("RGBA", (364, 498))
            canvas.paste(result.resize((316, 498), NEAREST), (24, 0))
            canvas.save(DEST / f"{actor}-{outfit}-{index}.png")


def prepare_action(key, path, actor, outfit, hat, use_png_frames=False):
    source = Image.open(ROOT / "gif" / path)
    def read_frame(index):
        if use_png_frames:
            with Image.open((ROOT / "gif" / path).with_name(f"frame_{index+1}.png")) as png:
                return cutout(png)
        return cutout(source)
    first = read_frame(0)
    left, top, right, bottom = first.getbbox()
    reference = Image.open(DEST / f"{actor}-{outfit}-{hat}.png").getbbox()
    scale = (reference[3]-reference[1]) / (bottom-top)
    width, height = round(first.width*scale), round(first.height*scale)
    # Anchor the entire sequence using the resting frame, preserving motion.
    x = round((reference[0]+reference[2]) / 2 - (left+right)*scale/2)
    y = round(reference[3] - bottom*scale)
    durations = []
    for i in range(source.n_frames):
        source.seek(i)
        frame = (first if i == 0 else read_frame(i)).resize((width, height), NEAREST)
        canvas = Image.new("RGBA", (364, 498))
        canvas.alpha_composite(frame, dest=(x, y))
        canvas.save(DEST / f"{key}-{i}.png")
        durations.append(source.info.get("duration", 140))
    return {"prefix": key, "durations": durations}


def school_hammer(hat, template):
    """Pivot the uniform forearm and the original prop together at the elbow."""
    body = Image.open(DEST / f"Seeky-6-{hat}.png").convert("RGBA")
    mask = Image.new("L", body.size)
    draw = ImageDraw.Draw(mask)
    draw.polygon([(114, 307), (140, 307), (138, 320), (136, 338),
                  (137, 362), (111, 362)], fill=255)
    forearm = Image.new("RGBA", body.size)
    forearm.paste(body, mask=mask)
    body.paste((0, 0, 0, 0), mask=mask)

    original = Image.open(DEST / "soft-0.png")
    prop_mask = Image.new("L", original.size)
    ImageDraw.Draw(prop_mask).polygon(
        [(68, 302), (120, 278), (132, 280), (142, 296), (142, 310),
         (127, 319), (133, 338), (122, 344), (106, 325), (85, 339),
         (75, 336), (67, 320)], fill=255)
    prop = Image.new("RGBA", original.size)
    prop.paste(original, mask=prop_mask)
    moving = Image.new("RGBA", body.size)
    prop = prop.rotate(82, NEAREST, center=(126, 342))
    moving.alpha_composite(prop, dest=(2, 7))
    moving.alpha_composite(forearm)
    prefix = f"soft-school-{hat}"
    for index, angle in enumerate((-28, -90, -65, -40, -78)):
        frame = body.copy()
        arm = moving.rotate(angle, NEAREST, center=(128, 307))
        frame.alpha_composite(arm)
        frame.save(DEST / f"{prefix}-{index}.png")
    return {"prefix": prefix, "durations": template["durations"]}


def prepare_actions():
    catalog = []
    for key, label, actor, path in [
        ("grimace", "做鬼脸", "Ocean", "做鬼脸/grimace_Ocean.gif"),
        ("ocean-hammer", "挥锤子", "Ocean", "ocean_hammer/ocean_hammer.gif"),
        ("hammer", "挥锤子", "Seeky", "挥锤子_第一版/hammer_seeky.gif"),
        ("soft", "轻挥小锤", "Seeky", "轻挥小锤子_第二版/soft_hammer.gif"),
    ]:
        sample = prepare_action(key, path, actor, 4, 3, use_png_frames=(key == "ocean-hammer"))
        variants = {"4-3": sample}
        if key == "soft":
            for hat in range(1, 5):
                variants[f"6-{hat}"] = school_hammer(hat, sample)
        catalog.append(dict(key=key, label=label, actor=actor, variants=variants))
    (DEST / "actions.js").write_text(
        "const actionCatalog = " + json.dumps(catalog, ensure_ascii=False, indent=2)
        + ";\n", encoding="utf-8")


if __name__ == "__main__":
    DEST.mkdir(exist_ok=True)
    for actor in ACTORS:
        prepare_actor(actor)
    prepare_actions()
    prepare_faces(DEST)

