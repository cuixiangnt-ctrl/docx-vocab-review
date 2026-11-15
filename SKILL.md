---
name: docx-vocab-review
description: 从 Word 考卷 / 讲义 / 词汇表的 .docx 文档中抽取词汇短语表格，自动补全音标、词性、例句，生成可复习的六字段词表（JSON）和自包含复习网页（HTML，带朗读/搜索/自测/已掌握）。当用户说"从 word 抽单词""把考卷词汇整理成复习表""词汇短语复习""期中单词表""docx 词汇抽取""生成复习模块"时使用。依赖仅 Python 标准库，无需安装第三方包。
---

# docx 考卷词汇复习（docx-vocab-review）

## 核心定位

把一份或多份 Word 考卷、讲义、词汇表（.docx）里的**词汇短语表格**抽出来，自动：
1. 修正常见的「列错位」（序号被当成英文词、短语被塞进词性列）；
2. 联网补全**音标**（dictionaryapi.dev，整词优先、首词回退）；
3. 用真题语境生成**例句**；
4. 输出结构化**六字段词表** `exam_review_data.json`（单词 / 词汇 / 发音 / 词性 / 意思 / 例句），并可一键生成**自包含复习网页** `exam_review.html`（浏览器直接打开，支持搜索、按词性筛选、单词+例句英式发音朗读、已掌握标记、自测模式）。

全程只用 Python 标准库（zipfile / xml.etree / urllib / re），**不需要 pip 安装任何包**，跨平台可用。

---

## 触发场景

- 「帮我把这份期中试卷的词汇短语整理成复习表」
- 「从 word 里把单词抽出来，要有音标和例句」
- 「把这个词汇表做成能背诵/自测的网页」
- 用户上传 / 指向一个 .docx，里面有「英文词 / 词性 / 中文」或「词汇短语复习」「讲评与错题巩固」之类的表格

---

## 使用流程

两步流水线，脚本都在 `scripts/` 下：

### 第 1 步：抽取 + 补全音标
```bash
python scripts/extract_vocab.py 词汇短语复习.docx 讲评与错题巩固.docx -o vocab_data.json
```
- 自动识别含「英文词」或（「词性」+「中文」）表头的表格；
- 修正列错位（英文短语归位到 `en`，序号丢弃，词性标 `phr.`）；
- 多线程抓取音标，整体限时 40s（超时不影响其余字段）；
- 输出 `vocab_data.json`（原始六列 + `ipa` 音标字典）。

### 第 2 步：生成六字段词表 / 复习页
```bash
# 仅数据
python scripts/build_review.py -i vocab_data.json -o exam_review_data.json

# 同时生成自包含复习网页（推荐）
python scripts/build_review.py -i vocab_data.json -o exam_review_data.json --html exam_review.html
```
- 输出 `exam_review_data.json`：`[{word, vocab, ipa, pos, cn, ex, ctx, src, mark}]`
  - `word` 词根/首词，`vocab` 完整形式（含 `die / dying` 这类变体），`ipa` 音标（缺失标 `—`），`pos` 词性，`cn` 中文，`ex` 例句，`ctx` 真题语境，`src` 来源文件，`mark` 重点标记（◆★● 等）
- 加 `--html` 生成 `exam_review.html`：单文件、可离线、可发给娃在手机/电脑上背。

如需把复习表**嵌进已有的学习系统网页**，把 `exam_review_data.json` 内联进页面，复用页面已有的 `goto` 切换和 TTS 即可（参考本仓库示例）。

---

## 字段说明（六字段）

| 字段 | 含义 | 示例 |
|------|------|------|
| word | 单词（词根/首词） | die |
| vocab | 词汇（完整形式，含变体） | die / dying |
| ipa | 发音（音标，缺则 `—`） | /daɪ/ |
| pos | 词性 | v./adj. |
| cn | 意思 | 死亡；垂死的 |
| ex | 例句（真题语境包装） | The plant is dying. |

---

## 已知边界

- 音标缺失的词多为**短语 / 专有名词**（如 `a pair of glasses`），页面会用「点 🔊 听读」兜底朗读，不影响使用。
- 例句优先取自**真题语境**（词在卷子里真实出现的句子），最贴合考试；无语境的短语用通用模板生成。
- 音标来源 dictionaryapi.dev，抽词后首次联网抓取；离线或网络受限时部分音标为空，可后续联网重跑 `extract_vocab.py` 补取。
- 列错位修正是启发式（en 为纯数字且 pos 含字母时交换），若你的 docx 列序特殊，先看一眼 `vocab_data.json` 再决定。
