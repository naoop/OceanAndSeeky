'use strict';

// 常量和配置
const ACTOR_NAMES = ['Ocean', 'Seeky'];
const UI_TEXT = {
  formats: ['静态图', 'GIF'],
  cast: ['Ocean', '双人', 'Seeky'],
  tabs: ['着装', '头饰', '表情', '动作'],
  outfits: ['粉色装', '红衬衫', '簪花套装', '背带裤', '粉衬衫', '校服'],
  hats: ['默认发型', '簪花', '动物耳朵', '粉色蜜桃帽']
};

// 头饰ID到名称的映射
const HEADWEAR_MAP = {
  1: 'default-hair',
  2: 'flower',
  3: 'animal-ears',
  4: 'peach-hat'
};

// 应用状态
const state = {
  cast: 'dual',
  format: 'static',
  outfit: 4,
  tab: 'outfit',
  editor: 'Ocean',
  together: false,
  elapsed: 0,
  last: null,
  timer: 0,
  people: Object.fromEntries(ACTOR_NAMES.map(name => [
    name,
    { hat: 3, face: null, action: null, frame: 0, time: 0 }
  ])),
  layersConfig: {}  // 将在加载时填充
};

const assets = 'studio-assets/';
const layersPath = 'studio-assets/layers/';

// 工具函数
const byId = id => document.getElementById(id);
const portrait = (name, suit, hat) => assets + name + '-' + suit + '-' + hat + '.png';
const frameSrc = (variant, frame) => assets + variant.prefix + '-' + frame + '.png';

// 加载图层配置
async function loadLayerConfig(character) {
  try {
    const response = await fetch(layersPath + character + '/layers.json');
    return await response.json();
  } catch (e) {
    console.error(`Failed to load layer config for ${character}:`, e);
    return null;
  }
}

// 初始化图层配置
async function initLayerConfigs() {
  for (const character of ACTOR_NAMES) {
    const config = await loadLayerConfig(character);
    if (config) {
      state.layersConfig[character] = config;
    }
  }
}

// 使用图层系统合成角色图像
function compositeCharacter(character, outfit, hat, expression) {
  const config = state.layersConfig[character];
  if (!config) {
    // 降级到旧的合成图
    return portrait(character, outfit, hat);
  }
  
  // 返回图层数据用于前端堆叠
  const layers = [];
  const basePath = layersPath + character + '/';
  
  // 1. Body layer (无头身体)
  const bodyPath = basePath + `body/outfit-${outfit}-hat-${hat}.png`;
  layers.push({ type: 'body', src: bodyPath });
  
  // 2. Face layer
  let faceFile = 'face-default.png';
  if (expression && config.expressions[expression]) {
    const exprConfig = config.expressions[expression];
    faceFile = exprConfig.face || 'face-default.png';
  }
  layers.push({ type: 'face', src: basePath + faceFile });
  
  // 3. Features layer
  if (expression && config.expressions[expression]) {
    const featuresFile = config.expressions[expression].features;
    if (featuresFile) {
      layers.push({ type: 'features', src: basePath + featuresFile });
    }
  } else {
    // 默认表情
    layers.push({ type: 'features', src: basePath + 'features-default.png' });
  }
  
  // 4. Hair layer
  if (config.layers.hair) {
    layers.push({ type: 'hair', src: basePath + config.layers.hair });
  }
  
  // 5. Headwear layer
  const headwearName = HEADWEAR_MAP[hat];
  if (config.layers.headwear && config.layers.headwear[headwearName]) {
    const headwearFile = config.layers.headwear[headwearName];
    if (headwearFile) {
      layers.push({ type: 'headwear', src: basePath + headwearFile });
    }
  }
  
  return layers;
}

function variantFor(name, key = state.people[name].action) {
  return actionCatalog.find(action => action.actor === name && action.key === key)
    ?.variants[state.outfit + '-' + state.people[name].hat];
}

function visibleActors() {
  return state.cast === 'dual' ? ACTOR_NAMES : [state.cast];
}

function element(tag, text = '', cls = '') {
  const item = document.createElement(tag);
  if (text) item.textContent = text;
  if (cls) item.className = cls;
  return item;
}

function updateButtonGroup(containerId, values, current, mapFn) {
  const container = byId(containerId);
  const buttons = container.querySelectorAll('button');
  
  values.forEach((value, i) => {
    if (buttons[i]) {
      buttons[i].setAttribute('aria-pressed', String(mapFn(value) === current));
    }
  });
}

function renderButtonGroup(parent, values, current, apply, mapFn = v => v) {
  values.forEach(value => {
    const button = element('button');
    button.type = 'button';
    button.textContent = value;
    button.setAttribute('aria-pressed', String(mapFn(value) === current));
    button.onclick = () => {
      apply(mapFn(value));
      render();
    };
    parent.append(button);
  });
}

function renderChoiceButton(parent, label, selected, apply, previewLayers = null) {
  const button = element('button');
  button.type = 'button';
  button.setAttribute('aria-pressed', String(selected));
  
  if (previewLayers) {
    button.className = 'tile';
    const art = element('span', '', 'art');
    
    // 如果是图层数组，创建预览容器
    if (Array.isArray(previewLayers)) {
      const preview = element('div', '', 'layer-preview');
      previewLayers.forEach(layer => {
        const img = element('img');
        img.alt = '';
        img.src = layer.src;
        img.className = 'layer-' + layer.type;
        preview.append(img);
      });
      art.append(preview);
    } else {
      // 单个图像URL
      const image = element('img');
      image.alt = '';
      image.src = previewLayers;
      art.append(image);
    }
    
    button.append(art);
  }
  
  button.append(label);
  button.onclick = () => {
    apply();
    render();
  };
  parent.append(button);
}

function stopPair() {
  state.together = false;
}

function selectCast(value) {
  state.cast = value;
  if (value !== 'dual') {
    state.editor = value;
    stopPair();
  }
}

function chooseAction(key, frame = 0) {
  stopPair();
  Object.assign(state.people[state.editor], { action: key, frame, time: 0 });
  state.elapsed = 0;
}

function renderPanel() {
  const scope = byId('scope');
  const choices = byId('choices');
  
  scope.replaceChildren();
  choices.replaceChildren();
  
  scope.append(state.tab === 'outfit' ? '两人共用一套着装' : '编辑角色');
  
  if (state.tab !== 'outfit') {
    const who = element('div', '', 'switch');
    visibleActors().forEach(name => {
      renderChoiceButton(who, name, state.editor === name, () => {
        state.editor = name;
      });
    });
    scope.append(who);
  }
  
  const grid = element('div', '', 'grid');
  const person = state.people[state.editor];
  
  if (state.tab === 'outfit') {
    // 着装选择 - 使用图层预览
    UI_TEXT.outfits.forEach((label, i) => {
      const suitIndex = i + 1;
      const isSelected = state.outfit === suitIndex;
      
      // 为每个可见角色创建图层预览
      const previewLayers = [];
      visibleActors().forEach(name => {
        const layers = compositeCharacter(name, suitIndex, state.people[name].hat, null);
        if (Array.isArray(layers)) {
          layers.forEach(layer => previewLayers.push(layer));
        }
      });
      
      renderChoiceButton(grid, label, isSelected, () => {
        state.outfit = suitIndex;
      }, previewLayers.length > 0 ? previewLayers : portrait(state.editor, suitIndex, person.hat));
    });
  } else if (state.tab === 'hat') {
    // 头饰选择
    UI_TEXT.hats.forEach((label, i) => {
      const hatIndex = i + 1;
      const layers = compositeCharacter(state.editor, state.outfit, hatIndex, null);
      
      renderChoiceButton(grid, label, person.hat === hatIndex, () => {
        person.hat = hatIndex;
      }, layers);
    });
  } else if (state.tab === 'face') {
    // 表情选择
    const config = state.layersConfig[state.editor];
    
    function selectFace(exprKey) {
      chooseAction(null);
      person.face = exprKey;
    }
    
    // 默认表情
    const defaultLayers = compositeCharacter(state.editor, state.outfit, person.hat, null);
    renderChoiceButton(grid, '定稿表情', !person.face && !variantFor(state.editor),
      () => selectFace(null), defaultLayers);
    
    // 所有表情
    if (config && config.expressions) {
      for (const [exprKey, exprData] of Object.entries(config.expressions)) {
        if (exprKey === 'default') continue;
        
        const layers = compositeCharacter(state.editor, state.outfit, person.hat, exprKey);
        renderChoiceButton(grid, exprData.label, 
          person.face === exprKey && !variantFor(state.editor),
          () => selectFace(exprKey), layers);
      }
    }
  } else {
    // 动作选择
    const defaultLayers = compositeCharacter(state.editor, state.outfit, person.hat, person.face);
    renderChoiceButton(grid, '定稿姿势', !variantFor(state.editor) && !state.together,
      () => chooseAction(null), defaultLayers);
    
    for (const { key, label, actor, variants } of actionCatalog) {
      if (actor !== state.editor) continue;
      
      const variant = variantFor(state.editor, key);
      if (!variant) {
        const supported = Object.keys(variants).map(pair => {
          const [suit, hat] = pair.split('-').map(Number);
          return UI_TEXT.outfits[suit - 1] + '·' + UI_TEXT.hats[hat - 1];
        });
        choices.append(element('p', label + '可用搭配：' + supported.join('、')));
        continue;
      }
      
      renderChoiceButton(grid, label, key === person.action && !state.together,
        () => chooseAction(key),
        frameSrc(variant, Math.min(1, variant.durations.length - 1)));
      
      if (state.format === 'static' && person.action === key && !state.together) {
        choices.append(element('h3', label + ' · 定格姿势'));
        const frames = element('div', '', 'grid frames');
        variant.durations.forEach((_, i) => {
          renderChoiceButton(frames, '第 ' + (i + 1) + ' 帧',
            !state.together && person.action === key &&
            Math.min(person.frame, variant.durations.length - 1) === i,
            () => chooseAction(key, i), frameSrc(variant, i));
        });
        choices.append(frames);
      }
    }
    
    choices.append(element('h3', '双人动作'));
    const row = element('div', '', 'row');
    const label = state.together ? '结束同步跳'
      : (state.cast === 'dual' ? '同步跳一下' : '切到双人并同步跳');
    renderChoiceButton(row, label, state.together, () => {
      state.together = !state.together;
      if (state.together) state.cast = 'dual';
      state.elapsed = 0;
    });
    choices.append(row);
  }
  
  choices.append(grid);
}

function frameAt(person, variant) {
  const delays = variant.durations;
  const start = Math.min(person.frame, delays.length - 1);
  
  if (state.format === 'static') return start;
  
  let time = person.time % delays.reduce((a, b) => a + b, 0);
  for (let step = 0; step < delays.length; step++) {
    const i = (step + start) % delays.length;
    if (time < delays[i]) return i;
    time -= delays[i];
  }
  return start;
}

function paint() {
  for (const figure of byId('stage').children) {
    const name = figure.dataset.name;
    const person = state.people[name];
    const variant = !state.together && variantFor(name);
    
    // 如果有动作动画，使用旧的全帧精灵图
    if (variant) {
      const url = frameSrc(variant, frameAt(person, variant));
      const mainImg = figure.querySelector('.actor-main');
      
      // 隐藏图层，显示动画帧
      figure.querySelectorAll('.actor-layer').forEach(layer => layer.hidden = true);
      mainImg.hidden = false;
      if (mainImg.getAttribute('src') !== url) mainImg.src = url;
    } else {
      // 使用图层系统
      const mainImg = figure.querySelector('.actor-main');
      mainImg.hidden = true;
      
      const exprKey = person.face;
      const layers = compositeCharacter(name, state.outfit, person.hat, exprKey);
      
      if (Array.isArray(layers)) {
        // 更新图层
        layers.forEach((layerData, i) => {
          const layerImg = figure.querySelector(`.actor-layer[data-layer="${layerData.type}"]`);
          if (layerImg) {
            layerImg.hidden = false;
            if (layerImg.getAttribute('src') !== layerData.src) {
              layerImg.src = layerData.src;
            }
          }
        });
        
        // 隐藏未使用的图层
        figure.querySelectorAll('.actor-layer').forEach(layerImg => {
          const layerType = layerImg.dataset.layer;
          if (!layers.some(l => l.type === layerType)) {
            layerImg.hidden = true;
          }
        });
      }
    }
    
    // 同步跳跃动画
    const height = state.together
      ? (state.format === 'static' ? 1 : Math.sin(Math.PI * state.elapsed / 800))
      : 0;
    const transform = 'translateY(' + (-height * 6) + '%)';
    figure.querySelectorAll('.actor-main, .actor-layer').forEach(img => {
      img.style.transform = transform;
    });
  }
}

function tick(now) {
  if (state.last !== null) {
    if (state.together) {
      state.elapsed += now - state.last;
    } else {
      for (const name of visibleActors()) {
        if (variantFor(name)) state.people[name].time += now - state.last;
      }
    }
  }
  state.last = now;
  
  if (state.together && state.elapsed >= 800) {
    stopPair();
    state.elapsed = 0;
    render();
    return;
  }
  
  paint();
  state.timer = requestAnimationFrame(tick);
}

function playback() {
  cancelAnimationFrame(state.timer);
  state.last = null;
  
  if (!document.hidden && state.format === 'gif' &&
      (state.together || visibleActors().some(n => variantFor(n)))) {
    state.timer = requestAnimationFrame(tick);
  }
}

function renderStage() {
  const stage = byId('stage');
  
  const currentActors = Array.from(stage.children).map(el => el.dataset.name);
  const newActors = visibleActors();
  
  if (currentActors.length !== newActors.length ||
      !currentActors.every((name, i) => name === newActors[i])) {
    stage.replaceChildren();
    
    for (const name of newActors) {
      const figure = element('div', '', 'actor');
      figure.dataset.name = name;
      
      // 主图像（用于动画帧）
      const mainImg = element('img');
      mainImg.className = 'actor-main';
      mainImg.alt = name;
      mainImg.hidden = true;
      
      // 图层系统（按堆叠顺序）
      const layerTypes = ['body', 'face', 'features', 'hair', 'headwear'];
      const layerImages = layerTypes.map(type => {
        const img = element('img');
        img.className = 'actor-layer';
        img.dataset.layer = type;
        img.alt = '';
        img.hidden = true;
        return img;
      });
      
      const nameLabel = element('span', name);
      
      figure.append(mainImg, ...layerImages, nameLabel);
      stage.append(figure);
    }
  }
}

function render() {
  updateButtonGroup('format', UI_TEXT.formats, state.format,
    v => v === '静态图' ? 'static' : 'gif');
  updateButtonGroup('cast', UI_TEXT.cast, state.cast,
    v => v === 'Ocean' ? 'Ocean' : v === 'Seeky' ? 'Seeky' : 'dual');
  updateButtonGroup('tabs', UI_TEXT.tabs, state.tab,
    v => ['outfit', 'hat', 'face', 'action'][UI_TEXT.tabs.indexOf(v)]);
  
  renderStage();
  renderPanel();
  paint();
  playback();
  
  if (state.format === 'gif' && !state.together &&
      visibleActors().every(n => !variantFor(n))) {
    byId('choices').append(element('p', '在「动作」中选择一个动作，即可播放 GIF 预览。'));
  }
}

function initializeUI() {
  const formatBox = byId('format');
  renderButtonGroup(formatBox, UI_TEXT.formats, state.format, (v) => {
    state.format = v === '静态图' ? 'static' : 'gif';
    state.elapsed = 0;
    ACTOR_NAMES.forEach(n => {
      state.people[n].time = 0;
    });
  }, v => v === '静态图' ? 'static' : 'gif');
  
  const castBox = byId('cast');
  renderButtonGroup(castBox, UI_TEXT.cast, state.cast, selectCast,
    v => v === 'Ocean' ? 'Ocean' : v === 'Seeky' ? 'Seeky' : 'dual');
  
  const tabsBox = byId('tabs');
  renderButtonGroup(tabsBox, UI_TEXT.tabs, state.tab, (v) => {
    state.tab = v;
  }, v => ['outfit', 'hat', 'face', 'action'][UI_TEXT.tabs.indexOf(v)]);
  
  render();
}

// 初始化
document.addEventListener('visibilitychange', playback);

// 加载图层配置后初始化UI
initLayerConfigs().then(() => {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeUI);
  } else {
    initializeUI();
  }
});
