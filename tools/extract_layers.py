#!/usr/bin/env python3
"""
从现有的合成精灵图中提取独立图层。

图层堆叠（从下到上）：
1. body: 身体+服装+后发
2. face: 皮肤+面部轮廓+人耳（无五官）
3. features: 眉毛、眼睛、鼻子、嘴、腮红等
4. hair-front: 前发/刘海（遮挡五官）
5. headwear: 头饰/配件（帽子、花、动物耳朵）
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "studio-assets"
LAYERS_SRC = ROOT / "assets-src" / "layers"
CANVAS_SIZE = (364, 498)

# 面部区域定义（手动校准）
FACE_REGIONS = {
    "Ocean": {
        "center": (181, 202),  # 面部中心
        "bbox": (130, 158, 232, 236),  # 面部边界框 (x1, y1, x2, y2)
        "bangs_y": 178,  # 刘海下边界
        "skin_sample": (182, 202),  # 采样皮肤颜色的位置
    },
    "Seeky": {
        "center": (181, 204),
        "bbox": (132, 160, 230, 238),
        "bangs_y": 180,
        "skin_sample": (182, 204),
    }
}

# 头饰名称映射
HEADWEAR_NAMES = {
    1: "default-hair",
    2: "flower",
    3: "animal-ears",
    4: "peach-hat"
}


def color_distance(c1, c2):
    """计算两个颜色的欧氏距离。"""
    return np.sqrt(np.sum((np.array(c1[:3]) - np.array(c2[:3])) ** 2))


def is_skin_color(pixel, skin_ref):
    """判断像素是否是皮肤色。"""
    if pixel[3] < 128:  # 半透明或透明
        return False
    # 皮肤色范围：偏粉的亮色
    r, g, b = pixel[:3]
    return r > 200 and g > 150 and b > 140 and color_distance(pixel, skin_ref) < 50


def is_hair_color(pixel):
    """判断像素是否是头发色（深色）。"""
    if pixel[3] < 128:
        return False
    r, g, b = pixel[:3]
    # 头发通常是深色
    return r < 100 or (r < 130 and g < 100)


def is_feature_pixel(pixel, blank_pixel):
    """判断像素是否是五官（与空白面部不同）。"""
    if pixel[3] < 10:
        return False
    # 墨线或深色（眉毛、眼睛、嘴巴轮廓）
    r, g, b = pixel[:3]
    if r < 150 and g < 100:
        return True
    # 或者与空白面部颜色差异明显
    if blank_pixel[3] > 0:
        return color_distance(pixel, blank_pixel) > 30
    return pixel[3] > 200


def extract_blank_face(character):
    """
    提取角色的空白面部（仅皮肤，无五官）。
    
    策略：从默认头像开始，将五官区域用周围皮肤色填充。
    """
    print(f"  提取 {character} 的空白面部...")
    
    # 使用背带裤+动物耳朵的默认组合
    base = Image.open(ASSETS / f"{character}-4-3.png").convert("RGBA")
    base_arr = np.array(base)
    
    region = FACE_REGIONS[character]
    x1, y1, x2, y2 = region["bbox"]
    
    # 采样皮肤颜色
    skin_sample_pos = region["skin_sample"]
    skin_color = tuple(base_arr[skin_sample_pos[1], skin_sample_pos[0]])
    
    # 创建空白面部
    blank = base.copy()
    blank_arr = np.array(blank)
    
    # 定义五官区域（眼睛、鼻子、嘴）- 这些需要被皮肤填充
    features_mask = Image.new("L", base.size, 0)
    draw = ImageDraw.Draw(features_mask)
    
    # 眼睛区域（两只眼睛）
    eye_y = region["center"][1] - 10
    left_eye_x = region["center"][0] - 27
    right_eye_x = region["center"][0] + 27
    
    for eye_x in [left_eye_x, right_eye_x]:
        # 椭圆形眼睛区域
        draw.ellipse(
            (eye_x - 18, eye_y - 12, eye_x + 18, eye_y + 12),
            fill=255
        )
    
    # 眉毛区域
    for eye_x in [left_eye_x, right_eye_x]:
        draw.rectangle(
            (eye_x - 20, eye_y - 22, eye_x + 20, eye_y - 13),
            fill=255
        )
    
    # 嘴巴区域
    mouth_y = region["center"][1] + 20
    draw.ellipse(
        (region["center"][0] - 18, mouth_y - 8, 
         region["center"][0] + 18, mouth_y + 10),
        fill=255
    )
    
    # 鼻子区域（小）
    nose_y = region["center"][1] + 5
    draw.ellipse(
        (region["center"][0] - 5, nose_y - 3,
         region["center"][0] + 5, nose_y + 3),
        fill=255
    )
    
    # 腮红区域
    for cheek_x in [region["center"][0] - 35, region["center"][0] + 35]:
        draw.ellipse(
            (cheek_x - 12, region["center"][1] + 8, 
             cheek_x + 12, region["center"][1] + 20),
            fill=255
        )
    
    features_mask_arr = np.array(features_mask)
    
    # 在五官区域用皮肤色填充
    mask_pixels = features_mask_arr > 128
    
    # 使用周围皮肤色的平均值
    face_region = blank_arr[y1:y2, x1:x2]
    skin_pixels = []
    
    for y in range(face_region.shape[0]):
        for x in range(face_region.shape[1]):
            pixel = face_region[y, x]
            if is_skin_color(pixel, skin_color):
                skin_pixels.append(pixel[:3])
    
    if skin_pixels:
        avg_skin = np.mean(skin_pixels, axis=0).astype(np.uint8)
        blank_arr[mask_pixels] = list(avg_skin) + [255]
    else:
        # 后备方案：使用采样的皮肤色
        blank_arr[mask_pixels] = list(skin_color[:3]) + [255]
    
    blank = Image.fromarray(blank_arr)
    output_path = LAYERS_SRC / character / "face" / "default.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    blank.save(output_path)
    
    print(f"    保存到: {output_path}")
    return blank


def extract_body_layer(character, outfit, hat):
    """
    提取身体层：服装+身体+后发，但用空白面部替换原面部。
    """
    base = Image.open(ASSETS / f"{character}-{outfit}-{hat}.png").convert("RGBA")
    blank_face = Image.open(LAYERS_SRC / character / "face" / "default.png").convert("RGBA")
    
    # 组合：基础精灵图 + 空白面部覆盖
    result = base.copy()
    result.paste(blank_face, (0, 0), blank_face)
    
    return result


def extract_features_from_expression(character, expr_prefix):
    """
    从表情叠加中提取五官层。
    
    策略：表情叠加 - 空白面部 = 五官（去除刘海部分）
    """
    expr_path = ASSETS / f"{expr_prefix}-plain.png"
    if not expr_path.exists():
        expr_path = ASSETS / f"{expr_prefix}.png"
    
    if not expr_path.exists():
        return None
    
    expr = Image.open(expr_path).convert("RGBA")
    blank_face = Image.open(LAYERS_SRC / character / "face" / "default.png").convert("RGBA")
    
    expr_arr = np.array(expr)
    blank_arr = np.array(blank_face)
    
    # 创建五官层
    features = Image.new("RGBA", expr.size, (0, 0, 0, 0))
    features_arr = np.array(features)
    
    region = FACE_REGIONS[character]
    x1, y1, x2, y2 = region["bbox"]
    bangs_y = region["bangs_y"]
    
    # 提取五官：表情叠加中与空白面部不同的像素
    for y in range(y1, y2):
        for x in range(x1, x2):
            expr_pixel = expr_arr[y, x]
            blank_pixel = blank_arr[y, x]
            
            # 跳过刘海区域（上方）
            if y < bangs_y:
                continue
            
            # 判断是否是五官像素
            if is_feature_pixel(expr_pixel, blank_pixel):
                features_arr[y, x] = expr_pixel
            elif expr_pixel[3] > 200 and not is_skin_color(expr_pixel, blank_pixel):
                # 非皮肤色的不透明像素也算五官（例如红色腮红）
                if color_distance(expr_pixel, blank_pixel) > 20:
                    features_arr[y, x] = expr_pixel
    
    return Image.fromarray(features_arr)


def extract_front_hair(character, hat):
    """
    提取前发/刘海层。
    
    策略：从基础精灵图中提取刘海区域的头发像素。
    """
    base = Image.open(ASSETS / f"{character}-4-{hat}.png").convert("RGBA")
    base_arr = np.array(base)
    
    region = FACE_REGIONS[character]
    bangs_y = region["bangs_y"]
    x1, y1, x2, y2 = region["bbox"]
    
    # 创建刘海层
    front_hair = Image.new("RGBA", base.size, (0, 0, 0, 0))
    front_hair_arr = np.array(front_hair)
    
    # 提取刘海区域的头发像素
    for y in range(y1, bangs_y + 10):
        for x in range(x1, x2):
            pixel = base_arr[y, x]
            if is_hair_color(pixel):
                front_hair_arr[y, x] = pixel
    
    return Image.fromarray(front_hair_arr)


def extract_headwear(character, hat):
    """
    提取头饰层。
    
    策略：对比当前头饰与默认发型（hat=1）的差异。
    """
    if hat == 1:
        # 默认发型没有额外头饰
        return Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    
    current = Image.open(ASSETS / f"{character}-4-{hat}.png").convert("RGBA")
    default = Image.open(ASSETS / f"{character}-4-1.png").convert("RGBA")
    
    current_arr = np.array(current)
    default_arr = np.array(default)
    
    # 创建头饰层
    headwear = Image.new("RGBA", current.size, (0, 0, 0, 0))
    headwear_arr = np.array(headwear)
    
    region = FACE_REGIONS[character]
    
    # 头饰通常在头部区域及以上
    for y in range(0, region["bbox"][1] + 50):
        for x in range(CANVAS_SIZE[0]):
            curr_pixel = current_arr[y, x]
            def_pixel = default_arr[y, x]
            
            # 如果当前像素与默认不同，且是不透明的，则是头饰
            if curr_pixel[3] > 128 and color_distance(curr_pixel, def_pixel) > 30:
                headwear_arr[y, x] = curr_pixel
            elif curr_pixel[3] > 128 and def_pixel[3] < 128:
                # 或者当前有像素但默认没有
                headwear_arr[y, x] = curr_pixel
    
    return Image.fromarray(headwear_arr)


def main():
    """主函数：提取所有图层。"""
    print("=" * 50)
    print("图层提取工具")
    print("=" * 50)
    print()
    
    # 为每个角色提取空白面部
    for character in ["Ocean", "Seeky"]:
        print(f"处理角色: {character}")
        blank_face = extract_blank_face(character)
        
        # 提取身体层（各种服装组合）
        print(f"  提取身体层...")
        for outfit in range(1, 7):
            for hat in range(1, 5):
                body = extract_body_layer(character, outfit, hat)
                output_path = LAYERS_SRC / character / "body" / f"outfit-{outfit}-hat-{hat}.png"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                body.save(output_path)
        print(f"    保存了 24 个身体层变体")
        
        # 提取前发层
        print(f"  提取前发层...")
        for hat in range(1, 5):
            front_hair = extract_front_hair(character, hat)
            output_path = LAYERS_SRC / character / "hair-front" / f"hair-{hat}.png"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            front_hair.save(output_path)
        print(f"    保存了 4 个前发变体")
        
        # 提取头饰层
        print(f"  提取头饰层...")
        for hat in range(1, 5):
            headwear = extract_headwear(character, hat)
            output_path = LAYERS_SRC / character / "headwear" / f"{HEADWEAR_NAMES[hat]}.png"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            headwear.save(output_path)
        print(f"    保存了 4 个头饰")
        
        print()
    
    # 提取表情五官层
    print("提取表情五官层...")
    
    with open(ASSETS / "faces.js", "r", encoding="utf-8") as f:
        content = f.read()
        json_str = content.split("const faceCatalog = ")[1].rstrip(";\n")
        face_catalog = json.loads(json_str)
    
    for character, expressions in face_catalog.items():
        print(f"  {character}:")
        for expr in expressions:
            prefix = expr["prefix"]
            label = expr["label"]
            
            features = extract_features_from_expression(character, prefix)
            if features:
                # 使用拼音或英文作为文件名
                safe_name = prefix.replace("face-", "")
                output_path = LAYERS_SRC / character / "features" / f"{safe_name}.png"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                features.save(output_path)
                print(f"    - {label} ({safe_name})")
    
    print()
    print("=" * 50)
    print("✓ 图层提取完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
