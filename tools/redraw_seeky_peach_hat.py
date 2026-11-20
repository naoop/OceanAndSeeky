#!/usr/bin/env python3
"""
手动重绘 Seeky 的桃子帽。

基于 Seeky-4-4（背带裤+桃子帽）原始精灵图。
"""
import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "studio-assets"
LAYERS = ROOT / "studio-assets" / "layers"


def redraw_seeky_peach_hat():
    """
    基于原始精灵图重绘 Seeky 的桃子帽。
    """
    # 读取原始精灵图
    original = Image.open(ASSETS / "Seeky-4-4.png").convert("RGBA")
    orig_arr = np.array(original)
    
    # 创建桃子帽图层
    peach = Image.new("RGBA", original.size, (0, 0, 0, 0))
    peach_arr = np.array(peach)
    
    # 桃子帽的大致区域（通过观察原始图确定）
    # 中心大约在 (182, 90-120)
    # 桃子帽包括：粉色帽身 + 绿色叶子 + 茎
    
    # 提取策略：在头顶区域找所有非头发、非耳朵的像素
    for y in range(0, 180):
        for x in range(120, 244):  # 头部水平范围
            pixel = orig_arr[y, x]
            
            if pixel[3] < 128:
                continue
            
            r, g, b = pixel[:3]
            
            # 排除头发（深色）
            is_hair = (r < 100 and g < 100 and b < 100)
            
            # 排除兔耳（粉色/白色/淡肉色）
            is_ear_pink = (r > 200 and g > 150 and b > 150 and r - g < 60)
            is_ear_white = (r > 220 and g > 220 and b > 220)
            
            # 桃子帽特征：
            # 1. 粉色帽身（比耳朵更饱和的粉色）
            is_peach_pink = (r > 220 and g > 140 and g < 190 and b > 160 and b < 210)
            
            # 2. 绿色叶子/茎
            is_leaf = (g > r and g > b and g > 100)
            
            # 3. 黄色/橙色边缘
            is_peach_accent = (r > 200 and g > 150 and b < 180 and r > g)
            
            if (is_peach_pink or is_leaf or is_peach_accent) and not is_hair:
                peach_arr[y, x] = pixel
    
    peach = Image.fromarray(peach_arr)
    
    # 统计像素
    extracted = np.sum(peach_arr[:, :, 3] > 128)
    
    return peach, extracted


def main():
    """主函数。"""
    print("手动重绘 Seeky 桃子帽...")
    
    peach, pixel_count = redraw_seeky_peach_hat()
    
    print(f"  提取了 {pixel_count} 像素")
    
    if pixel_count < 2000:
        print(f"  ⚠️  像素数太少，可能需要调整")
    
    # 保存
    output_path = LAYERS / "Seeky" / "headwear-peach-hat.png"
    peach.save(output_path)
    print(f"  保存到: {output_path}")
    
    print("\n✓ 完成")


if __name__ == "__main__":
    main()
