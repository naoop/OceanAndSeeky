'use strict';
const names = ['Ocean', 'Seeky'];
const outfits = ['粉色装', '红衬衫', '簪花套装', '背带裤', '粉衬衫', '校服'];
const hats = ['默认发型', '簪花', '动物耳朵', '粉色蜜桃帽'];
const people = Object.fromEntries(names.map(name => [name, {hat:3, face:null, action:null, frame:0, time:0}]));
let cast = '双人', format = '静态图', outfit = 4, tab = '着装', editor = 'Ocean';
let together = false, elapsed = 0, last = null, timer = 0;
const assets = 'studio-assets/';
const portrait = (name, suit, hat) => assets + name + '-' + suit + '-' + hat + '.png';
const frameSrc = (variant, frame) => assets + variant.prefix + '-' + frame + '.png';
const variantFor = (name, key = people[name].action) =>
  actionCatalog.find(action => action.actor === name && action.key === key)
    ?.variants[outfit + '-' + people[name].hat];
const visible = () => cast === '双人' ? names : [cast];
const byId = id => document.getElementById(id);
function element(tag, text, cls) {
  const item = document.createElement(tag);
  if (text) item.textContent = text;
  if (cls) item.className = cls;
  return item;
}
function choice(parent, label, selected, apply, images = []) {
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
    const position = [...document.querySelectorAll('button')].indexOf(button);
    apply();
    render();
    const replacement = document.querySelectorAll('button')[position];
    if (replacement) replacement.focus({preventScroll:true});
  };
  parent.append(button);
}
function group(parent, cls) {
  const box = element('div', '', cls);
  parent.append(box);
  return box;
}
function stopPair() { together = false; }
function selectCast(value) {
  cast = value;
  if (value !== '双人') { editor = value; stopPair(); }
}
function chooseAction(key, frame = 0) {
  stopPair();
  Object.assign(people[editor], {action:key, frame, time:0});
  elapsed = 0;
}
function panel() {
  const scope = byId('scope'), choices = byId('choices');
  scope.replaceChildren(); choices.replaceChildren();
  scope.append(tab === '着装' ? '两人共用一套着装' : '编辑角色');
  if (tab !== '着装') {
    const who = group(scope, 'switch');
    for (const name of visible()) choice(who, name, editor === name, () => { editor = name; });
  }
  const grid = group(choices, 'grid');
  const person = people[editor];
  if (tab === '着装') {
    outfits.forEach((label, i) => choice(grid, label, outfit === i+1, () => {
      outfit = i+1;
    }, visible().map(n => portrait(n, i+1, people[n].hat))));
  } else if (tab === '头饰') {
    hats.forEach((label, i) => choice(grid, label, person.hat === i+1, () => {
      person.hat = i+1;
    }, [assets + editor + '-head-' + (i+1) + '.png']));
  } else if (tab === '表情') {
    function selectFace(prefix) {
      chooseAction(null);
      person.face = prefix;
    }
    choice(grid, '定稿表情', !person.face && !variantFor(editor),
      () => selectFace(null), [assets + editor + '-head-' + person.hat + '.png']);
    for (const {label,prefix} of faceCatalog[editor]) {
      choice(grid, label, person.face === prefix && !variantFor(editor),
        () => selectFace(prefix), [assets + prefix + '-icon.png']);
    }
  } else {
    choice(grid, '定稿姿势', !variantFor(editor) && !together, () => chooseAction(null),
      [portrait(editor, outfit, person.hat)]);
    for (const {key,label,actor,variants} of actionCatalog) {
      if (actor !== editor) continue;
      const variant = variantFor(editor, key);
      if (!variant) {
        const supported = Object.keys(variants).map(pair => {
          const [suit, hat] = pair.split('-').map(Number);
          return outfits[suit-1] + '·' + hats[hat-1];
        });
        choices.append(element('p',label + '可用搭配：' + supported.join('、')));
        continue;
      }
      choice(grid, label, key === person.action && !together, () => chooseAction(key),
          [frameSrc(variant, Math.min(1, variant.durations.length-1))]);
      if (format === '静态图' && person.action === key && !together) {
        choices.append(element('h3',label + ' · 定格姿势'));
        const frames = group(choices, 'grid frames');
        variant.durations.forEach((_, i) => choice(frames, '第 ' + (i+1) + ' 帧',
          !together && person.action === key && Math.min(person.frame,variant.durations.length-1) === i,
          () => chooseAction(key,i), [frameSrc(variant,i)]));
      }
    }
    {
      choices.append(element('h3','双人动作'));
      const row = group(choices,'row');
      const label = together ? '结束同步跳' : (cast === '双人' ? '同步跳一下' : '切到双人并同步跳');
      choice(row,label,together,() => {
        together = !together;
        if (together) cast = '双人';
        elapsed = 0;
      });
    }
  }
}
function frameAt(person, variant) {
  const delays = variant.durations;
  const start = Math.min(person.frame, delays.length-1);
  if (format === '静态图') return start;
  let time = person.time % delays.reduce((a,b) => a+b,0);
  for (let step=0; step<delays.length; step++) {
    const i = (step+start) % delays.length;
    if (time < delays[i]) return i;
    time -= delays[i];
  }
  return start;
}
function paint() {
  for (const figure of byId('stage').children) {
    const name = figure.dataset.name, person = people[name], image = figure.firstChild;
    const variant = !together && variantFor(name);
    const url = variant ? frameSrc(variant,frameAt(person,variant)) : portrait(name,outfit,person.hat);
    if (image.getAttribute('src') !== url) image.src = url;
    const layer = figure.children[1];
    layer.hidden = Boolean(variant) || !person.face;
    const faceUrl = assets + person.face + (person.hat === 3 ? '' : '-plain') + '.png';
    if (!layer.hidden && layer.getAttribute('src') !== faceUrl) {
      layer.src = faceUrl;
    }
    const height = together ? (format === '静态图' ? 1 : Math.sin(Math.PI * elapsed / 800)) : 0;
    image.style.transform = 'translateY(' + (-height*6) + '%)';
    layer.style.transform = image.style.transform;
  }
}
function tick(now) {
  if (last !== null) {
    if (together) elapsed += now-last;
    else for (const name of visible()) {
      if (variantFor(name)) people[name].time += now-last;
    }
  }
  last = now;
  if (together && elapsed >= 800) { stopPair(); elapsed = 0; render(); return; }
  paint();
  timer = requestAnimationFrame(tick);
}
function playback() {
  cancelAnimationFrame(timer);
  last = null;
  if (!document.hidden && format === 'GIF' && (together || visible().some(n => variantFor(n)))) {
    timer = requestAnimationFrame(tick);
  }
}
function render() {
  for (const [id, labels, current, apply] of [
    ['format',['静态图','GIF'],format,v => {
      format=v; elapsed=0; names.forEach(n => { people[n].time=0; });
    }],
    ['cast',['Ocean','双人','Seeky'],cast,selectCast],
    ['tabs',['着装','头饰','表情','动作'],tab,v => {tab=v;}]
  ]) {
    const box = byId(id); box.replaceChildren();
    labels.forEach(label => choice(box,label,label === current,() => apply(label)));
  }
  const stage = byId('stage'); stage.replaceChildren();
  for (const name of visible()) {
    const figure = element('div','','actor'); figure.dataset.name = name;
    const image = element('img'); image.alt = name + ' · ' + outfits[outfit-1];
    const face = element('img'); face.alt = ''; face.hidden = true;
    figure.append(image,face,element('span',name)); stage.append(figure);
  }
  panel(); paint(); playback();
  if (format === 'GIF' && !together && visible().every(n => !variantFor(n))) {
    byId('choices').append(element('p','在「动作」中选择一个动作，即可播放 GIF 预览。'));
  }
}
document.addEventListener('visibilitychange',playback);
render();

