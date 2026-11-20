#!/usr/bin/env python3
"""
生成 QA 接触表（contact sheets）以验证所有角色×服装×帽子组合。

为每个角色生成：
1. 48 个组合的网格（6 服装 × 4 帽子 × 2 角色）- 使用默认表情
2. 每个表情的完整展示
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "studio-assets"
LAYERS = ROOT / "studio-assets" / "layers"
EXPORTS = ROOT / "exports"


def load_config(character):
    """加载角色配置。"""
    config_path = LAYERS / character / "layers.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def composite_layers(character, outfit, hat, expression='default'):
    """合成图层。"""
    config = load_config(character)
    base_path = LAYERS / character
    
    # 创建画布
    canvas = Image.new('RGBA', tuple(config['canvas']), (0, 0, 0, 0))
    
    # 1. Body layer
    body_file = base_path / 'body' / f'outfit-{outfit}-hat-{hat}.png'
    if body_file.exists():
        body = Image.open(body_file).convert('RGBA')
        canvas.paste(body, (0, 0), body)
    
    # 2. Face layer
    face_file = base_path / config['layers']['face']
    if face_file.exists():
        face = Image.open(face_file).convert('RGBA')
        canvas.paste(face, (0, 0), face)
    
    # 3. Features layer
    expr_config = config['expressions'].get(expression, config['expressions']['default'])
    features_file = base_path / expr_config.get('features', 'features-default.png')
    if features_file.exists():
        features = Image.open(features_file).convert('RGBA')
        canvas.paste(features, (0, 0), features)
    
    # 4. Hair layer
    hair_file = base_path / config['layers']['hair']
    if hair_file.exists():
        hair = Image.open(hair_file).convert('RGBA')
        canvas.paste(hair, (0, 0), hair)
    
    # 5. Headwear layer(s)
    headwear_map = {1: 'default-hair', 2: 'flower', 3: 'animal-ears', 4: 'peach-hat'}
    headwear_name = headwear_map.get(hat, 'default-hair')
    headwear_files = config['layers']['headwear'].get(headwear_name, [])
    
    if isinstance(headwear_files, list):
        for hw_file in headwear_files:
            if hw_file:
                hw_path = base_path / hw_file
                if hw_path.exists():
                    hw = Image.open(hw_path).convert('RGBA')
                    canvas.paste(hw, (0, 0), hw)
    
    return canvas


def generate_combo_sheet(character):
    """
    生成组合网格：6 服装 × 4 帽子。
    
    每个单元格显示：服装编号-帽子编号
    """
    cell_w, cell_h = 364, 498
    margin = 10
    label_h = 30
    
    # 6 列（服装）× 4 行（帽子）
    cols, rows = 6, 4
    
    sheet_w = cols * (cell_w + margin) + margin
    sheet_h = rows * (cell_h + label_h + margin) + margin + 40  # 额外标题空间
    
    sheet = Image.new('RGBA', (sheet_w, sheet_h), (240, 240, 240, 255))
    draw = ImageDraw.Draw(sheet)
    
    # 尝试加载字体
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
        small_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
    except:
        font = ImageFont.load_default()
        small_font = font
    
    # 标题
    title = f"{character} - All Outfit×Hat Combinations"
    draw.text((margin, 10), title, fill=(0, 0, 0, 255), font=font)
    
    y_offset = 40
    
    issues = []
    
    for hat in range(1, 5):
        for outfit in range(1, 7):
            col = outfit - 1
            row = hat - 1
            
            x = margin + col * (cell_w + margin)
            y = y_offset + row * (cell_h + label_h + margin)
            
            # 标签
            label = f"outfit-{outfit}-hat-{hat}"
            draw.text((x, y), label, fill=(0, 0, 0, 255), font=small_font)
            
            # 合成图像
            try:
                sprite = composite_layers(character, outfit, hat)
                sheet.paste(sprite, (x, y + label_h), sprite)
                
                # 检查问题（只对 hat=1 检查耳朵残留）
                # hat=2,3,4 有耳朵层，肩膀的粉色/白色是正常的耳朵延伸
                if hat == 1:
                    sprite_arr = np.array(sprite)
                    shoulder_region = sprite_arr[235:260, 60:300, :]
                    
                    # 统计粉色/白色像素（不应该有的耳朵残留）
                    pink_count = 0
                    white_count = 0
                    for sy in range(shoulder_region.shape[0]):
                        for sx in range(shoulder_region.shape[1]):
                            if shoulder_region[sy, sx, 3] > 128:
                                r, g, b = shoulder_region[sy, sx, :3]
                                is_pink = (r > 200 and g > 150 and b > 150 and r > g)
                                is_white = (r > 220 and g > 220 and b > 220)
                                if is_pink:
                                    pink_count += 1
                                elif is_white:
                                    white_count += 1
                    
                    if pink_count > 50 or white_count > 50:
                        issues.append((outfit, hat, f"{pink_count}pink+{white_count}white"))
                        # 标记问题单元格
                        draw.rectangle([x, y + label_h, x + cell_w, y + label_h + cell_h], 
                                     outline=(255, 0, 0, 255), width=3)
            except Exception as e:
                draw.text((x, y + label_h + 50), f"ERROR: {str(e)[:30]}", 
                         fill=(255, 0, 0, 255), font=small_font)
    
    return sheet, issues


def generate_expression_sheet(character):
    """
    生成表情网格：所有表情 × 默认服装。
    """
    config = load_config(character)
    expressions = list(config['expressions'].keys())
    
    cell_w, cell_h = 364, 498
    margin = 10
    label_h = 30
    
    # 动态计算网格大小
    cols = 5
    rows = (len(expressions) + cols - 1) // cols
    
    sheet_w = cols * (cell_w + margin) + margin
    sheet_h = rows * (cell_h + label_h + margin) + margin + 40
    
    sheet = Image.new('RGBA', (sheet_w, sheet_h), (240, 240, 240, 255))
    draw = ImageDraw.Draw(sheet)
    
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
        small_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
    except:
        font = ImageFont.load_default()
        small_font = font
    
    title = f"{character} - All Expressions (outfit-1-hat-3)"
    draw.text((margin, 10), title, fill=(0, 0, 0, 255), font=font)
    
    y_offset = 40
    
    for i, expr_key in enumerate(expressions):
        col = i % cols
        row = i // cols
        
        x = margin + col * (cell_w + margin)
        y = y_offset + row * (cell_h + label_h + margin)
        
        expr_config = config['expressions'][expr_key]
        label = expr_config.get('label', expr_key)
        draw.text((x, y), label, fill=(0, 0, 0, 255), font=small_font)
        
        try:
            sprite = composite_layers(character, 1, 3, expr_key)
            sheet.paste(sprite, (x, y + label_h), sprite)
        except Exception as e:
            draw.text((x, y + label_h + 50), f"ERROR: {str(e)[:30]}", 
                     fill=(255, 0, 0, 255), font=small_font)
    
    return sheet


def main():
    """主函数。"""
    print("=" * 60)
    print("生成 QA 接触表")
    print("=" * 60)
    print()
    
    qa_dir = EXPORTS / "qa"
    qa_dir.mkdir(parents=True, exist_ok=True)
    
    all_issues = {}
    
    for character in ["Ocean", "Seeky"]:
        print(f"处理 {character}...")
        
        # 生成组合网格
        print(f"  生成组合网格...")
        combo_sheet, issues = generate_combo_sheet(character)
        combo_path = qa_dir / f"{character}_all_combos.png"
        combo_sheet.save(combo_path)
        print(f"  保存到: {combo_path}")
        
        if issues:
            print(f"  ⚠️  发现 {len(issues)} 个问题:")
            for outfit, hat, residue in issues[:5]:
                print(f"    - outfit-{outfit}-hat-{hat}: {residue} 残留像素")
            all_issues[character] = issues
        else:
            print(f"  ✓ 所有组合通过视觉检查")
        
        # 生成表情网格
        print(f"  生成表情网格...")
        expr_sheet = generate_expression_sheet(character)
        expr_path = qa_dir / f"{character}_all_expressions.png"
        expr_sheet.save(expr_path)
        print(f"  保存到: {expr_path}")
        
        print()
    
    print("=" * 60)
    print("QA 报告")
    print("=" * 60)
    
    if all_issues:
        print(f"发现问题的角色: {', '.join(all_issues.keys())}")
        for char, issues in all_issues.items():
            print(f"\n{char}:")
            for outfit, hat, residue in issues:
                print(f"  - outfit-{outfit}-hat-{hat}: {residue} 像素")
    else:
        print("✓ 所有角色的所有组合通过视觉检查")
    
    print(f"\nQA 接触表保存在: {qa_dir}/")


if __name__ == "__main__":
    main()
