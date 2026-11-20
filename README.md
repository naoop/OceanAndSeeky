# Ocean & Seeky 像素造型室

一个交互式的像素艺术角色展示工具，可以在浏览器中实时切换两个角色（Ocean 猫耳少年、Seeky 兔耳少年）的服装、头饰、表情和动作。

## 快速开始

### 在线预览

用浏览器直接打开 `index.html`，即可在本地查看和操作角色造型。

### 功能特性

- 🎨 **6 套服装**：粉色装、红衬衫、簪花套装、背带裤、粉衬衫、校服
- 👒 **4 种头饰**：默认发型、簪花、动物耳朵、粉色蜜桃帽
- 😊 **动态表情**：多种表情帧可选
- 🎬 **GIF 动画**：挥锤子、做鬼脸、轻挥小锤等动作
- 👥 **双人模式**：可单独展示或双人同框
- 🎞️ **播放模式**：支持静态图和 GIF 动画切换

## 项目结构

```
.
├── index.html              # 主页面
├── studio.js               # 前端逻辑
├── studio.css              # 样式表
├── studio-assets/          # 生成的展示资源（151 个 PNG + 配置 JS）
│   ├── actions.js          # 动作配置
│   ├── faces.js            # 表情配置
│   └── *.png               # 生成的图像帧
├── assets-src/             # 源素材
│   ├── gif/                # 动作 GIF 源文件
│   ├── refs/               # 无面部的头像参考图（用于表情配准）
│   └── makeup/             # 定稿的美术素材
│       └── SeekyOcean妆造定稿/
│           ├── 头部/       # 头饰原画
│           └── 造型/       # 服装原画
├── tools/                  # 构建脚本
│   ├── prepare_assets.py   # 主构建脚本
│   ├── prepare_faces.py    # 表情处理脚本
│   └── action_config.json  # 动作配置文件
├── archive/                # 归档文件
│   └── v0-canvas/          # 旧版本 Canvas 应用
├── exports/                # 导出文件（.gitignore）
└── requirements.txt        # Python 依赖
```

## 构建流程

### 1. 环境准备

确保安装了 Python 3.7+ 和必要的依赖：

```bash
python3 -m pip install -r requirements.txt
```

### 2. 生成资源

从源素材生成展示用的 PNG 资源：

```bash
# 生成所有资源（角色、动作、表情）
python3 tools/prepare_assets.py

# 只生成角色静态图
python3 tools/prepare_assets.py --actors-only

# 只生成指定动作（grimace / ocean-hammer / hammer / soft）
python3 tools/prepare_assets.py --action grimace
```

构建脚本会自动：
- 去除白色背景（通过漫水填充）
- 配准头部位置并生成服装×头饰组合
- 从 GIF 或 PNG 序列提取动画帧
- 检测并报告重复帧
- 生成表情叠加层

生成的文件输出到 `studio-assets/` 目录。

### 3. 查看结果

用浏览器打开 `index.html`，即可看到更新后的资源。

## 命名规范

为了保持代码整洁和易于维护，项目遵循以下命名规范：

### 文件命名
- **角色静态图**：`{character}-{outfit}-{hat}.png`  
  例：`Ocean-4-3.png`（Ocean，背带裤，动物耳朵）
- **头部缩略图**：`{character}-head-{hat}.png`  
  例：`Seeky-head-2.png`
- **动作帧**：`{action}-{frame}.png`  
  例：`grimace-0.png`, `hammer-3.png`
- **表情图**：`face-{action}-{frame}[-plain|-icon].png`  
  例：`face-grimace-1.png`（带帽），`face-grimace-1-plain.png`（无帽），`face-grimace-1-icon.png`（预览图）

### 目录命名
- 统一使用小写字母和连字符（kebab-case）
- 源素材保留原始命名以便追溯

## 添加新动作

1. **准备源素材**：将 GIF 动画或 PNG 序列放入 `assets-src/gif/` 的子文件夹
2. **编辑配置**：在 `tools/action_config.json` 中添加动作定义：
   ```json
   {
     "key": "new-action",
     "label": "新动作名称",
     "actor": "Ocean",
     "source_path": "folder/animation.gif",
     "use_png_frames": false,
     "outfit": 4,
     "hat": 3,
     "durations": [500, 300, 200, 400]
   }
   ```
3. **重新构建**：运行 `python3 tools/prepare_assets.py --action new-action`
4. **测试**：在浏览器中刷新 `index.html` 查看新动作

## 技术细节

### 坐标配置

脚本中的魔术数字已提取到配置文件：
- **画布尺寸**：364 × 498 像素
- **目标眼睛位置**：用于表情配准
- **头部位置算法**：通过最小化色差自动计算头发和脸部对齐位置

### 帧去重

构建脚本会自动检测重复帧（通过 MD5 哈希）。例如：
- `grimace-0.png` 和 `grimace-5.png` 是相同的（GIF 播放循环导致）
- `soft-1.png` 和 `soft-4.png` 是相同的

当前实现仍保存所有帧以保持兼容性，未来可以进一步优化存储。

### 表情处理

表情系统使用以下流程：
1. 从动作帧中提取眼睛和嘴部
2. 对齐到无面部的头像参考图
3. 保留墨线和细节，丢弃皮肤色
4. 生成带帽（`.png`）和无帽（`-plain.png`）两个版本
5. 生成预览缩略图（`-icon.png`）

## 性能优化

- **151 个 PNG 文件**：当前每个帧独立加载
- **未来改进**：
  - 使用 CSS 雪碧图（spritesheet）减少 HTTP 请求
  - 考虑使用 WebP 格式减小文件大小
  - 大型源文件可使用 Git LFS 管理（当前未启用）

## 相关文档

- [素材说明和交互规范](assets-src/makeup/SeekyOcean妆造定稿/README.md)
- [原始造型设计要点](assets-src/makeup/SeekyOcean妆造定稿/设计要点.md)

## 开发者注意事项

- **不要直接编辑** `studio-assets/` 中的文件，它们是自动生成的
- **不要删除** `assets-src/` 中的原始设计稿
- 修改代码后运行 `python3 tools/prepare_assets.py` 重新生成资源
- 所有脚本支持从项目根目录运行

## 图层系统

### 图层架构

从 v2.0 开始，项目使用分层渲染架构，将角色拆分为独立的可组合图层。这使得表情、头饰和服装可以独立管理和组合。

#### 图层堆叠顺序（从下到上）

1. **body（身体层）**：身体+服装+后发
   - 路径：`assets-src/layers/<character>/body/outfit-<N>-hat-<N>.png`
   - 包含：完整的身体、服装和后发（马尾、披肩发等）
   - 面部区域：使用空白皮肤填充（无五官）

2. **face（面部层）**：皮肤+面部轮廓+人耳
   - 路径：`assets-src/layers/<character>/face/default.png`
   - 包含：皮肤色、脸型轮廓、人类耳朵
   - 不包含：眼睛、眉毛、鼻子、嘴巴、腮红

3. **features（五官层）**：眉毛、眼睛、鼻子、嘴、腮红
   - 路径：`assets-src/layers/<character>/features/<expression>.png`
   - 包含：完整的面部表情（眼睛、眉毛、嘴巴、腮红等）
   - 不包含：皮肤色、头发、刘海
   - 透明背景，仅五官区域有像素

4. **hair-front（前发层）**：刘海/前发
   - 路径：`assets-src/layers/<character>/hair-front/hair-<N>.png`
   - 包含：覆盖额头和眉毛的前发/刘海
   - 必须在五官层之上，以实现刘海自然遮挡眉毛的效果

5. **headwear（头饰层）**：帽子、动物耳朵、发饰
   - 路径：`assets-src/layers/<character>/headwear/<name>.png`
   - 包含：帽子、簪花、动物耳朵等配件
   - 与头发分离，便于独立替换头饰而不影响发型

6. **fx（特效层）**：汗水、星星、心形等（未来扩展）

### 图层命名规范

| 图层类型 | 文件名格式 | 示例 |
|---------|-----------|------|
| 身体 | `outfit-<服装>-hat-<头饰>.png` | `outfit-4-hat-3.png` |
| 面部 | `default.png` 或 `<face-shape>.png` | `default.png`, `puffed-cheeks.png` |
| 五官 | `<expression>.png` | `grimace-0.png`, `smile.png` |
| 前发 | `hair-<头饰>.png` | `hair-3.png` |
| 头饰 | `<name>.png` | `animal-ears.png`, `flower.png` |

### 添加新表情

1. **准备五官层图像**
   - 尺寸：364×498 像素（与画布相同）
   - 格式：PNG，透明背景
   - 内容：仅包含五官（眉毛、眼睛、鼻子、嘴、腮红）
   - 位置：面部区域（约 x=130-232, y=158-236）
   - 注意：不要包含皮肤色、头发或刘海

2. **保存文件**
   ```bash
   assets-src/layers/<character>/features/<expression-name>.png
   ```

3. **更新配置**
   编辑 `tools/layers_config.json`：
   ```json
   {
     "expressions": {
       "<character>": [
         {
           "key": "<expression-name>",
           "label": "表情名称",
           "face": "default"
         }
       ]
     }
   }
   ```

4. **重新构建**
   ```bash
   python3 tools/build_layered_assets.py
   ```

### 添加新的面部形状

大多数表情使用默认面部形状（`default.png`）。如果某个表情需要特殊的脸型（如鼓起的腮帮子、张大的嘴巴拉伸下巴），可以创建自定义面部层：

1. **创建面部形状**
   ```bash
   assets-src/layers/<character>/face/<face-shape>.png
   ```
   
2. **在配置中指定**
   ```json
   {"key": "puffed", "label": "鼓腮", "face": "puffed-cheeks"}
   ```

3. 所有面部形状必须共享相同的锚点（眼睛中心线、下巴顶点）

### 图层合成

最终图像通过图层合成生成：

```python
from PIL import Image

# 按顺序叠加图层
result = Image.new("RGBA", (364, 498), (0, 0, 0, 0))
result = Image.alpha_composite(result, body_layer)
result = Image.alpha_composite(result, face_layer)
result = Image.alpha_composite(result, features_layer)
result = Image.alpha_composite(result, hair_front_layer)
result = Image.alpha_composite(result, headwear_layer)
```

所有图层使用相同的画布尺寸和锚点，无需图层偏移。

### 技术细节

- **像素艺术保持**：所有缩放使用最近邻插值，保持像素艺术的清晰度
- **Alpha 混合**：使用标准 alpha 合成，支持半透明像素
- **图层提取**：从现有合成图中自动提取图层（`tools/extract_layers.py`）
- **颜色判断**：基于颜色距离和透明度判断像素类型（皮肤/头发/五官）

### 动画支持

当前动画（挥锤子、做鬼脸等）仍使用全帧精灵图，未分层。这是因为：
- 动画帧包含运动中的身体姿势变化
- 分层动画需要每一层都有完整的动画序列
- 复杂度较高，收益有限

未来如果需要动画表情切换，可以为动作帧添加图层支持。

## 许可证

本项目为个人创作项目，素材和代码版权归原作者所有。
