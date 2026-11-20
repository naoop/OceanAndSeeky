#!/usr/bin/env python3
"""验证所有资源文件是否存在且配置正确。"""
import json
from pathlib import Path

ROOT = Path(__file__).parent
ASSETS = ROOT / "studio-assets"

def test_portraits():
    """测试角色静态图。"""
    print("测试角色静态图...")
    missing = []
    for actor in ["Ocean", "Seeky"]:
        for outfit in range(1, 7):
            for hat in range(1, 5):
                file = ASSETS / f"{actor}-{outfit}-{hat}.png"
                if not file.exists():
                    missing.append(str(file))
    
    if missing:
        print(f"  ✗ 缺失 {len(missing)} 个文件")
        for f in missing[:5]:
            print(f"    - {f}")
        return False
    else:
        print("  ✓ 所有 48 个角色组合都存在")
        return True

def test_heads():
    """测试头部图标。"""
    print("测试头部图标...")
    missing = []
    for actor in ["Ocean", "Seeky"]:
        for hat in range(1, 5):
            file = ASSETS / f"{actor}-head-{hat}.png"
            if not file.exists():
                missing.append(str(file))
    
    if missing:
        print(f"  ✗ 缺失 {len(missing)} 个文件")
        return False
    else:
        print("  ✓ 所有 8 个头部图标都存在")
        return True

def test_actions():
    """测试动作帧。"""
    print("测试动作配置...")
    
    with open(ASSETS / "actions.js", "r", encoding="utf-8") as f:
        content = f.read()
        json_str = content.split("const actionCatalog = ")[1].rstrip(";\n")
        actions = json.loads(json_str)
    
    print(f"  找到 {len(actions)} 个动作")
    
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
        for f in missing[:5]:
            print(f"    - {f}")
        return False
    else:
        print("  ✓ 所有动作帧都存在")
        return True

def test_faces():
    """测试表情。"""
    print("测试表情配置...")
    
    with open(ASSETS / "faces.js", "r", encoding="utf-8") as f:
        content = f.read()
        json_str = content.split("const faceCatalog = ")[1].rstrip(";\n")
        faces = json.loads(json_str)
    
    total_faces = sum(len(entries) for entries in faces.values())
    print(f"  找到 {total_faces} 个表情（Ocean: {len(faces['Ocean'])}, Seeky: {len(faces['Seeky'])}）")
    
    missing = []
    for actor, entries in faces.items():
        for entry in entries:
            prefix = entry["prefix"]
            for suffix in ["", "-plain", "-icon"]:
                file = ASSETS / f"{prefix}{suffix}.png"
                if not file.exists():
                    missing.append(str(file))
    
    if missing:
        print(f"  ✗ 缺失 {len(missing)} 个表情文件")
        for f in missing[:5]:
            print(f"    - {f}")
        return False
    else:
        print("  ✓ 所有表情文件都存在")
        return True

def test_png_sources():
    """检查是否使用 PNG 源。"""
    print("检查配置...")
    
    with open(ROOT / "tools" / "action_config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    
    all_png = all(action.get("use_png_frames", False) for action in config["actions"])
    
    if all_png:
        print("  ✓ 所有动作都使用 PNG 源帧")
        return True
    else:
        print("  ✗ 部分动作仍使用 GIF 源")
        for action in config["actions"]:
            if not action.get("use_png_frames", False):
                print(f"    - {action['key']}: use_png_frames = {action.get('use_png_frames')}")
        return False

def main():
    """运行所有测试。"""
    print("=" * 50)
    print("资源完整性测试")
    print("=" * 50)
    print()
    
    tests = [
        test_portraits,
        test_heads,
        test_actions,
        test_faces,
        test_png_sources,
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
