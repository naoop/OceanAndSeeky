#!/usr/bin/env python3
"""
使用图层系统构建展示资源。

图层堆叠（从下到上）：
1. body: 身体+服装+后发
2. face: 皮肤+面部轮廓（无五官）
3. features: 眉毛、眼睛、鼻子、嘴、腮红
4. hair-front: 前发/刘海
5. headwear: 头饰/配件
"""
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
LAYERS_SRC = ROOT / "assets-src" / "layers"
DEST = ROOT / "studio-assets"
CONFIG_FILE = Path(__file__).parent / "layers_config.json"
CANVAS_SIZE = (364, 498)


def load_config():
    """加载图层配置。"""
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def composite_layers(character, outfit, hat, expression=None):
    """
    合成图层生成最终图像。
    
    参数:
        character: 角色名称 (Ocean/Seeky)
        outfit: 服装编号 (1-6)
        hat: 头饰编号 (1-4)
        expression: 表情键名 (可选)
    
    返回:
        PIL.Image: 合成后的图像
    """
    result = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    
    # 1. 身体层
    body_path = LAYERS_SRC / character / "body" / f"outfit-{outfit}-hat-{hat}.png"
    if body_path.exists():
        body = Image.open(body_path).convert("RGBA")
        result = Image.alpha_composite(result, body)
    
    # 2. 面部层
    face_path = LAYERS_SRC / character / "face" / "default.png"
    if face_path.exists():
        face = Image.open(face_path).convert("RGBA")
        result = Image.alpha_composite(result, face)
    
    # 3. 五官层（如果有表情）
    if expression:
        features_path = LAYERS_SRC / character / "features" / f"{expression}.png"
        if features_path.exists():
            features = Image.open(features_path).convert("RGBA")
            result = Image.alpha_composite(result, features)
    
    # 4. 前发层
    hair_path = LAYERS_SRC / character / "hair-front" / f"hair-{hat}.png"
    if hair_path.exists():
        hair_front = Image.open(hair_path).convert("RGBA")
        result = Image.alpha_composite(result, hair_front)
    
    # 5. 头饰层
    config = load_config()
    headwear_name = config["headwear"][str(hat)]["name"]
    headwear_path = LAYERS_SRC / character / "headwear" / f"{headwear_name}.png"
    if headwear_path.exists():
        headwear = Image.open(headwear_path).convert("RGBA")
        result = Image.alpha_composite(result, headwear)
    
    return result


def generate_character_portraits():
    """生成所有角色静态图（服装×头饰组合）。"""
    print("生成角色静态图...")
    
    for character in ["Ocean", "Seeky"]:
        print(f"  {character}:")
        count = 0
        for outfit in range(1, 7):
            for hat in range(1, 5):
                portrait = composite_layers(character, outfit, hat, expression=None)
                output_path = DEST / f"{character}-{outfit}-{hat}.png"
                portrait.save(output_path)
                count += 1
        print(f"    生成了 {count} 个静态图")


def generate_head_icons():
    """生成头部图标。"""
    print("生成头部图标...")
    
    for character in ["Ocean", "Seeky"]:
        for hat in range(1, 5):
            # 使用前发+头饰合成头部图标
            icon = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
            
            # 面部
            face_path = LAYERS_SRC / character / "face" / "default.png"
            if face_path.exists():
                face = Image.open(face_path).convert("RGBA")
                icon = Image.alpha_composite(icon, face)
            
            # 前发
            hair_path = LAYERS_SRC / character / "hair-front" / f"hair-{hat}.png"
            if hair_path.exists():
                hair_front = Image.open(hair_path).convert("RGBA")
                icon = Image.alpha_composite(icon, hair_front)
            
            # 头饰
            config = load_config()
            headwear_name = config["headwear"][str(hat)]["name"]
            headwear_path = LAYERS_SRC / character / "headwear" / f"{headwear_name}.png"
            if headwear_path.exists():
                headwear = Image.open(headwear_path).convert("RGBA")
                icon = Image.alpha_composite(icon, headwear)
            
            # 裁剪并缩放
            bbox = icon.getbbox()
            if bbox:
                icon = icon.crop(bbox)
                icon.thumbnail((110, 110), Image.Resampling.NEAREST)
            
            output_path = DEST / f"{character}-head-{hat}.png"
            icon.save(output_path)
    
    print("    生成了 8 个头部图标")


def generate_expression_overlays():
    """生成表情叠加层图标。"""
    print("生成表情图标...")
    
    config = load_config()
    
    for character, expressions in config["expressions"].items():
        for expr in expressions:
            key = expr["key"]
            
            # 表情图标：面部+五官+前发（使用动物耳朵=3）
            icon = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
            
            # 面部
            face_path = LAYERS_SRC / character / "face" / "default.png"
            if face_path.exists():
                face = Image.open(face_path).convert("RGBA")
                icon = Image.alpha_composite(icon, face)
            
            # 五官
            features_path = LAYERS_SRC / character / "features" / f"{key}.png"
            if features_path.exists():
                features = Image.open(features_path).convert("RGBA")
                icon = Image.alpha_composite(icon, features)
            
            # 前发（使用动物耳朵的前发）
            hair_path = LAYERS_SRC / character / "hair-front" / "hair-3.png"
            if hair_path.exists():
                hair_front = Image.open(hair_path).convert("RGBA")
                icon = Image.alpha_composite(icon, hair_front)
            
            # 裁剪到头部区域
            bbox = icon.getbbox()
            if bbox:
                # 只保留头部区域
                x1, y1, x2, y2 = bbox
                # 扩展一点边距
                padding = 10
                crop_box = (
                    max(0, x1 - padding),
                    max(0, y1 - padding),
                    min(CANVAS_SIZE[0], x2 + padding),
                    min(CANVAS_SIZE[1], y2 + padding)
                )
                icon = icon.crop(crop_box)
            
            # 保存图标
            output_path = DEST / f"face-{key}-icon.png"
            icon.save(output_path)
    
    print(f"    生成了 {sum(len(exprs) for exprs in config['expressions'].values())} 个表情图标")


def generate_faces_js():
    """生成 faces.js 配置文件。"""
    print("生成 faces.js...")
    
    config = load_config()
    
    face_catalog = {}
    for character, expressions in config["expressions"].items():
        entries = []
        for expr in expressions:
            entries.append({
                "prefix": f"face-{expr['key']}",
                "label": expr["label"]
            })
        face_catalog[character] = entries
    
    js_content = "const faceCatalog = " + json.dumps(face_catalog, ensure_ascii=False, indent=2) + ";\n"
    
    output_path = DEST / "faces.js"
    output_path.write_text(js_content, encoding="utf-8")
    
    print(f"    保存: {output_path}")


def main():
    """主函数。"""
    print("=" * 50)
    print("基于图层系统生成展示资源")
    print("=" * 50)
    print()
    
    DEST.mkdir(exist_ok=True)
    
    generate_character_portraits()
    print()
    
    generate_head_icons()
    print()
    
    generate_expression_overlays()
    print()
    
    generate_faces_js()
    print()
    
    print("=" * 50)
    print("✓ 资源生成完成")
    print("=" * 50)
    print()
    print("注意：动作动画仍使用原有的全帧精灵图。")
    print("图层系统用于静态角色和表情展示。")


if __name__ == "__main__":
    main()
