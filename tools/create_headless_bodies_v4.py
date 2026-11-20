#!/usr/bin/env python3
"""
为每个服装变体创建无头身体精灵图（v4 - 颜色识别 + 连通区域）。

策略：
1. 使用手绘图层作为初始遮罩
2. 在头部区域（y < 260）扩展遮罩，包括：
   - 头发颜色（深色）
   - 耳朵颜色（粉色/白色/肤色）
   - 帽子/花冠颜色
3. 排除明显的衣服颜色
4. 保留背包带等身体细节
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "studio-assets"
LAYERS = ROOT / "studio-assets" / "layers"


def load_config(character):
    """加载角色配置。"""
    config_path = LAYERS / character / "layers.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def is_head_color(r, g, b, character):
    """判断像素是否是头部相关颜色。"""
    # 头发（深色）
    if r < 100 and g < 100 and b < 100:
        return True
    
    # 脸部肤色
    if 200 < r < 260 and 150 < g < 220 and 140 < b < 200:
        return True
    
    # 耳朵/帽子颜色
    if character == "Ocean":
        # Ocean 猫耳：深色（已被头发覆盖）
        # 桃子帽：粉色
        if r > 200 and g > 140 and b > 140 and r > g and r - b < 60:
            return True
        # 花冠：各种颜色
        if r > 180 or g > 180 or b > 180:
            return True
    else:  # Seeky
        # Seeky 兔耳：粉色/白色
        if (r > 200 and g > 150 and b > 150) or (r > 220 and g > 220 and b > 220):
            return True
        # 桃子帽/花冠
        if r > 180 or g > 180 or b > 180:
            return True
    
    return False


def is_body_color(r, g, b):
    """判断像素是否是明显的身体/衣服颜色。"""
    # 衣服通常是饱和色
    # 红色T恤
    if r > 180 and g < 120 and b < 120:
        return True
    # 蓝色背心/裤子
    if r < 150 and g < 180 and b > 150:
        return True
    # 黄色/橙色背包带
    if r > 200 and g > 160 and b < 150 and g > b:
        return True
    
    return False


def create_headless_body(character, outfit, hat):
    """
    为 outfit×hat 组合创建无头身体（颜色识别版）。
    """
    # 加载原始精灵
    sprite_path = ASSETS / f"{character}-{outfit}-{hat}.png"
    if not sprite_path.exists():
        return None, f"sprite not found: {sprite_path.name}"
    
    sprite = Image.open(sprite_path).convert('RGBA')
    sprite_arr = np.array(sprite).copy()
    
    # 创建遮罩
    mask = np.zeros((498, 364), dtype=bool)
    
    # 加载手绘图层作为参考
    config = load_config(character)
    base_path = LAYERS / character
    
    # 1. 标记手绘图层的像素
    for layer_file in [config['layers']['face'], config['layers']['hair']]:
        layer_path = base_path / layer_file
        if layer_path.exists():
            layer = Image.open(layer_path).convert('RGBA')
            layer_arr = np.array(layer)
            mask |= (layer_arr[:, :, 3] > 128)
    
    # 2. 标记头饰图层
    headwear_map = {1: 'default-hair', 2: 'flower', 3: 'animal-ears', 4: 'peach-hat'}
    headwear_name = headwear_map.get(hat, 'default-hair')
    headwear_files = config['layers']['headwear'].get(headwear_name, [])
    
    if isinstance(headwear_files, list):
        for hw_file in headwear_files:
            if hw_file:
                hw_path = base_path / hw_file
                if hw_path.exists():
                    hw = Image.open(hw_path).convert('RGBA')
                    hw_arr = np.array(hw)
                    mask |= (hw_arr[:, :, 3] > 128)
    
    # 3. 在头部区域（y < 260）扩展遮罩，基于颜色
    head_cutoff = 260
    
    for y in range(0, head_cutoff):
        for x in range(364):
            if mask[y, x]:
                continue  # 已经标记
            
            pixel = sprite_arr[y, x]
            if pixel[3] < 128:
                continue  # 透明
            
            r, g, b = pixel[:3]
            
            # 排除明显的衣服
            if is_body_color(r, g, b):
                continue
            
            # 检查是否是头部颜色
            if is_head_color(r, g, b, character):
                mask[y, x] = True
    
    # 4. 应用遮罩
    sprite_arr[mask, 3] = 0
    
    # 验证肩膀区域
    shoulder_region = sprite_arr[235:260, 60:300, :]
    shoulder_pixels = np.sum(shoulder_region[:, :, 3] > 128)
    
    # 检查粉色/白色残留
    pink_count = 0
    white_count = 0
    
    for y in range(235, 260):
        for x in range(60, 300):
            if sprite_arr[y, x, 3] > 128:
                r, g, b = sprite_arr[y, x, :3]
                is_pink = (r > 200 and g > 150 and b > 150 and r > g)
                is_white = (r > 220 and g > 220 and b > 220)
                if is_pink:
                    pink_count += 1
                elif is_white:
                    white_count += 1
    
    status = f"shoulder: {shoulder_pixels} px"
    if pink_count > 50 or white_count > 50:
        status += f", {pink_count}pink+{white_count}white RESIDUE"
    
    return Image.fromarray(sprite_arr), status


def main():
    """主函数。"""
    print("=" * 60)
    print("创建无头身体精灵图 (v4 - 颜色识别)")
    print("=" * 60)
    print()
    
    all_issues = {}
    
    for character in ["Ocean", "Seeky"]:
        print(f"处理 {character}...")
        output_dir = LAYERS / character / "body"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        issues = []
        
        for outfit in range(1, 7):
            for hat in range(1, 5):
                headless, status = create_headless_body(character, outfit, hat)
                if headless:
                    output_path = output_dir / f"outfit-{outfit}-hat-{hat}.png"
                    headless.save(output_path)
                    
                    if "RESIDUE" in status:
                        issues.append(f"outfit-{outfit}-hat-{hat}: {status}")
        
        print(f"  生成了 24 个无头身体精灵图")
        
        if issues:
            print(f"  ⚠️  {len(issues)} 个有残留:")
            for issue in issues[:3]:
                print(f"    - {issue}")
            if len(issues) > 3:
                print(f"    ... 还有 {len(issues) - 3} 个")
            all_issues[character] = issues
        else:
            print(f"  ✓ 所有身体层通过检查")
    
    print()
    print("=" * 60)
    print("完成")
    print("=" * 60)
    
    if all_issues:
        total_issues = sum(len(v) for v in all_issues.values())
        print(f"\n总共 {total_issues} 个组合需要手动检查")
    else:
        print("\n✓ 所有组合通过自动检查")


if __name__ == "__main__":
    main()
