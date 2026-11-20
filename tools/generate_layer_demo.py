#!/usr/bin/env python3
"""
生成图层演示接触表，展示各个图层和最终合成效果。
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
LAYERS_SRC = ROOT / "assets-src" / "layers"
OUTPUT = ROOT / "exports"
CANVAS_SIZE = (364, 498)


def composite_layers(character, outfit, hat, expression=None):
    """
    合成图层生成最终图像。
    
    图层顺序（从下到上）：
    1. body: 身体+服装+后发
    2. face: 空白面部
    3. features: 五官
    4. hair-front: 前发
    5. headwear: 头饰
    """
    layers = []
    
    # 1. 身体层
    body_path = LAYERS_SRC / character / "body" / f"outfit-{outfit}-hat-{hat}.png"
    if body_path.exists():
        layers.append(("body", Image.open(body_path).convert("RGBA")))
    
    # 2. 面部层（总是包含）
    face_path = LAYERS_SRC / character / "face" / "default.png"
    if face_path.exists():
        layers.append(("face", Image.open(face_path).convert("RGBA")))
    
    # 3. 五官层（如果有表情）
    if expression:
        features_path = LAYERS_SRC / character / "features" / f"{expression}.png"
        if features_path.exists():
            layers.append(("features", Image.open(features_path).convert("RGBA")))
    
    # 4. 前发层
    hair_path = LAYERS_SRC / character / "hair-front" / f"hair-{hat}.png"
    if hair_path.exists():
        layers.append(("hair-front", Image.open(hair_path).convert("RGBA")))
    
    # 5. 头饰层
    headwear_names = {1: "default-hair", 2: "flower", 3: "animal-ears", 4: "peach-hat"}
    headwear_path = LAYERS_SRC / character / "headwear" / f"{headwear_names[hat]}.png"
    if headwear_path.exists():
        layers.append(("headwear", Image.open(headwear_path).convert("RGBA")))
    
    # 合成
    result = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    for name, layer in layers:
        result = Image.alpha_composite(result, layer)
    
    return result, layers


def create_contact_sheet():
    """创建接触表展示图层分解和合成效果。"""
    print("生成图层演示接触表...")
    
    OUTPUT.mkdir(exist_ok=True)
    
    # 为每个角色创建演示
    for character in ["Ocean", "Seeky"]:
        print(f"\n处理 {character}...")
        
        # 使用背带裤(4) + 动物耳朵(3) + 一个表情
        outfit, hat = 4, 3
        expression = "grimace-0" if character == "Ocean" else "hammer-0"
        
        # 获取合成结果和各个图层
        composite, layers = composite_layers(character, outfit, hat, expression)
        
        # 创建接触表：每个图层 + 最终合成
        # 布局：横向排列各图层，最右侧是合成结果
        num_layers = len(layers) + 1  # 各层 + 合成
        cell_width = CANVAS_SIZE[0]
        cell_height = CANVAS_SIZE[1]
        label_height = 40
        
        sheet_width = cell_width * num_layers
        sheet_height = cell_height + label_height
        
        sheet = Image.new("RGB", (sheet_width, sheet_height), (240, 240, 240))
        draw = ImageDraw.Draw(sheet)
        
        # 绘制各个图层
        for i, (name, layer) in enumerate(layers):
            x = i * cell_width
            
            # 在白色背景上绘制图层（用于透明度可视化）
            cell_bg = Image.new("RGB", CANVAS_SIZE, (255, 255, 255))
            cell_bg.paste(layer, (0, 0), layer)
            
            sheet.paste(cell_bg, (x, label_height))
            
            # 绘制标签
            label_text = {
                "body": "1. 身体层",
                "face": "2. 面部层",
                "features": "3. 五官层",
                "hair-front": "4. 前发层",
                "headwear": "5. 头饰层"
            }.get(name, name)
            
            # 使用默认字体
            bbox = draw.textbbox((0, 0), label_text)
            text_width = bbox[2] - bbox[0]
            text_x = x + (cell_width - text_width) // 2
            draw.text((text_x, 10), label_text, fill=(50, 50, 50))
        
        # 绘制最终合成
        composite_x = len(layers) * cell_width
        composite_bg = Image.new("RGB", CANVAS_SIZE, (230, 245, 235))  # 浅绿色背景
        composite_bg.paste(composite, (0, 0), composite)
        sheet.paste(composite_bg, (composite_x, label_height))
        
        # 合成标签
        label_text = "✓ 最终合成"
        bbox = draw.textbbox((0, 0), label_text)
        text_width = bbox[2] - bbox[0]
        text_x = composite_x + (cell_width - text_width) // 2
        draw.text((text_x, 10), label_text, fill=(40, 100, 60))
        
        # 保存
        output_path = OUTPUT / f"layer-breakdown-{character}.png"
        sheet.save(output_path)
        print(f"  保存: {output_path}")
        
        # 同时保存一个详细版本：显示多个表情
        print(f"  生成多表情对比...")
        expressions = ["grimace-0", "grimace-2", "grimace-4"] if character == "Ocean" else ["hammer-0", "hammer-2", "soft-0"]
        
        multi_width = cell_width * len(expressions)
        multi_height = cell_height + label_height
        
        multi_sheet = Image.new("RGB", (multi_width, multi_height), (240, 240, 240))
        multi_draw = ImageDraw.Draw(multi_sheet)
        
        for i, expr in enumerate(expressions):
            composite_expr, _ = composite_layers(character, outfit, hat, expr)
            x = i * cell_width
            
            # 绘制到背景上
            cell_bg = Image.new("RGB", CANVAS_SIZE, (230, 245, 235))
            cell_bg.paste(composite_expr, (0, 0), composite_expr)
            multi_sheet.paste(cell_bg, (x, label_height))
            
            # 标签
            label_text = expr.replace("grimace-", "表情").replace("hammer-", "表情").replace("soft-", "表情")
            bbox = multi_draw.textbbox((0, 0), label_text)
            text_width = bbox[2] - bbox[0]
            text_x = x + (cell_width - text_width) // 2
            multi_draw.text((text_x, 10), label_text, fill=(50, 50, 50))
        
        output_path = OUTPUT / f"expressions-{character}.png"
        multi_sheet.save(output_path)
        print(f"  保存: {output_path}")
    
    print("\n✓ 接触表生成完成")
    print(f"输出目录: {OUTPUT}")


if __name__ == "__main__":
    create_contact_sheet()
