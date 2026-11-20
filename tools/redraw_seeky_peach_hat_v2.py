#!/usr/bin/env python3
"""
重绘 Seeky 桃子帽（基于差异分析）。
"""
import numpy as np
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "studio-assets"
LAYERS = ROOT / "studio-assets" / "layers"


def extract_seeky_peach_hat_by_diff():
    """通过差异分析提取 Seeky 桃子帽。"""
    hat4 = Image.open(ASSETS / "Seeky-4-4.png").convert("RGBA")
    hat1 = Image.open(ASSETS / "Seeky-4-1.png").convert("RGBA")
    
    hat4_arr = np.array(hat4)
    hat1_arr = np.array(hat1)
    
    # 创建桃子帽图层
    peach = Image.new("RGBA", hat4.size, (0, 0, 0, 0))
    peach_arr = np.array(peach)
    
    extracted = 0
    
    # 在头顶区域找差异
    for y in range(0, 200):
        for x in range(80, 284):
            p4 = hat4_arr[y, x]
            p1 = hat1_arr[y, x]
            
            if p4[3] < 128:
                continue
            
            # 计算颜色差异
            color_diff = 0
            if p1[3] > 128:
                color_diff = int(np.sum(np.abs(p4[:3].astype(int) - p1[:3].astype(int))))
            else:
                color_diff = 999
            
            # 如果差异大，可能是帽子
            if color_diff > 20:
                r, g, b = p4[:3]
                
                # 排除头发（深色）
                is_hair = (r < 100 and g < 100 and b < 100)
                
                # 排除兔耳（淡粉色/白色，接近肤色）
                # 兔耳特征：高亮度、低饱和度
                brightness = (r + g + b) / 3
                is_ear = (brightness > 200 and abs(r - g) < 30 and abs(g - b) < 30)
                
                # 桃子帽特征：
                # 1. 粉红色（饱和粉色，不是淡粉）
                is_peachy_pink = (r > 200 and g > 150 and b > 150 and (r - g) > 20)
                
                # 2. 黄橙色（叶子边缘）
                is_peachy_yellow = (r > 200 and g > 180 and b > 100 and b < 160)
                
                # 3. 深红/棕色轮廓
                is_peachy_dark = (r > 80 and r < 180 and g > 20 and g < 100 and b > 20 and b < 100)
                
                if (is_peachy_pink or is_peachy_yellow or is_peachy_dark) and not is_hair and not is_ear:
                    peach_arr[y, x] = p4
                    extracted += 1
    
    peach = Image.fromarray(peach_arr)
    return peach, extracted


def main():
    """主函数。"""
    print("重绘 Seeky 桃子帽（基于差异）...")
    
    peach, pixel_count = extract_seeky_peach_hat_by_diff()
    
    print(f"  提取了 {pixel_count} 像素")
    
    # 保存
    output_path = LAYERS / "Seeky" / "headwear-peach-hat.png"
    peach.save(output_path)
    print(f"  保存到: {output_path}")
    
    # 比较 Ocean 的桃子帽
    ocean_peach = Image.open(LAYERS / "Ocean" / "headwear-peach-hat.png").convert("RGBA")
    ocean_arr = np.array(ocean_peach)
    ocean_pixels = np.sum(ocean_arr[:, :, 3] > 128)
    
    print(f"\n对比:")
    print(f"  Ocean 桃子帽: {ocean_pixels} 像素")
    print(f"  Seeky 桃子帽: {pixel_count} 像素")
    
    if pixel_count > 1500:
        print("\n✓ 完成")
    else:
        print(f"\n⚠️  像素数偏少，可能需要手动绘制")


if __name__ == "__main__":
    main()
