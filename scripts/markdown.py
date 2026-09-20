"""依存ゼロの Markdown -> HTML 変換器。

四柱推命鑑定プロジェクトの scripts/markdown.py を流用し、この工房に固有の
2 記法を足したもの:

  :::quote n    原典からの引用。n は frontmatter の sources の添字。
                出典ラベルを添えて描画する。ブロック引用 (>) とは別物で、
                こちらだけが引用の字数制限と原典照合の対象になる。
  [[slug]]      他の仮説記事への相互参照。

ブロックを先に確定させてからインラインを掛ける2フェーズ構成。
逆順にすると表の | やリストの - が壊れる。
"""

import html
import re

# ── ブロック判定用 ──────────────────────────────
FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.*?)[ \t]*#*$")
HR_RE = re.compile(r"^(-{3,}|\*{3,}|_{3,})$")
TABLE_ROW_RE = re.compile(r"^\|.*\|$")
TABLE_SEP_RE = re.compile(r"^\|[\s:\-|]+\|$")
LIST_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])[ \t]+(.*)$")

# この工房に固有の記法
QUOTE_OPEN_RE = re.compile(r"^:::quote[ \t]+(\d+)[ \t]*$")
QUOTE_CLOSE_RE = re.compile(r"^:::[ \t]*$")
XREF_RE = re.compile(r"\[\[([A-Za-z0-9][A-Za-z0-9\-_]*)\]\]")

ID_STRIP_RE = re.compile(r"[^\u4e00-\u9fff\u3040-\u30ffa-zA-Z0-9\s\-]")

# render() が張り替える変換中の文脈。ビルドは単一スレッドなのでこれで足りる。
_ctx = {"sources": [], "titles": {}, "xrefs": None, "quotes": None}


def make_heading_id(text, used):
    base = ID_STRIP_RE.sub("", text).strip()
    base = re.sub(r"\s+", "-", base).lower()[:60] or "section"
    count = used.get(base, 0)
    used[base] = count + 1
    return base if count == 0 else "%s-%d" % (base, count)


# ── インライン ──────────────────────────────────
def _xref(m):
    slug = m.group(1)
    if _ctx["xrefs"] is not None:
        _ctx["xrefs"].add(slug)
    title = (_ctx["titles"] or {}).get(slug)
    # 参照先が無いこと自体はビルドの検証が失敗させる。描画側は印を付けるだけ。
    cls = "xref" if title else "xref xref-missing"
    return '<a href="#/h/%s" class="%s">%s</a>' % (
        slug, cls, html.escape(title or slug, quote=False))


def inline(text):
    # エスケープは必ず最初。最後にやると自前で作ったタグまで壊れる。
    text = html.escape(text, quote=False)

    # インラインコードを退避しておく（中の ** や [[ ]] を変換させない）
    codes = []

    def _stash(m):
        codes.append(m.group(1))
        return "\x00C%d\x00" % (len(codes) - 1)

    text = re.sub(r"`([^`]+)`", _stash, text)

    text = XREF_RE.sub(_xref, text)

    # 太字は斜体より先。逆だと * ひとつを斜体が食う。
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text, flags=re.S)
    # 流用元は (?<![*\w]) だったが、\w が日本語にもマッチするため
    # 日本語の文中では斜体が一度も成立しなかった。この工房の記事は日本語なので外す。
    text = re.sub(r"(?<!\*)\*(?!\s)([^*]+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', text)

    text = re.sub(r"[ \t]{2,}\n", "<br>\n", text)

    for idx, code in enumerate(codes):
        text = text.replace("\x00C%d\x00" % idx, "<code>%s</code>" % code)
    return text


# ── ブロック ────────────────────────────────────
def _split_row(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    parts = re.split(r"(?<!\\)\|", s)
    return [p.strip().replace("\\|", "|") for p in parts]


def _aligns(sep_line):
    out = []
    for cell in _split_row(sep_line):
        left = cell.startswith(":")
        right = cell.endswith(":")
        if left and right:
            out.append("center")
        elif right:
            out.append("right")
        elif left:
            out.append("left")
        else:
            out.append(None)
    return out


def _cell(tag, value, align):
    style = ' style="text-align:%s"' % align if align else ""
    return "<%s%s>%s</%s>" % (tag, style, inline(value), tag)


def _table(lines, i):
    header = _split_row(lines[i])
    aligns = _aligns(lines[i + 1])
    i += 2
    body = []
    while i < len(lines) and TABLE_ROW_RE.match(lines[i].strip()):
        body.append(_split_row(lines[i]))
        i += 1

    width = len(header)
    aligns += [None] * (width - len(aligns))

    out = ['<div class="table-scroll"><table>', "<thead><tr>"]
    for idx, cell in enumerate(header):
        out.append(_cell("th", cell, aligns[idx]))
    out.append("</tr></thead>")
    if body:
        out.append("<tbody>")
        for row in body:
            row = (row + [""] * width)[:width]
            out.append("<tr>")
            for idx, cell in enumerate(row):
                out.append(_cell("td", cell, aligns[idx]))
            out.append("</tr>")
        out.append("</tbody>")
    out.append("</table></div>")
    return "".join(out), i


def _fence(lines, i, m):
    indent = len(m.group(1))
    marker = m.group(2)[0]
    length = len(m.group(2))
    lang = m.group(3).strip()
    close_re = re.compile(r"^\s*%s{%d,}\s*$" % (re.escape(marker), length))
    i += 1
    buf = []
    while i < len(lines):
        if close_re.match(lines[i]):
            i += 1
            break
        line = lines[i]
        buf.append(line[indent:] if line[:indent].strip() == "" else line)
        i += 1
    code = html.escape("\n".join(buf), quote=False)
    cls = ' class="language-%s"' % html.escape(lang, quote=True) if lang else ""
    return "<pre><code%s>%s\n</code></pre>" % (cls, code), i


def _srcquote(lines, i, m):
    """:::quote n 〜 ::: を原典引用として描画する。

    本文はインライン変換を通さない。原典の逐語であり、
    ここで太字や相互参照が効いてしまうと逐語でなくなるため。
    """
    idx = int(m.group(1))
    i += 1
    buf = []
    while i < len(lines) and not QUOTE_CLOSE_RE.match(lines[i].strip()):
        buf.append(lines[i])
        i += 1
    if i < len(lines):
        i += 1  # 閉じる ::: を食う

    text = "\n".join(buf).strip()
    if _ctx["quotes"] is not None:
        _ctx["quotes"].append({"index": idx, "text": text})

    sources = _ctx["sources"] or []
    src = sources[idx] if 0 <= idx < len(sources) else None
    label = src.get("label", "") if src else "（出典が解決できていません）"

    body = html.escape(text, quote=False).replace("\n", "<br>\n")
    return ('<figure class="srcquote"><blockquote>%s</blockquote>'
            '<figcaption>%s</figcaption></figure>'
            % (body, html.escape(label, quote=False))), i


def _quote(lines, i, sink, used):
    buf = []
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith(">"):
            buf.append(re.sub(r"^\s*>[ \t]?", "", line))
            i += 1
        elif line.strip() == "":
            break
        else:
            buf.append(line)  # lazy continuation
            i += 1
    return "<blockquote>%s</blockquote>" % blocks(buf, sink, used), i


def _list(lines, i, sink, used):
    m = LIST_RE.match(lines[i])
    base = len(m.group(1))
    ordered = m.group(2) not in ("-", "*", "+")
    items = []
    cur = None

    while i < len(lines):
        line = lines[i]
        m2 = LIST_RE.match(line)
        if m2 and len(m2.group(1)) == base:
            cur = [m2.group(3)]
            items.append(cur)
            i += 1
            continue
        if cur is None:
            break
        if not line.strip():
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                m3 = LIST_RE.match(lines[j])
                ind = len(lines[j]) - len(lines[j].lstrip())
                if (m3 and len(m3.group(1)) >= base) or ind > base:
                    cur.append("")
                    i += 1
                    continue
            break
        ind = len(line) - len(line.lstrip())
        if ind > base:
            cur.append(line[min(ind, base + 2):])
            i += 1
            continue
        break

    html_items = []
    for item in items:
        if len(item) == 1:
            html_items.append("<li>%s</li>" % inline(item[0]))
        else:
            inner = blocks(item, sink, used).strip()
            only_p = re.fullmatch(r"<p>([\s\S]*?)</p>", inner)
            if only_p:
                inner = only_p.group(1)
            html_items.append("<li>%s</li>" % inner)

    tag = "ol" if ordered else "ul"
    return "<%s>%s</%s>" % (tag, "".join(html_items), tag), i


def _is_table(lines, i):
    if i + 1 >= len(lines):
        return False
    if not TABLE_ROW_RE.match(lines[i].strip()):
        return False
    return bool(TABLE_SEP_RE.match(lines[i + 1].strip()))


def blocks(lines, sink, used):
    out = []
    para = []
    i = 0
    n = len(lines)

    def flush():
        if para:
            out.append("<p>%s</p>" % inline("\n".join(para)))
            del para[:]

    while i < n:
        line = lines[i]

        # 1. フェンスドコードを最優先（中の --- や + に一切触らない）
        m = FENCE_RE.match(line)
        if m:
            flush()
            chunk, i = _fence(lines, i, m)
            out.append(chunk)
            continue

        stripped = line.strip()

        # 2. 原典引用（フェンスの直後に見る。中身は逐語のまま通す）
        m = QUOTE_OPEN_RE.match(stripped)
        if m:
            flush()
            chunk, i = _srcquote(lines, i, m)
            out.append(chunk)
            continue

        # 3. 空行
        if not stripped:
            flush()
            i += 1
            continue

        # 4. 見出し
        m = HEADING_RE.match(line)
        if m:
            flush()
            level = len(m.group(1))
            body = inline(m.group(2).strip())
            plain = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", body))).strip()
            if level in (2, 3):
                hid = make_heading_id(plain, used)
                if sink is not None:
                    sink.append({"id": hid, "text": plain, "level": level})
                out.append('<h%d id="%s">%s</h%d>' % (level, hid, body, level))
            else:
                out.append("<h%d>%s</h%d>" % (level, body, level))
            i += 1
            continue

        # 5. 水平線（表セパレータより先に判定する）
        if HR_RE.match(stripped):
            flush()
            out.append("<hr>")
            i += 1
            continue

        # 6. 表（次行のセパレータまで見る2行先読みが必須）
        if _is_table(lines, i):
            flush()
            chunk, i = _table(lines, i)
            out.append(chunk)
            continue

        # 7. 引用（著者自身の強調。原典引用ではない）
        if stripped.startswith(">"):
            flush()
            chunk, i = _quote(lines, i, sink, used)
            out.append(chunk)
            continue

        # 8. リスト
        if LIST_RE.match(line):
            flush()
            chunk, i = _list(lines, i, sink, used)
            out.append(chunk)
            continue

        # 9. 段落（行末2スペースを消さないため strip しない）
        para.append(line.rstrip("\n"))
        i += 1

    flush()
    return "\n".join(out)


def render(md, sink=None, used=None, sources=None, titles=None,
           xrefs=None, quotes=None):
    """Markdown 本文を HTML にする。

    sink    h2/h3 の目次が積まれる
    sources frontmatter の sources。:::quote の出典ラベル解決に使う
    titles  slug -> title。[[slug]] の表示名に使う
    xrefs   set。本文中の [[slug]] が集まる（被リンクの逆算用）
    quotes  list。:::quote の {index, text} が集まる（検証用）
    """
    if used is None:
        used = {}
    # 既定値ではなく旧値へ戻す。既定値に戻すと、将来 render が再入したときに
    # 内側の後始末が外側の引用収集を黙って止めてしまう。
    saved = dict(_ctx)
    _ctx["sources"] = sources or []
    _ctx["titles"] = titles or {}
    _ctx["xrefs"] = xrefs
    _ctx["quotes"] = quotes
    try:
        return blocks(md.split("\n"), sink, used)
    finally:
        _ctx.update(saved)


def strip_tags(markup):
    """タグを落として素のテキストにする（抜粋・検索インデックス用）。"""
    text = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", markup)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()
