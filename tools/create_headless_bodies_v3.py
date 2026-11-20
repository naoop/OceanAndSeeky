#!/usr/bin/env python3
"""
为每个服装变体创建无头身体精灵图（v3 - 每个 outfit×hat 使用对应原始精灵）。

策略：
1. 加载对应的原始精灵（Character-outfit-hat.png）
2. 加载手绘的 face, hair, headwear 图层
3. 创建头部遮罩 = face + hair + headwear 的所有像素
4. 从原始精灵中擦除遮罩覆盖的区域
5. 保留身体（衣服细节如背包带）
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


def create_head_mask(character, hat):
    """
    创建头部遮罩，包含所有头部图层的像素。
    
    返回: numpy array (bool mask)
    """
    config = load_config(character)
    base_path = LAYERS / character
    
    # 创建遮罩（364×498）
    mask = np.zeros((498, 364), dtype=bool)
    
    # 1. Face layer
    face_path = base_path / config['layers']['face']
    if face_path.exists():
        face = Image.open(face_path).convert('RGBA')
        face_arr = np.array(face)
        mask |= (face_arr[:, :, 3] > 128)
    
    # 2. Hair layer
    hair_path = base_path / config['layers']['hair']
    if hair_path.exists():
        hair = Image.open(hair_path).convert('RGBA')
        hair_arr = np.array(hair)
        mask |= (hair_arr[:, :, 3] > 128)
    
    # 3. Headwear layers
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
    
    return mask


def create_headless_body(character, outfit, hat):
    """
    为 outfit×hat 组合创建无头身体。
    
    从原始精灵中擦除 face + hair + headwear 的所有像素。
    """
    # 加载原始精灵
    sprite_path = ASSETS / f"{character}-{outfit}-{hat}.png"
    if not sprite_path.exists():
        return None, f"sprite not found: {sprite_path.name}"
    
    sprite = Image.open(sprite_path).convert('RGBA')
    sprite_arr = np.array(sprite)
    
    # 创建头部遮罩
    head_mask = create_head_mask(character, hat)
    
    # 从精灵中擦除头部
    sprite_arr[head_mask, 3] = 0
    
    # 验证肩膀区域
    shoulder_region = sprite_arr[235:260, 60:300, :]
    shoulder_pixels = np.sum(shoulder_region[:, :, 3] > 128)
    
    # 检查是否有耳朵颜色残留
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
    
    status = f"ok (shoulder: {shoulder_pixels} pixels"
    if pink_count > 50:
        status += f", {pink_count} pink RESIDUE"
    if white_count > 50:
        status += f", {white_count} white RESIDUE"
    status += ")"
    
    return Image.fromarray(sprite_arr), status


def main():
    """主函数。"""
    print("=" * 60)
    print("创建无头身体精灵图 (v3 - 基于手绘图层遮罩)")
    print("=" * 60)
    print()
    
    all_issues = {}
    
    for character in ["Ocean", "Seeky"]:
        print(f"处理 {character}...")
        output_dir = LAYERS / character / "body"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        count = 0
        issues = []
        
        for outfit in range(1, 7):
            for hat in range(1, 5):
                headless, status = create_headless_body(character, outfit, hat)
                if headless:
                    output_path = output_dir / f"outfit-{outfit}-hat-{hat}.png"
                    headless.save(output_path)
                    count += 1
                    
                    if "RESIDUE" in status:
                        issues.append((outfit, hat, status))
                        print(f"  ⚠️  outfit-{outfit}-hat-{hat}: {status}")
                else:
                    print(f"  ✗ outfit-{outfit}-hat-{hat}: {status}")
        
        print(f"  生成了 {count} 个无头身体精灵图")
        
        if issues:
            print(f"  ⚠️  {len(issues)} 个可能有问题")
            all_issues[character] = issues
        else:
            print(f"  ✓ 所有身体层通过初步检查")
        
        print()
    
    print("=" * 60)
    print("完成")
    print("=" * 60)
    
    if all_issues:
        print("\n需要检查的组合:")
        for char, issues in all_issues.items():
            print(f"{char}:")
            for outfit, hat, status in issues:
                print(f"  - outfit-{outfit}-hat-{hat}: {status}")


if __name__ == "__main__":
    main()
