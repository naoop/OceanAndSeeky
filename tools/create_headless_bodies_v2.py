#!/usr/bin/env python3
"""
为每个服装变体创建无头身体精灵图（改进版）。

使用智能遮罩而非简单水平切割，精确擦除旧头部像素。
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "studio-assets"
LAYERS = ROOT / "studio-assets" / "layers"


def create_head_mask(character, outfit, hat):
    """
    创建头部遮罩，标记所有需要擦除的旧头部像素。
    
    策略：
    1. 对比 hat=3（动物耳朵）变体和 hat=1（默认发型）变体
    2. 使用连通区域分析找到头部区域（脖子以上）
    3. 包括耳朵的完整形状（包括垂到肩膀的部分）
    """
    sprite_path = ASSETS / f"{character}-{outfit}-{hat}.png"
    if not sprite_path.exists():
        return None
    
    sprite = Image.open(sprite_path).convert("RGBA")
    sprite_arr = np.array(sprite)
    
    # 创建遮罩
    mask = np.zeros(sprite.size[::-1], dtype=np.uint8)
    
    # 策略1：擦除所有脖子以上的像素
    # 但要更精确地定位脖子位置
    neck_y = 235
    
    # 策略2：找到所有头部相关的像素
    # 头部区域：上半部分 + 耳朵/头发延伸
    
    # 首先标记明确的头部区域（y < 220）
    for y in range(0, 220):
        for x in range(sprite.size[0]):
            if sprite_arr[y, x, 3] > 128:
                mask[y, x] = 255
    
    # 然后在脖子附近区域（y=220-260）进行更精细的分析
    # 识别头发、耳朵等延伸部分
    for y in range(220, 260):
        for x in range(sprite.size[0]):
            pixel = sprite_arr[y, x]
            if pixel[3] < 128:
                continue
            
            r, g, b = pixel[:3]
            
            # 检查是否是头发颜色（深色）
            is_hair = (r < 100 and g < 100 and b < 100)
            
            # 检查是否是耳朵颜色
            # Ocean 猫耳：深色
            # Seeky 兔耳：粉色/白色
            is_ocean_ear = (character == "Ocean" and r < 120 and g < 120 and b < 120)
            is_seeky_ear = (character == "Seeky" and 
                          ((r > 200 and g > 150 and b > 150) or  # 粉色
                           (r > 220 and g > 220 and b > 220)))   # 白色
            
            # 检查是否是帽子/花冠（各种颜色）
            # 如果在头部区域正下方，且颜色不像衣服，标记为头部
            is_accessory = False
            if x > 100 and x < 260:  # 头部水平范围
                # 检查上方是否有头部像素
                if y > 10 and mask[y-10:y, x].any():
                    # 排除明显的衣服颜色
                    is_red_shirt = (r > 180 and g < 100 and b < 100)
                    is_blue_vest = (r < 150 and g < 180 and b > 150)
                    if not (is_red_shirt or is_blue_vest):
                        is_accessory = True
            
            if is_hair or is_ocean_ear or is_seeky_ear or is_accessory:
                mask[y, x] = 255
    
    # 使用连通区域分析扩展遮罩，确保完整覆盖耳朵
    from scipy import ndimage
    # 扩展遮罩以包括相邻像素
    mask = ndimage.binary_dilation(mask, iterations=2).astype(np.uint8) * 255
    
    # 但要保护衣服细节（背包带等）
    # 背包带通常在肩膀位置，颜色明亮
    for y in range(220, 260):
        for x in range(sprite.size[0]):
            pixel = sprite_arr[y, x]
            if pixel[3] < 128:
                continue
            
            r, g, b = pixel[:3]
            
            # Ocean outfit-1 的黄色/粉色背包带
            is_backpack_strap = (
                (r > 200 and g > 150 and b < 150) or  # 粉色
                (r > 200 and g > 180 and b < 100)     # 黄色
            )
            
            # 如果是背包带且在合理位置（肩膀外侧），取消标记
            if is_backpack_strap and (x < 80 or x > 280):
                mask[y, x] = 0
    
    return mask


def create_headless_body(character, outfit, hat):
    """创建无头身体精灵图（改进版）。"""
    sprite_path = ASSETS / f"{character}-{outfit}-{hat}.png"
    if not sprite_path.exists():
        return None
    
    sprite = Image.open(sprite_path).convert("RGBA")
    sprite_arr = np.array(sprite)
    
    # 创建头部遮罩
    mask = create_head_mask(character, outfit, hat)
    if mask is None:
        return None
    
    # 应用遮罩
    sprite_arr[:, :, 3] = np.where(mask > 128, 0, sprite_arr[:, :, 3])
    
    return Image.fromarray(sprite_arr)


def main():
    """主函数。"""
    print("=" * 60)
    print("创建无头身体精灵图（改进版 - 智能遮罩）")
    print("=" * 60)
    print()
    
    # 检查是否有 scipy
    try:
        import scipy
    except ImportError:
        print("警告: scipy 未安装，使用简化版本")
        print("建议: pip install scipy")
    
    for character in ["Ocean", "Seeky"]:
        print(f"处理 {character}...")
        output_dir = LAYERS / character / "body"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        count = 0
        issues = []
        
        for outfit in range(1, 7):
            for hat in range(1, 5):
                headless = create_headless_body(character, outfit, hat)
                if headless:
                    output_path = output_dir / f"outfit-{outfit}-hat-{hat}.png"
                    headless.save(output_path)
                    count += 1
                    
                    # 验证肩膀区域
                    arr = np.array(headless)
                    shoulder_region = arr[235:250, 60:300, :]
                    residue = np.sum(shoulder_region[:, :, 3] > 128)
                    
                    if residue > 100:  # 超过 100 个像素可能有问题
                        issues.append(f"outfit-{outfit}-hat-{hat}: {residue} 残留像素")
        
        print(f"  生成了 {count} 个无头身体精灵图")
        if issues:
            print(f"  ⚠️  发现 {len(issues)} 个可能的问题:")
            for issue in issues[:5]:
                print(f"    - {issue}")
        else:
            print(f"  ✓ 所有身体层通过初步检查")
    
    print()
    print("=" * 60)
    print("✓ 完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
