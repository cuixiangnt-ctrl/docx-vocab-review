#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_review.py — 把 vocab_data.json 补全为六字段复习词表，并可生成自包含复习网页。

用法:
    python build_review.py -i vocab_data.json -o exam_review_data.json
    python build_review.py -i vocab_data.json -o exam_review_data.json --html exam_review.html

输出:
    exam_review_data.json -> [{"word","vocab","ipa","pos","cn","ex","ctx","src","mark"}]
    (可选) exam_review.html -> 单文件复习页(搜索/词性筛选/朗读/已掌握/自测)，离线可用
"""
import argparse, json, os, re, sys

VERBS = set([
    'look', 'have', 'listen', 'choose', 'give', 'search', 'ask', 'take', 'make', 'be', 'press',
    'push', 'keep', 'spread', 'enter', 'wonder', 'miss', 'believe', 'set', 'catch', 'open', 'fail',
    'drink', 'grow', 'borrow', 'touch', 'observe', 'change', 'enjoy', 'record', 'repair', 'buy',
    'draw', 'bring', 'answer', 'water', 'play', 'worry', 'read', 'write', 'help', 'send', 'show',
    'tell', 'think', 'know', 'learn', 'start', 'stop', 'use', 'want', 'need', 'find', 'feel',
    'become', 'call', 'carry', 'check', 'clean', 'close', 'cook', 'count', 'cover', 'cross', 'cut',
    'decide', 'describe', 'design', 'develop', 'discover', 'discuss', 'do', 'drive', 'eat', 'explain',
    'express', 'fall', 'fill', 'follow', 'forget', 'get', 'go', 'guess', 'happen', 'hate', 'hear',
    'hold', 'hope', 'improve', 'include', 'introduce', 'invite', 'join', 'jump', 'kill', 'laugh',
    'lead', 'leave', 'let', 'like', 'live', 'lose', 'love', 'mean', 'meet', 'move', 'name', 'notice',
    'offer', 'order', 'paint', 'pass', 'pay', 'pick', 'plan', 'point', 'practice', 'prepare',
    'protect', 'provide', 'pull', 'put', 'rain', 'reach', 'realize', 'receive', 'remember', 'return',
    'run', 'say', 'see', 'sell', 'serve', 'share', 'shout', 'sing', 'sit', 'sleep', 'smile', 'speak',
    'spend', 'stand', 'stay', 'study', 'suggest', 'support', 'surf', 'swim', 'talk', 'teach', 'travel',
    'try', 'turn', 'understand', 'visit', 'wait', 'walk', 'watch', 'wear', 'welcome', 'win', 'work',
])


def parse_word(en):
    vocab = en.strip()
    base = re.split(r'\s*[/／]\s*|\s*…+\s*|\s*\+\s*', vocab)[0].strip()
    base = re.sub(r'\(.*?\)', '', base).strip()
    return base, vocab


def resolve_ipa(base, ipa_db):
    k = base.lower().strip()
    if k in ipa_db and ipa_db.get(k):
        return ipa_db[k]
    first = k.split()[0] if k.split() else k
    if first in ipa_db and ipa_db.get(first):
        return ipa_db[first]
    return None


def clean_ctx(ctx):
    c = (ctx or '').strip()
    c = re.sub(r'^\d+\s*', '', c)
    return c


def gen_example(en, base, pos, ctx):
    """例句：优先用真题语境包装成句子；无语境的短语用通用模板。"""
    c = clean_ctx(ctx)
    if not c:
        return '(' + en + ')'
    first = c.split()[0].lower().strip('.,;:') if c.split() else ''
    if first in VERBS:
        s = 'They ' + c[0].lower() + c[1:]
        if not s.endswith(('.', '!', '?')):
            s += '.'
        return s
    s = c[0].upper() + c[1:]
    if not s.endswith(('.', '!', '?')):
        s += '.'
    return s


def build(data):
    out = []
    for e in data['entries']:
        base, vocab = parse_word(e['en'])
        ipa = resolve_ipa(base, data.get('ipa', {})) or '—'
        ex = gen_example(e['en'], base, e.get('pos', ''), e.get('ctx', ''))
        out.append({
            'word': base, 'vocab': vocab, 'ipa': ipa,
            'pos': e.get('pos', '').strip(), 'cn': e.get('cn', '').strip(),
            'ex': ex, 'ctx': clean_ctx(e.get('ctx', '')), 'src': e.get('src', ''), 'mark': e.get('mark', ''),
        })
    return out


HTML_TPL = r'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>__TITLE__</title>
<style>
  :root{--pri:#2f6fd6;--ink:#22324a;--line:#e6ecf6;--muted:#8a97ad}
  *{box-sizing:border-box}
  body{margin:0;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:#f4f7fc;color:var(--ink)}
  .wrap{max-width:1100px;margin:0 auto;padding:16px}
  .head{background:linear-gradient(135deg,#2f6fd6,#3b8ad9);color:#fff;border-radius:14px;padding:18px 20px}
  .head h1{margin:0 0 4px;font-size:20px}
  .head p{margin:0;font-size:13px;opacity:.92}
  .toolbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px;margin:14px 0}
  .inp{flex:1 1 220px;min-width:180px;padding:9px 12px;border:1.5px solid var(--line);border-radius:9px;font-size:14px;outline:none}
  .inp:focus{border-color:var(--pri)}
  .sel{padding:9px 10px;border:1.5px solid var(--line);border-radius:9px;font-size:13.5px;background:#fff}
  .tg{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
  .btn{padding:9px 14px;border:1.5px solid var(--line);background:#fff;border-radius:9px;font-size:13px;cursor:pointer;font-weight:600;color:#445}
  .btn.active{border-color:var(--pri);background:var(--pri);color:#fff}
  .cnt{font-size:12.5px;color:var(--muted);margin-left:auto}
  .list.card{display:grid;grid-template-columns:repeat(auto-fill,minmax(255px,1fr));gap:12px}
  .list.row{display:flex;flex-direction:column;gap:8px}
  .card{background:#fff;border:1px solid var(--line);border-radius:13px;padding:14px 15px;box-shadow:0 1px 3px rgba(20,40,80,.04)}
  .card.mastered{opacity:.6}.card.mastered .word{text-decoration:line-through}
  .top{display:flex;align-items:center;justify-content:space-between;gap:8px}
  .word{font-size:21px;font-weight:800;color:var(--pri);word-break:break-word}
  .vocab{font-size:13px;color:var(--muted);margin-top:2px}
  .meta{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:8px 0 6px;font-size:12.5px}
  .ipa{font-family:Consolas,monospace;color:#1f8a4c;font-weight:700}
  .ipa.miss{color:var(--muted);font-weight:500;font-family:inherit}
  .pos{background:#eef3fb;color:var(--pri);padding:1px 8px;border-radius:6px;font-weight:700}
  .src{background:#f3f5f9;color:var(--muted);padding:1px 8px;border-radius:6px}
  .cn{font-size:15px;font-weight:600;margin-top:2px}
  .ex{font-size:13.5px;color:#36506e;margin-top:6px;line-height:1.45;display:flex;gap:6px;align-items:flex-start}
  .ex .spk{flex:none;margin-top:1px}
  .ctx{font-size:12px;color:var(--muted);margin-top:6px;border-left:3px solid #e6ecf6;padding-left:8px}
  .foot{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:10px;padding-top:9px;border-top:1px dashed var(--line)}
  .mk{display:flex;align-items:center;gap:6px;font-size:13px;cursor:pointer}
  .rev{padding:5px 12px;border:1px solid var(--pri);background:#fff;color:var(--pri);border-radius:8px;font-size:12.5px;cursor:pointer;font-weight:600}
  .spk{border:none;background:#eef3fb;color:var(--pri);width:30px;height:30px;border-radius:50%;cursor:pointer;font-size:14px;display:inline-flex;align-items:center;justify-content:center}
  .spk:hover{background:var(--pri);color:#fff}.spk.speaking{background:#1f8a4c;color:#fff}
  .list.test .cn,.list.test .ex{display:none}
  .list.test .card.revealed .cn,.list.test .card.revealed .ex{display:block}
  .list.test .rev{display:inline-block}.list:not(.test) .rev{display:none}
  .empty{text-align:center;color:var(--muted);padding:40px 0}
</style></head>
<body><div class="wrap">
  <div class="head"><h1>📝 考试复习 · 词汇短语</h1><p>点击 🔊 听英式发音 · 可标记「已掌握」</p></div>
  <div class="toolbar">
    <input id="search" class="inp" placeholder="搜索单词 / 意思 / 例句…">
    <select id="pos" class="sel"></select>
    <select id="src" class="sel"><option value="">全部来源</option></select>
    <div class="tg">
      <button id="view" class="btn">列表视图</button>
      <button id="test" class="btn">自测模式</button>
      <button id="reset" class="btn">重置掌握</button>
      <span id="cnt" class="cnt"></span>
    </div>
  </div>
  <div id="list" class="list card"></div>
</div>
<script>
var ER_DATA = __DATA__;
var st={q:'',pos:'',src:'',view:'card',test:false};
var MK='examreview_mastery_v1', mk={};
try{mk=JSON.parse(localStorage.getItem(MK)||'{}')||{}}catch(e){mk={}}
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
function speak(t,b){if(!window.speechSynthesis){alert('当前浏览器不支持朗读，请用 Chrome/Edge/Safari');return}
  try{speechSynthesis.cancel()}catch(e){}
  var u=new SpeechSynthesisUtterance(t);u.lang='en-GB';u.rate=.82;
  var vs=speechSynthesis.getVoices()||[];for(var i=0;i<vs.length;i++){if(/en[-_]GB/i.test(vs[i].lang)){u.voice=vs[i];break}}
  if(b)b.classList.add('speaking');u.onend=u.onerror=function(){if(b)b.classList.remove('speaking')};
  speechSynthesis.speak(u)}
function filt(){return ER_DATA.filter(function(x){
  if(st.pos&&x.pos!==st.pos)return false;if(st.src&&x.src!==st.src)return false;
  if(st.q){var q=st.q.toLowerCase();if((x.word+'\n'+x.vocab+'\n'+x.cn+'\n'+x.ex).toLowerCase().indexOf(q)<0)return false}return true})}
function card(x){var hv=x.vocab&&x.vocab!==x.word;
  var ipa=x.ipa==='—'?'<span class="ipa miss">（无音标·点🔊听读）</span>':'<span class="ipa">'+esc(x.ipa)+'</span>';
  var pos=x.pos?'<span class="pos">'+esc(x.pos)+'</span>':'';
  var ctx=(x.ctx&&x.ctx!==x.ex)?'<div class="ctx">真题语境：'+esc(x.ctx)+'</div>':'';
  var ck=mk[x.vocab]?' checked':'';var mc=mk[x.vocab]?' mastered':'';
  return '<div class="card'+mc+'" data-v="'+esc(x.vocab)+'"><div class="top"><div class="word">'+esc(x.word)+
    '</div><button class="spk" data-spk="'+esc(x.word)+'">🔊</button></div>'+(hv?'<div class="vocab">'+esc(x.vocab)+'</div>':'')+
    '<div class="meta">'+ipa+' '+pos+' <span class="src">'+esc(x.src)+'</span></div>'+
    '<div class="cn">'+esc(x.cn)+'</div><div class="ex"><button class="spk" data-ex="'+esc(x.ex)+'">🔊</button><span>'+esc(x.ex)+'</span></div>'+
    ctx+'<div class="foot"><label class="mk"><input type="checkbox" data-mk="'+esc(x.vocab)+'"'+ck+'> 已掌握</label>'+
    '<button class="rev" data-rev="'+esc(x.vocab)+'">显示答案</button></div></div>'}
function render(){var l=document.getElementById('list');var d=filt();
  l.className='list '+(st.view==='row'?'row':'card')+(st.test?' test':'');
  l.innerHTML=d.length?'':('<div class="empty">没有匹配的词汇</div>');
  l.innerHTML=d.map(card).join('');var c=0;d.forEach(function(x){if(mk[x.vocab])c++});
  document.getElementById('cnt').textContent='共 '+d.length+' 条 · 已掌握 '+c+' 条'}
function init(){var ps=document.getElementById('pos'),poses={};
  ER_DATA.forEach(function(x){if(x.pos)poses[x.pos]=1});
  ps.innerHTML='<option value="">全部词性</option>'+Object.keys(poses).sort().map(function(p){return'<option value="'+esc(p)+'">'+esc(p)+'</option>'}).join('');
  document.getElementById('src').innerHTML+='';var so=document.getElementById('src');
  var srcs={};ER_DATA.forEach(function(x){if(x.src)srcs[x.src]=1});
  so.innerHTML='<option value="">全部来源</option>'+Object.keys(srcs).map(function(s){return'<option value="'+esc(s)+'">'+esc(s)+'</option>'}).join('');
  ps.onchange=function(){st.pos=this.value;render()};
  so.onchange=function(){st.src=this.value;render()};
  document.getElementById('search').oninput=function(){st.q=this.value.trim();render()};
  document.getElementById('view').onclick=function(){st.view=st.view==='card'?'row':'card';this.textContent=st.view==='row'?'卡片视图':'列表视图';this.classList.toggle('active',st.view==='row');render()};
  document.getElementById('test').onclick=function(){st.test=!st.test;this.classList.toggle('active',st.test);render()};
  document.getElementById('reset').onclick=function(){if(!confirm('清空所有「已掌握」标记？'))return;mk={};try{localStorage.removeItem(MK)}catch(e){}render()};
  l.addEventListener('click',function(e){var s=e.target.closest('[data-spk]');if(s){speak(s.dataset.spk,s);return}
    var x=e.target.closest('[data-ex]');if(x){speak(x.dataset.ex,x);return}
    var r=e.target.closest('[data-rev]');if(r){var c=r.closest('.card');if(c)c.classList.add('revealed')}});
  l.addEventListener('change',function(e){var m=e.target.closest('[data-mk]');if(m){var v=m.dataset.mk;
    if(m.checked)mk[v]=1;else delete mk[v];try{localStorage.setItem(MK,JSON.stringify(mk))}catch(e){}
    var c=m.closest('.card');if(c)c.classList.toggle('mastered',m.checked);var cc=0;ER_DATA.forEach(function(x){if(mk[x.vocab])cc++});
    document.getElementById('cnt').textContent='共 '+filt().length+' 条 · 已掌握 '+cc+' 条'}});
  render()}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
</script></body></html>'''


def main():
    ap = argparse.ArgumentParser(description='生成六字段复习词表 / 复习网页')
    ap.add_argument('-i', '--in', dest='inp', default='vocab_data.json')
    ap.add_argument('-o', '--out', default='exam_review_data.json')
    ap.add_argument('--html', default=None, help='同时生成的复习网页路径')
    ap.add_argument('--title', default='考试复习 · 词汇短语', help='网页标题')
    args = ap.parse_args()

    if not os.path.exists(args.inp):
        print('输入文件不存在:', args.inp, file=sys.stderr)
        sys.exit(1)
    data = json.load(open(args.inp, encoding='utf-8'))
    out = build(data)
    json.dump(out, open(args.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('已写出', os.path.abspath(args.out), '(%d 条)' % len(out))

    if args.html:
        html = HTML_TPL.replace('__DATA__', json.dumps(out, ensure_ascii=False))
        html = html.replace('__TITLE__', args.title)
        open(args.html, 'w', encoding='utf-8').write(html)
        print('已写出', os.path.abspath(args.html))


if __name__ == '__main__':
    main()
