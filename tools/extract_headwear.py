#!/usr/bin/env python3
"""
提取头饰变体（hat 2-4：簪花、帽子等）。

通过对比头饰变体与动物耳朵变体的差异来提取头饰像素。
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "studio-assets"
LAYERS = ROOT / "studio-assets" / "layers"

# 头饰名称映射
HEADWEAR_NAMES = {
    2: "flower",      # 簪花
    3: "animal-ears", # 动物耳朵（已有）
    4: "peach-hat"    # 粉色蜜桃帽
}


def is_hair_color(pixel):
    """判断是否是头发颜色（深色）。"""
    if pixel[3] < 128:
        return False
    r, g, b = pixel[:3]
    # 头发是深色
    return r < 100 or (r < 130 and g < 100 and b < 120)


def is_ear_color(pixel):
    """判断是否是动物耳朵颜色。"""
    if pixel[3] < 128:
        return False
    r, g, b = pixel[:3]
    # 动物耳朵通常是深色（接近头发）或特定颜色
    return r < 120 and g < 120 and b < 120


def extract_headwear(character, hat):
    """
    提取头饰图层。
    
    策略：对比当前头饰变体与动物耳朵变体（hat=3）的差异。
    去除头发和耳朵颜色的像素，只保留头饰本身。
    """
    if hat == 3:
        # 动物耳朵已经有了
        return None, "already provided"
    
    # 读取当前头饰变体和动物耳朵变体（使用 outfit 4 作为参考）
    current_path = ASSETS / f"{character}-4-{hat}.png"
    ears_path = ASSETS / f"{character}-4-3.png"
    
    if not current_path.exists():
        return None, f"sprite not found: {current_path.name}"
    
    current = Image.open(current_path).convert("RGBA")
    ears = Image.open(ears_path).convert("RGBA")
    
    current_arr = np.array(current)
    ears_arr = np.array(ears)
    
    # 创建头饰图层
    headwear = Image.new("RGBA", current.size, (0, 0, 0, 0))
    headwear_arr = np.array(headwear)
    
    # 只在头部区域提取
    head_region = (0, 0, 364, 240)
    x1, y1, x2, y2 = head_region
    
    extracted_pixels = 0
    hair_pixels_skipped = 0
    
    for y in range(y1, y2):
        for x in range(x1, x2):
            curr_pixel = current_arr[y, x]
            ears_pixel = ears_arr[y, x]
            
            # 如果当前像素与耳朵变体不同
            if curr_pixel[3] > 128:
                # 计算颜色差异
                color_diff = np.sqrt(np.sum((curr_pixel[:3].astype(int) - ears_pixel[:3].astype(int)) ** 2))
                
                # 如果颜色差异显著，或者当前有像素但耳朵变体没有
                if color_diff > 30 or (curr_pixel[3] > 128 and ears_pixel[3] < 128):
                    # 排除头发颜色
                    if is_hair_color(curr_pixel):
                        hair_pixels_skipped += 1
                        continue
                    
                    # 排除耳朵颜色（对于替换耳朵的头饰）
                    if is_ear_color(curr_pixel) and hat != 3:
                        continue
                    
                    # 保留头饰像素
                    headwear_arr[y, x] = curr_pixel
                    extracted_pixels += 1
    
    headwear = Image.fromarray(headwear_arr)
    
    # 检查是否提取到足够的像素
    if extracted_pixels < 100:
        return None, f"too few pixels ({extracted_pixels}), mostly hair overlap"
    
    return headwear, f"ok ({extracted_pixels} pixels, skipped {hair_pixels_skipped} hair pixels)"


def main():
    """主函数。"""
    print("=" * 60)
    print("提取头饰变体")
    print("=" * 60)
    print()
    
    results = {}
    
    for character in ["Ocean", "Seeky"]:
        print(f"处理 {character}...")
        output_dir = LAYERS / character
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # hat=3 的动物耳朵已经有了（headwear-ears.png）
        # 只需要提取 hat=2 和 hat=4
        for hat in [2, 4]:
            headwear_name = HEADWEAR_NAMES[hat]
            headwear, status = extract_headwear(character, hat)
            
            result_key = f"{character}-{headwear_name}"
            
            if headwear:
                output_path = output_dir / f"headwear-{headwear_name}.png"
                headwear.save(output_path)
                print(f"  ✓ {headwear_name}: {status}")
                results[result_key] = {"status": "extracted", "detail": status}
            else:
                print(f"  ✗ {headwear_name}: {status}")
                results[result_key] = {"status": "failed", "detail": status}
        
        print()
    
    # 输出报告
    print("=" * 60)
    print("提取报告")
    print("=" * 60)
    
    for key, result in results.items():
        status_icon = "✓" if result["status"] == "extracted" else "✗"
        print(f"{status_icon} {key}: {result['detail']}")
    
    print()
    print("注意：如果某个头饰无法干净分离，需要手动从源美术资源中提取")


if __name__ == "__main__":
    main()
