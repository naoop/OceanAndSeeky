"""从定稿的美术素材重建展示用图像资源。"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

# 支持从项目根目录运行
sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_faces import prepare_faces

# 路径配置
ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "assets-src" / "makeup" / "SeekyOcean妆造定稿"
GIF_SRC = ROOT / "assets-src" / "gif"
DEST = ROOT / "studio-assets"
CONFIG_FILE = Path(__file__).parent / "action_config.json"

# 常量配置
CANVAS_WIDTH = 364
CANVAS_HEIGHT = 498
ACTORS = ("Ocean", "Seeky")
ORIGINAL_HEADS = (4, 1, 2, 3, 1, 1)  # 每套服装的原始头饰索引
NEAREST = Image.Resampling.NEAREST


def load_config():
    """加载动作配置文件。"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"错误: 找不到配置文件 {CONFIG_FILE}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"错误: 配置文件格式错误: {e}", file=sys.stderr)
        sys.exit(1)


def cutout(source):
    """通过漫水填充去除白色背景，保持角色透明。"""
    image = source.convert("RGBA")
    ImageDraw.floodfill(image, (0, 0), (255, 255, 255, 0), thresh=12)
    return image


def head_position(body, head):
    """配准绘制的头发和面部像素到完整尺寸的原始图像。"""
    sample = np.asarray(head)
    ys, xs = np.where((sample[:, :, 3] == 255) & (sample[:, :, 0] < 130))
    ys, xs = ys[::137], xs[::137]
    pixels = np.asarray(body)
    
    def error(offset):
        dx, dy = offset
        return np.abs(pixels[ys + dy, xs + dx, :3].astype(int)
                      - sample[ys, xs, :3]).mean()
    
    # 粗略搜索
    coarse = min(((x, y) for x in range(-18, 40, 4)
                  for y in range(-22, 110, 4)), key=error)
    cx, cy = coarse
    # 精细搜索
    return min(((x, y) for x in range(cx-4, cx+5)
                for y in range(cy-4, cy+5)), key=error)


def image_hash(img):
    """计算图像内容的哈希值用于去重。"""
    return hashlib.md5(img.tobytes()).hexdigest()


def prepare_actor(actor):
    """为指定角色准备所有服装和头饰组合的静态图像。"""
    print(f"处理角色 {actor}...")
    heads = {}
    
    # 加载并处理所有头饰
    for index in range(1, 5):
        path_pattern = f"{index}_*_{actor}.png"
        matches = list((ART / "头部").glob(path_pattern))
        if not matches:
            print(f"错误: 找不到匹配 {path_pattern} 的头部文件", file=sys.stderr)
            sys.exit(1)
        path = matches[0]
        head = cutout(Image.open(path))
        heads[index] = head
        
        # 生成头饰缩略图
        icon = head.crop(head.getbbox())
        icon.thumbnail((110, 110), NEAREST)
        icon.save(DEST / f"{actor}-head-{index}.png")
    
    # 处理每套服装
    for outfit, original in enumerate(ORIGINAL_HEADS, 1):
        path_pattern = f"{outfit:02}_*_{actor}.png"
        matches = list((ART / "造型").glob(path_pattern))
        if not matches:
            print(f"错误: 找不到匹配 {path_pattern} 的造型文件", file=sys.stderr)
            sys.exit(1)
        path = matches[0]
        body = cutout(Image.open(path))
        xy = head_position(body, heads[original])
        
        # 创建无头版本用于换头
        bare = body.copy()
        bare.paste((0, 0, 0, 0), xy + (xy[0]+928, xy[1]+904),
                   heads[original].getchannel("A"))
        # 清除头发和花朵之间的封闭背景岛
        bare.paste((0, 0, 0, 0), (0, 0, bare.width, xy[1] + 650))
        
        # 为每个头饰生成组合图
        for index, head in heads.items():
            result = body if index == original else bare.copy()
            if index != original:
                result.alpha_composite(head, dest=xy)
            canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT))
            canvas.paste(result.resize((316, CANVAS_HEIGHT), NEAREST), (24, 0))
            canvas.save(DEST / f"{actor}-{outfit}-{index}.png")


def prepare_action(action_config):
    """根据配置准备单个动作的动画帧。"""
    key = action_config["key"]
    label = action_config["label"]
    actor = action_config["actor"]
    path = action_config["source_path"]
    outfit = action_config["outfit"]
    hat = action_config["hat"]
    use_png_frames = action_config.get("use_png_frames", False)
    durations = action_config.get("durations", [])
    
    print(f"处理动作 {label} ({key})...")
    
    gif_path = GIF_SRC / path
    if not gif_path.exists():
        print(f"错误: 找不到源文件 {gif_path}", file=sys.stderr)
        return None
    
    source = Image.open(gif_path)
    
    def read_frame(index):
        if use_png_frames:
            png_path = gif_path.with_name(f"frame_{index+1}.png")
            if not png_path.exists():
                print(f"错误: 找不到 PNG 帧 {png_path}", file=sys.stderr)
                sys.exit(1)
            with Image.open(png_path) as png:
                return cutout(png)
        return cutout(source)
    
    first = read_frame(0)
    left, top, right, bottom = first.getbbox()
    reference = Image.open(DEST / f"{actor}-{outfit}-{hat}.png").getbbox()
    scale = (reference[3] - reference[1]) / (bottom - top)
    width, height = round(first.width * scale), round(first.height * scale)
    
    # 使用静止帧作为锚点定位整个序列，保持运动一致
    x = round((reference[0] + reference[2]) / 2 - (left + right) * scale / 2)
    y = round(reference[3] - bottom * scale)
    
    frame_hashes = {}
    unique_frames = {}
    frame_mapping = []
    
    for i in range(source.n_frames):
        source.seek(i)
        frame = (first if i == 0 else read_frame(i)).resize((width, height), NEAREST)
        canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT))
        canvas.alpha_composite(frame, dest=(x, y))
        
        # 计算帧哈希用于去重
        frame_hash = image_hash(canvas)
        
        if frame_hash in frame_hashes:
            # 重复帧，记录映射
            frame_mapping.append(frame_hashes[frame_hash])
            print(f"  第 {i} 帧是第 {frame_hashes[frame_hash]} 帧的重复")
        else:
            # 新帧，保存
            frame_hashes[frame_hash] = i
            unique_frames[i] = canvas
            canvas.save(DEST / f"{key}-{i}.png")
            frame_mapping.append(i)
        
        # 使用配置的持续时间或从 GIF 读取
        if not durations:
            durations.append(source.info.get("duration", 140))
    
    return {
        "prefix": key,
        "durations": durations,
        "frame_mapping": frame_mapping if len(unique_frames) < len(frame_mapping) else None
    }


def school_hammer(hat, template):
    """为校服生成挥锤动作的变体（旋转前臂和道具）。"""
    body = Image.open(DEST / f"Seeky-6-{hat}.png").convert("RGBA")
    mask = Image.new("L", body.size)
    draw = ImageDraw.Draw(mask)
    
    # 前臂遮罩多边形
    draw.polygon([(114, 307), (140, 307), (138, 320), (136, 338),
                  (137, 362), (111, 362)], fill=255)
    forearm = Image.new("RGBA", body.size)
    forearm.paste(body, mask=mask)
    body.paste((0, 0, 0, 0), mask=mask)

    # 提取小锤道具
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
    
    # 为每帧生成不同角度
    for index, angle in enumerate((-28, -90, -65, -40, -78)):
        frame = body.copy()
        arm = moving.rotate(angle, NEAREST, center=(128, 307))
        frame.alpha_composite(arm)
        frame.save(DEST / f"{prefix}-{index}.png")
    
    return {"prefix": prefix, "durations": template["durations"]}


def prepare_actions(action_filter=None):
    """准备所有动作或指定的动作。"""
    config = load_config()
    catalog = []
    
    actions_to_process = config["actions"]
    if action_filter:
        actions_to_process = [a for a in actions_to_process if a["key"] == action_filter]
        if not actions_to_process:
            print(f"错误: 找不到动作 '{action_filter}'", file=sys.stderr)
            sys.exit(1)
    
    for action_config in actions_to_process:
        key = action_config["key"]
        label = action_config["label"]
        actor = action_config["actor"]
        
        sample = prepare_action(action_config)
        if sample is None:
            continue
            
        variants = {f"{action_config['outfit']}-{action_config['hat']}": sample}
        
        # 为校服生成特殊变体
        if action_config.get("generate_school_variants", False):
            for hat in range(1, 5):
                variants[f"6-{hat}"] = school_hammer(hat, sample)
        
        catalog.append(dict(key=key, label=label, actor=actor, variants=variants))
    
    # 只有处理所有动作时才重写 actions.js
    if not action_filter:
        (DEST / "actions.js").write_text(
            "const actionCatalog = " + json.dumps(catalog, ensure_ascii=False, indent=2)
            + ";\n", encoding="utf-8")
        print(f"已生成 {DEST / 'actions.js'}")


def main():
    """主函数，支持命令行参数。"""
    parser = argparse.ArgumentParser(
        description="从源素材生成像素小人展示资源",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python tools/prepare_assets.py              # 生成所有资源
  python tools/prepare_assets.py --action grimace    # 只生成做鬼脸动作
  python tools/prepare_assets.py --actors-only       # 只生成角色静态图
        """
    )
    parser.add_argument(
        "--action",
        help="只处理指定的动作（使用 key，如 'grimace'、'hammer'）"
    )
    parser.add_argument(
        "--actors-only",
        action="store_true",
        help="只生成角色静态图，不生成动作"
    )
    
    args = parser.parse_args()
    
    # 创建输出目录
    DEST.mkdir(exist_ok=True)
    
    print(f"输出目录: {DEST}")
    print()
    
    if not args.action:
        # 生成角色静态图
        for actor in ACTORS:
            prepare_actor(actor)
        print()
    
    if not args.actors_only:
        # 生成动作帧
        prepare_actions(args.action)
        print()
    
    if not args.action and not args.actors_only:
        # 生成表情叠加
        print("处理表情...")
        prepare_faces(DEST)
        print()
    
    print("✓ 资源生成完成")


if __name__ == "__main__":
    main()
