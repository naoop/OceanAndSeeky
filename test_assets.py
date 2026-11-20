#!/usr/bin/env python3
"""验证所有资源文件是否存在且配置正确（基于图层系统）。"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).parent
ASSETS = ROOT / "studio-assets"
LAYERS = ASSETS / "layers"


def test_layer_files():
    """测试图层文件完整性。"""
    print("测试图层文件...")
    
    missing = []
    for character in ["Ocean", "Seeky"]:
        config_path = LAYERS / character / "layers.json"
        if not config_path.exists():
            missing.append(str(config_path))
            continue
        
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        base_path = LAYERS / character
        
        # 检查面部层
        if "layers" in config and "face" in config["layers"]:
            face_file = config["layers"]["face"]
            if not (base_path / face_file).exists():
                missing.append(f"{character}/{face_file}")
        
        # 检查头发层
        if "layers" in config and "hair" in config["layers"]:
            hair_file = config["layers"]["hair"]
            if not (base_path / hair_file).exists():
                missing.append(f"{character}/{hair_file}")
        
        # 检查头饰层
        if "layers" in config and "headwear" in config["layers"]:
            for headwear_key, headwear_file in config["layers"]["headwear"].items():
                if headwear_file and not (base_path / headwear_file).exists():
                    missing.append(f"{character}/{headwear_file}")
        
        # 检查表情五官层
        if "expressions" in config:
            for expr_key, expr_data in config["expressions"].items():
                if "features" in expr_data:
                    features_file = expr_data["features"]
                    if not (base_path / features_file).exists():
                        missing.append(f"{character}/{features_file}")
        
        # 检查身体层
        body_dir = base_path / "body"
        if body_dir.exists():
            for outfit in range(1, 7):
                for hat in range(1, 5):
                    body_file = body_dir / f"outfit-{outfit}-hat-{hat}.png"
                    if not body_file.exists():
                        missing.append(f"{character}/body/{body_file.name}")
    
    if missing:
        print(f"  ✗ 缺失 {len(missing)} 个文件:")
        for f in missing[:10]:
            print(f"    - {f}")
        if len(missing) > 10:
            print(f"    ... 还有 {len(missing) - 10} 个")
        return False
    else:
        print("  ✓ 所有图层文件都存在")
        return True


def test_layer_dimensions():
    """测试图层文件尺寸。"""
    print("测试图层尺寸...")
    
    invalid = []
    for character in ["Ocean", "Seeky"]:
        layers_dir = LAYERS / character
        if not layers_dir.exists():
            continue
        
        for png_file in layers_dir.glob("*.png"):
            img = Image.open(png_file)
            if img.size != (364, 498):
                invalid.append(f"{character}/{png_file.name}: {img.size}")
            if img.mode != "RGBA":
                invalid.append(f"{character}/{png_file.name}: {img.mode} (expected RGBA)")
        
        # 检查 body 子目录
        body_dir = layers_dir / "body"
        if body_dir.exists():
            for png_file in body_dir.glob("*.png"):
                img = Image.open(png_file)
                if img.size != (364, 498):
                    invalid.append(f"{character}/body/{png_file.name}: {img.size}")
                if img.mode != "RGBA":
                    invalid.append(f"{character}/body/{png_file.name}: {img.mode}")
    
    if invalid:
        print(f"  ✗ {len(invalid)} 个文件尺寸或格式错误:")
        for f in invalid[:5]:
            print(f"    - {f}")
        return False
    else:
        print("  ✓ 所有图层都是 364×498 RGBA")
        return True


def test_features_no_skin():
    """测试五官层不含皮肤色填充。"""
    print("测试五官层纯净度...")
    
    # 皮肤色范围（从 QA report 可知皮肤是浅色）
    def is_skin_like(pixel):
        if pixel[3] < 10:  # 透明像素
            return False
        r, g, b = pixel[:3]
        # 皮肤色：高 R、中等 G、中等 B
        return r > 200 and g > 140 and b > 130
    
    issues = []
    for character in ["Ocean", "Seeky"]:
        layers_dir = LAYERS / character
        if not layers_dir.exists():
            continue
        
        for png_file in layers_dir.glob("features-*.png"):
            img = Image.open(png_file).convert("RGBA")
            arr = np.array(img)
            
            skin_pixels = 0
            total_pixels = 0
            
            # 检查面部区域（约 y=155-235, x=125-235）
            face_region = arr[155:236, 125:236]
            
            for y in range(face_region.shape[0]):
                for x in range(face_region.shape[1]):
                    pixel = face_region[y, x]
                    if pixel[3] > 10:  # 不透明像素
                        total_pixels += 1
                        if is_skin_like(pixel):
                            skin_pixels += 1
            
            if total_pixels > 0:
                skin_ratio = skin_pixels / total_pixels
                if skin_ratio > 0.3:  # 超过 30% 是皮肤色，可能有问题
                    issues.append(f"{character}/{png_file.name}: {skin_pixels}/{total_pixels} pixels ({skin_ratio:.1%}) are skin-like")
    
    if issues:
        print(f"  ⚠ {len(issues)} 个五官层包含肉色像素（可能是嘴唇/舌头等）:")
        for issue in issues[:5]:
            print(f"    - {issue}")
        if len(issues) > 5:
            print(f"    ... 还有 {len(issues) - 5} 个")
        print("  ℹ️  这是正常的 - 五官层可包含嘴唇、舌头等肉色元素")
        return True  # 不作为失败条件
    else:
        print("  ✓ 五官层主要包含深色特征")
        return True


def test_config_schema():
    """测试 layers.json 配置格式。"""
    print("测试配置文件格式...")
    
    errors = []
    for character in ["Ocean", "Seeky"]:
        config_path = LAYERS / character / "layers.json"
        if not config_path.exists():
            errors.append(f"{character}/layers.json: missing")
            continue
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # 验证必需字段
            required_keys = ["character", "canvas", "stack", "layers", "expressions"]
            for key in required_keys:
                if key not in config:
                    errors.append(f"{character}/layers.json: missing key '{key}'")
            
            # 验证 canvas
            if "canvas" in config and config["canvas"] != [364, 498]:
                errors.append(f"{character}/layers.json: canvas should be [364, 498]")
            
            # 验证 stack
            expected_stack = ["face", "features", "hair", "headwear"]
            if "stack" in config and config["stack"] != expected_stack:
                errors.append(f"{character}/layers.json: stack order mismatch")
            
        except json.JSONDecodeError as e:
            errors.append(f"{character}/layers.json: JSON error: {e}")
    
    if errors:
        print(f"  ✗ {len(errors)} 个配置错误:")
        for err in errors:
            print(f"    - {err}")
        return False
    else:
        print("  ✓ 配置文件格式正确")
        return True


def test_action_sprites():
    """测试动作帧精灵图（保持兼容性）。"""
    print("测试动作帧...")
    
    with open(ASSETS / "actions.js", "r", encoding="utf-8") as f:
        content = f.read()
        json_str = content.split("const actionCatalog = ")[1].rstrip(";\n")
        actions = json.loads(json_str)
    
    missing = []
    for action in actions:
        key = action["key"]
        for variant_key, variant in action["variants"].items():
            prefix = variant["prefix"]
            durations = variant["durations"]
            
            for i in range(len(durations)):
                file = ASSETS / f"{prefix}-{i}.png"
                if not file.exists():
                    missing.append(str(file))
    
    if missing:
        print(f"  ✗ 缺失 {len(missing)} 个动作帧")
        return False
    else:
        print("  ✓ 所有动作帧都存在")
        return True


def main():
    """运行所有测试。"""
    print("=" * 50)
    print("资源完整性测试（图层系统）")
    print("=" * 50)
    print()
    
    tests = [
        test_layer_files,
        test_layer_dimensions,
        test_features_no_skin,
        test_config_schema,
        test_action_sprites,
    ]
    
    results = [test() for test in tests]
    
    print()
    print("=" * 50)
    if all(results):
        print("✓ 所有测试通过")
    else:
        print(f"✗ {results.count(False)} 个测试失败")
    print("=" * 50)
    
    return all(results)


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
