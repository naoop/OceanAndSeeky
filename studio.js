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

// 应用状态
const state = {
  cast: 'dual',  // 'Ocean', 'dual', 'Seeky'
  format: 'static',  // 'static', 'gif'
  outfit: 4,
  tab: 'outfit',  // 'outfit', 'hat', 'face', 'action'
  editor: 'Ocean',  // 当前编辑的角色
  together: false,  // 双人同步跳跃
  elapsed: 0,
  last: null,
  timer: 0,
  people: Object.fromEntries(ACTOR_NAMES.map(name => [
    name,
    { hat: 3, face: null, action: null, frame: 0, time: 0 }
  ]))
};

const assets = 'studio-assets/';

// 工具函数
const byId = id => document.getElementById(id);
const portrait = (name, suit, hat) => assets + name + '-' + suit + '-' + hat + '.png';
const frameSrc = (variant, frame) => assets + variant.prefix + '-' + frame + '.png';

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

function renderChoiceButton(parent, label, selected, apply, images = []) {
  const button = element('button');
  button.type = 'button';
  button.setAttribute('aria-pressed', String(selected));
  
  if (images.length) {
    button.className = 'tile';
    const art = element('span', '', 'art');
    for (const url of images) {
      const image = element('img');
      image.alt = '';
      image.src = url;
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
  
  // 显示当前编辑范围
  scope.append(state.tab === 'outfit' ? '两人共用一套着装' : '编辑角色');
  
  // 如果不是着装标签，显示角色选择器
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
    // 着装选择
    UI_TEXT.outfits.forEach((label, i) => {
      const suitIndex = i + 1;
      renderChoiceButton(grid, label, state.outfit === suitIndex, () => {
        state.outfit = suitIndex;
      }, visibleActors().map(n => portrait(n, suitIndex, state.people[n].hat)));
    });
  } else if (state.tab === 'hat') {
    // 头饰选择
    UI_TEXT.hats.forEach((label, i) => {
      const hatIndex = i + 1;
      renderChoiceButton(grid, label, person.hat === hatIndex, () => {
        person.hat = hatIndex;
      }, [assets + state.editor + '-head-' + hatIndex + '.png']);
    });
  } else if (state.tab === 'face') {
    // 表情选择
    function selectFace(prefix) {
      chooseAction(null);
      person.face = prefix;
    }
    
    renderChoiceButton(grid, '定稿表情', !person.face && !variantFor(state.editor),
      () => selectFace(null), [assets + state.editor + '-head-' + person.hat + '.png']);
    
    for (const { label, prefix } of faceCatalog[state.editor]) {
      renderChoiceButton(grid, label, person.face === prefix && !variantFor(state.editor),
        () => selectFace(prefix), [assets + prefix + '-icon.png']);
    }
  } else {
    // 动作选择
    renderChoiceButton(grid, '定稿姿势', !variantFor(state.editor) && !state.together,
      () => chooseAction(null), [portrait(state.editor, state.outfit, person.hat)]);
    
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
        [frameSrc(variant, Math.min(1, variant.durations.length - 1))]);
      
      // 如果是静态模式且当前选中该动作，显示帧选择器
      if (state.format === 'static' && person.action === key && !state.together) {
        choices.append(element('h3', label + ' · 定格姿势'));
        const frames = element('div', '', 'grid frames');
        variant.durations.forEach((_, i) => {
          renderChoiceButton(frames, '第 ' + (i + 1) + ' 帧',
            !state.together && person.action === key &&
            Math.min(person.frame, variant.durations.length - 1) === i,
            () => chooseAction(key, i), [frameSrc(variant, i)]);
        });
        choices.append(frames);
      }
    }
    
    // 双人动作
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
    const image = figure.querySelector('.actor-body');
    const variant = !state.together && variantFor(name);
    
    const url = variant ? frameSrc(variant, frameAt(person, variant))
      : portrait(name, state.outfit, person.hat);
    
    if (image.getAttribute('src') !== url) image.src = url;
    
    const layer = figure.querySelector('.actor-face');
    layer.hidden = Boolean(variant) || !person.face;
    
    const faceUrl = assets + person.face + (person.hat === 3 ? '' : '-plain') + '.png';
    if (!layer.hidden && layer.getAttribute('src') !== faceUrl) {
      layer.src = faceUrl;
    }
    
    const height = state.together
      ? (state.format === 'static' ? 1 : Math.sin(Math.PI * state.elapsed / 800))
      : 0;
    const transform = 'translateY(' + (-height * 6) + '%)';
    image.style.transform = transform;
    layer.style.transform = transform;
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
  
  // 如果角色数量改变，重新创建舞台
  const currentActors = Array.from(stage.children).map(el => el.dataset.name);
  const newActors = visibleActors();
  
  if (currentActors.length !== newActors.length ||
      !currentActors.every((name, i) => name === newActors[i])) {
    stage.replaceChildren();
    
    for (const name of newActors) {
      const figure = element('div', '', 'actor');
      figure.dataset.name = name;
      
      const bodyImg = element('img');
      bodyImg.className = 'actor-body';
      bodyImg.alt = name + ' · ' + UI_TEXT.outfits[state.outfit - 1];
      
      const faceImg = element('img');
      faceImg.className = 'actor-face';
      faceImg.alt = '';
      faceImg.hidden = true;
      
      const nameLabel = element('span', name);
      
      figure.append(bodyImg, faceImg, nameLabel);
      stage.append(figure);
    }
  } else {
    // 只更新 alt 文本
    stage.querySelectorAll('.actor-body').forEach(img => {
      const name = img.closest('.actor').dataset.name;
      img.alt = name + ' · ' + UI_TEXT.outfits[state.outfit - 1];
    });
  }
}

function render() {
  // 更新按钮组状态
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
  
  // 提示信息
  if (state.format === 'gif' && !state.together &&
      visibleActors().every(n => !variantFor(n))) {
    byId('choices').append(element('p', '在「动作」中选择一个动作，即可播放 GIF 预览。'));
  }
}

function initializeUI() {
  // 初始化顶部控制栏
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
  
  // 初始渲染
  render();
}

// 初始化
document.addEventListener('visibilitychange', playback);

// 确保在 DOMContentLoaded 或脚本加载后初始化
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeUI);
} else {
  initializeUI();
}
