#!/usr/bin/env python3
"""
重新提取头饰变体（改进版）。

修复：
1. 桃子帽 - 重新提取完整帽身
2. 花冠 - 保留完整颜色
3. 头饰配置 - 支持耳朵+配饰组合
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "studio-assets"
LAYERS = ROOT / "studio-assets" / "layers"


def extract_flower_crown(character):
    """
    重新提取花冠，保留完整颜色。
    
    策略：对比 hat=2（花冠）和 hat=1（默认），提取所有差异像素。
    """
    hat2_path = ASSETS / f"{character}-4-2.png"
    hat1_path = ASSETS / f"{character}-4-1.png"
    
    if not hat2_path.exists() or not hat1_path.exists():
        return None, "sprites not found"
    
    hat2 = Image.open(hat2_path).convert("RGBA")
    hat1 = Image.open(hat1_path).convert("RGBA")
    
    hat2_arr = np.array(hat2)
    hat1_arr = np.array(hat1)
    
    # 创建花冠图层
    flower = Image.new("RGBA", hat2.size, (0, 0, 0, 0))
    flower_arr = np.array(flower)
    
    # 提取头部区域的差异
    head_region = (0, 0, 364, 240)
    x1, y1, x2, y2 = head_region
    
    extracted = 0
    
    for y in range(y1, y2):
        for x in range(x1, x2):
            hat2_pixel = hat2_arr[y, x]
            hat1_pixel = hat1_arr[y, x]
            
            # 如果 hat2 有像素但 hat1 没有，或者颜色差异显著
            if hat2_pixel[3] > 128:
                color_diff = np.sqrt(np.sum((hat2_pixel[:3].astype(int) - hat1_pixel[:3].astype(int)) ** 2))
                
                if hat1_pixel[3] < 128 or color_diff > 20:
                    # 排除头发（深色）
                    r, g, b = hat2_pixel[:3]
                    is_hair = (r < 100 and g < 100 and b < 100)
                    
                    if not is_hair:
                        flower_arr[y, x] = hat2_pixel
                        extracted += 1
    
    flower = Image.fromarray(flower_arr)
    return flower, f"ok ({extracted} pixels)"


def extract_peach_hat(character):
    """
    重新提取桃子帽，包含完整帽身。
    
    策略：对比 hat=4（桃子帽）和 hat=1（默认），提取所有差异。
    使用更宽松的阈值以包含粉色帽身。
    """
    hat4_path = ASSETS / f"{character}-4-4.png"
    hat1_path = ASSETS / f"{character}-4-1.png"
    
    if not hat4_path.exists() or not hat1_path.exists():
        return None, "sprites not found"
    
    hat4 = Image.open(hat4_path).convert("RGBA")
    hat1 = Image.open(hat1_path).convert("RGBA")
    
    hat4_arr = np.array(hat4)
    hat1_arr = np.array(hat1)
    
    # 创建桃子帽图层
    peach = Image.new("RGBA", hat4.size, (0, 0, 0, 0))
    peach_arr = np.array(peach)
    
    # 提取头部区域的差异
    head_region = (0, 0, 364, 220)
    x1, y1, x2, y2 = head_region
    
    extracted = 0
    
    for y in range(y1, y2):
        for x in range(x1, x2):
            hat4_pixel = hat4_arr[y, x]
            hat1_pixel = hat1_arr[y, x]
            
            if hat4_pixel[3] < 128:
                continue
            
            # 计算颜色差异
            if hat1_pixel[3] > 0:
                color_diff = np.sqrt(np.sum((hat4_pixel[:3].astype(int) - hat1_pixel[:3].astype(int)) ** 2))
            else:
                color_diff = 999  # hat1 透明，hat4 不透明
            
            # 更宽松的阈值以包含粉色帽身
            if color_diff > 15:
                r, g, b = hat4_pixel[:3]
                
                # 排除头发（深色）
                is_hair = (r < 100 and g < 100 and b < 100)
                
                # 排除耳朵（对于已经有的耳朵层）
                # 但保留帽子的所有部分
                if not is_hair:
                    peach_arr[y, x] = hat4_pixel
                    extracted += 1
    
    peach = Image.fromarray(peach_arr)
    
    # 如果提取的像素太少，说明阈值太严格
    if extracted < 3000:
        return None, f"too few pixels ({extracted}), needs manual redraw"
    
    return peach, f"ok ({extracted} pixels)"


def main():
    """主函数。"""
    print("=" * 60)
    print("重新提取头饰变体（改进版）")
    print("=" * 60)
    print()
    
    results = {}
    
    for character in ["Ocean", "Seeky"]:
        print(f"处理 {character}...")
        output_dir = LAYERS / character
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 重新提取花冠
        flower, status = extract_flower_crown(character)
        if flower:
            output_path = output_dir / "headwear-flower.png"
            flower.save(output_path)
            print(f"  ✓ flower: {status}")
            results[f"{character}-flower"] = {"status": "extracted", "detail": status}
        else:
            print(f"  ✗ flower: {status}")
            results[f"{character}-flower"] = {"status": "failed", "detail": status}
        
        # 重新提取桃子帽
        peach, status = extract_peach_hat(character)
        if peach:
            output_path = output_dir / "headwear-peach-hat.png"
            peach.save(output_path)
            print(f"  ✓ peach-hat: {status}")
            results[f"{character}-peach-hat"] = {"status": "extracted", "detail": status}
        else:
            print(f"  ✗ peach-hat: {status}")
            results[f"{character}-peach-hat"] = {"status": "failed", "detail": status}
        
        print()
    
    # 输出报告
    print("=" * 60)
    print("提取报告")
    print("=" * 60)
    
    failures = [k for k, v in results.items() if v["status"] == "failed"]
    
    if failures:
        print(f"✗ {len(failures)} 个头饰需要手动重绘:")
        for key in failures:
            print(f"  - {key}: {results[key]['detail']}")
    else:
        print("✓ 所有头饰成功提取")


if __name__ == "__main__":
    main()
