#!/usr/bin/env python3
"""
为每个服装变体创建无头身体精灵图。

去除旧的头发、面部和头饰，只保留身体、服装、脖子和衣领。
新的面部图层会覆盖脖子接缝处。
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "studio-assets"
LAYERS = ROOT / "studio-assets" / "layers"

# 头部区域定义（需要擦除的区域）
HEAD_REGIONS = {
    "Ocean": {
        "bbox": (0, 0, 364, 250),  # 整个头部区域（含头发、脸、耳朵/帽子）
        "neck_keep_y": 235,  # 保留脖子的下边界
    },
    "Seeky": {
        "bbox": (0, 0, 364, 250),
        "neck_keep_y": 235,
    }
}


def create_headless_body(character, outfit, hat):
    """创建无头身体精灵图。"""
    # 读取原始合成图
    sprite_path = ASSETS / f"{character}-{outfit}-{hat}.png"
    if not sprite_path.exists():
        return None
    
    sprite = Image.open(sprite_path).convert("RGBA")
    sprite_arr = np.array(sprite)
    
    region = HEAD_REGIONS[character]
    x1, y1, x2, y2 = region["bbox"]
    neck_y = region["neck_keep_y"]
    
    # 擦除头部区域（脖子以上全部清空）
    sprite_arr[y1:neck_y, x1:x2, 3] = 0  # 设置 alpha 为 0
    
    return Image.fromarray(sprite_arr)


def main():
    """主函数。"""
    print("=" * 60)
    print("创建无头身体精灵图")
    print("=" * 60)
    print()
    
    # 为每个角色创建所有服装变体的无头身体
    for character in ["Ocean", "Seeky"]:
        print(f"处理 {character}...")
        output_dir = LAYERS / character / "body"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        count = 0
        for outfit in range(1, 7):
            for hat in range(1, 5):
                headless = create_headless_body(character, outfit, hat)
                if headless:
                    output_path = output_dir / f"outfit-{outfit}-hat-{hat}.png"
                    headless.save(output_path)
                    count += 1
        
        print(f"  生成了 {count} 个无头身体精灵图")
    
    print()
    print("=" * 60)
    print("✓ 完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
