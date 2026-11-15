#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_vocab.py — 从 Word 考卷/讲义(.docx) 的词汇表中抽取词条并补全音标。

用法:
    python extract_vocab.py 词汇短语复习.docx 讲评与错题巩固.docx -o vocab_data.json

依赖: 仅 Python 标准库 (zipfile / xml.etree / urllib / re / threading)
输出: vocab_data.json -> {"entries":[{src,mark,ctx,en,pos,cn}], "ipa":{word:phonetic}}
"""
import argparse, json, os, re, sys, threading, time, urllib.request, urllib.parse
from xml.etree import ElementTree as ET

NS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def cell_text(tc):
    return ''.join(t.text or '' for t in tc.iter(NS + 't')).strip()


def parse_tables(path):
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read('word/document.xml'))
    out = []
    for tbl in root.iter(NS + 'tbl'):
        rows = [[cell_text(tc) for tc in tr.findall(NS + 'tc')] for tr in tbl.findall(NS + 'tr')]
        if rows:
            out.append(rows)
    return out


def is_vocab(rows):
    h = ' '.join(rows[0]) if rows else ''
    return ('英文词' in h) or ('词性' in h and '中文' in h)


def extract(path, src):
    entries = []
    for tbl in parse_tables(path):
        if not is_vocab(tbl):
            continue
        for r in tbl[1:]:
            if len(r) >= 5:
                mark, ctx, en, pos, cn = r[0], r[1], r[2], r[3], r[4]
            elif len(r) == 4:
                mark, en, pos, cn = '', r[0], r[1], r[2]
                ctx = ''
            else:
                continue
            if not en.strip():
                continue
            # 列错位修正：序号(纯数字)错放 en、英文短语错放 pos 时，英文短语归位到 en
            if re.fullmatch(r'\d+', en) and re.search(r'[A-Za-z]', pos):
                en, pos = pos, 'phr.'
            entries.append({'src': src, 'mark': mark.strip(), 'ctx': ctx.strip(),
                           'en': en.strip(), 'pos': pos.strip(), 'cn': cn.strip()})
    return entries


def fetch_ipa(word):
    try:
        url = 'https://api.dictionaryapi.dev/api/v2/entries/en/' + urllib.parse.quote(word.lower())
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode('utf-8'))
        if isinstance(data, list):
            for it in data:
                if it.get('phonetic'):
                    return it['phonetic']
            for it in data:
                for p in it.get('phonetics', []):
                    if p.get('text'):
                        return p['text']
    except Exception:
        pass
    return None


def main():
    ap = argparse.ArgumentParser(description='从 docx 考卷/讲义抽取词汇短语并补全音标')
    ap.add_argument('files', nargs='+', help='一个或多个 .docx 文件')
    ap.add_argument('-o', '--out', default='vocab_data.json', help='输出 json 路径')
    ap.add_argument('-t', '--timeout', type=float, default=40.0, help='音标联网抓取整体时限(秒)')
    args = ap.parse_args()

    entries = []
    for f in args.files:
        if not os.path.exists(f):
            print('跳过不存在的文件:', f, file=sys.stderr)
            continue
        src = os.path.splitext(os.path.basename(f))[0]
        entries += extract(f, src)

    # 去重
    seen, dedup = set(), []
    for e in entries:
        key = (e['en'].strip().lower(), e['cn'].strip())
        if key in seen:
            continue
        seen.add(key)
        dedup.append(e)

    # 音标
    words = set()
    for e in dedup:
        for w in re.findall(r"[A-Za-z][A-Za-z']*", e['en']):
            words.add(w.lower())
    ipa = {}
    start = time.monotonic()

    def worker(w):
        ipa[w] = fetch_ipa(w)

    ts = [threading.Thread(target=worker, args=(w,)) for w in words]
    for t in ts:
        t.start()
    for t in ts:
        t.join(max(0.0, args.timeout - (time.monotonic() - start)))

    found = sum(1 for v in ipa.values() if v)
    print('条目=%d  独立单词=%d  音标命中=%d' % (len(dedup), len(words), found))
    json.dump({'entries': dedup, 'ipa': ipa}, open(args.out, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('已写出', os.path.abspath(args.out))


if __name__ == '__main__':
    main()
