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

## 许可证

本项目为个人创作项目，素材和代码版权归原作者所有。
