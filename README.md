# docx-vocab-review

从 Word 考卷 / 讲义 / 词汇表（`.docx`）中抽取词汇短语表格，自动补全音标、词性、例句，生成可复习的六字段词表（JSON）和自包含复习网页（HTML）。

> 这是一个 WorkBuddy Skill，也可作为独立 Python 小工具使用。

## 特性

- 纯 Python 标准库（`zipfile` / `xml.etree` / `urllib` / `re`），**无需 `pip install`**
- 自动识别词汇表格，修正常见「列错位」（序号被当成英文词、短语塞进词性列）
- 自动抓取音标（dictionaryapi.dev，整词优先、首词回退，多线程限时 40s）
- 生成离线复习网页：搜索 / 词性筛选 / 英式发音朗读 / 自测 / 已掌握标记

## 用法

```bash
# 第 1 步：抽取 + 补音标
python scripts/extract_vocab.py 词汇短语复习.docx 讲评与错题巩固.docx -o vocab_data.json

# 第 2 步：生成六字段词表 + 复习网页
python scripts/build_review.py -i vocab_data.json -o exam_review_data.json --html exam_review.html
```

## 输出

- `exam_review_data.json`：`[{word, vocab, ipa, pos, cn, ex, ctx, src, mark}]`
  - `word` 词根/首词，`vocab` 完整形式（含变体），`ipa` 音标（缺则 `—`），`pos` 词性，`cn` 中文，`ex` 例句，`ctx` 真题语境，`src` 来源文件，`mark` 重点标记
- `exam_review.html`：单文件、可离线、可发给孩子在手机/电脑上背

完整触发词、字段说明与已知边界见 [`SKILL.md`](./SKILL.md)。
