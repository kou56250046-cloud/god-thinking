"""仮説記事の検証。design の検査表 25 項目。

方針が二つある。

1. **失敗は全件集めてから返す。** 1 件目で止めると、直しては走らせ直す往復が増える。
2. **照合は空白類を除去した正規化後に行う。** 原理講論は 1 節が 1 行（10 万バイト級）、
   統一思想の見出しは OCR で空白が乱れている。空白を無視しないと照合が成立しない。
"""

import io
import json
import os
import re

import markdown as M

# frontmatter に必ず要るキー。ここに無いキーが混じっていても失敗させる（検査 25）。
REQUIRED_KEYS = [
    "title", "claim", "lens", "topics", "mode", "terrain",
    "sources", "science", "mines", "known", "falsifiers", "questions", "related",
]

# 各キーに期待する型。キーの有無だけ見ても、型が違えば結局壊れる。
EXPECTED_TYPES = {
    "title": "str", "claim": "str", "mode": "str", "terrain": "str",
    "lens": "list[str]", "topics": "list[str]", "science": "list[str]",
    "falsifiers": "list[str]", "questions": "list[str]",
    "related": "list[str]", "known": "list[str]",
    "sources": "list[dict]", "mines": "list[dict]",
}

# 本文に必ず要る節。この順で並んでいること。
REQUIRED_SECTIONS = [
    "問い",
    "主張",
    "前提",
    "導出",
    "原典との突き合わせ",
    "この仮説が言っていないこと",
    "反証条件",
    "開かれた問い",
]

ANCHOR_MIN, ANCHOR_MAX = 10, 40
SECTION_MIN = 200
BODY_MIN, BODY_MAX = 3000, 8000
QUOTE_MAX, QUOTE_TOTAL_MAX = 200, 600
# 同じ原典ファイル内で、引用どうしが最低これだけ離れていること。
# 近い箇所を継ぎ足して連続した本文を再構成させないための下限。
QUOTE_MIN_GAP = 500

WS_RE = re.compile(r"[\s　]+")
H2_RE = re.compile(r"^##[ \t]+(.+?)[ \t]*$")


def norm(s):
    """照合用の正規化。空白類をすべて落とす。"""
    return WS_RE.sub("", s or "")


def count_chars(s):
    """字数は空白類を除いて数える。改行の入れ方で増減させないため。"""
    return len(norm(s))


# ── 読み込み ────────────────────────────────────
def load_corpus(docs_dir):
    """原典を正規化済みの本文として読む。キーは docs/ からの相対パス。

    **読むだけ。docs/ は絶対に書き換えない。**
    照合しかしないので、正規化後の文字列だけを持てば足りる。
    """
    corpus = {}
    for root, _dirs, files in os.walk(docs_dir):
        for name in files:
            if not name.endswith(".md"):
                continue
            full = os.path.join(root, name)
            rel = os.path.relpath(full, docs_dir).replace("\\", "/")
            corpus[rel] = norm(io.open(full, encoding="utf-8").read())
    return corpus


def split_frontmatter(text):
    """先頭の --- 〜 --- を JSON の frontmatter として切り出す。"""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, text, "先頭が --- で始まっていない"
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1:]), None
    return None, text, "frontmatter が --- で閉じていない"


def load_article(path):
    """1 記事を読む。frontmatter が壊れていても例外にせず error に載せる。"""
    slug = os.path.splitext(os.path.basename(path))[0]
    text = io.open(path, encoding="utf-8").read()
    raw, body, err = split_frontmatter(text)
    if err:
        return {"slug": slug, "path": path, "fm": None, "body": body, "fm_error": err}
    try:
        fm = json.loads(raw)
    except ValueError as e:
        return {"slug": slug, "path": path, "fm": None, "body": body,
                "fm_error": "JSON として読めない: %s" % e}
    return {"slug": slug, "path": path, "fm": fm, "body": body, "fm_error": None}


def split_sections(body):
    """## 見出しごとに本文を切る。戻りは [(見出し, 本文), ...] の出現順。"""
    out = []
    cur = None
    for line in body.split("\n"):
        m = H2_RE.match(line)
        if m:
            cur = [m.group(1).strip(), []]
            out.append(cur)
        elif cur is not None:
            cur[1].append(line)
    return [(h, "\n".join(b)) for h, b in out]


# ── 検証 ────────────────────────────────────────
class Report(object):
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.checked = {}

    def fail(self, where, code, msg):
        self.errors.append({"where": where, "code": code, "msg": msg})

    def warn(self, where, msg):
        self.warnings.append({"where": where, "msg": msg})

    def count(self, code, n=1):
        self.checked[code] = self.checked.get(code, 0) + n


def validate_cells(studio, filled, rep):
    """検査 26/27: 記事の無いマスすべてに判断が書かれているか。

    空白を「手つかず」のまま残さない。地雷を全件列挙させるのと同じ考え方で、
    書いていないことと、書かないと判断したことを区別する。
    """
    where = "config/studio.json cells"
    seen = {}
    for c in studio.get("cells", []):
        rep.count("C27")
        key = (c.get("topic"), c.get("lens"))
        if c.get("topic") not in studio["topics"] or c.get("lens") not in studio["lenses"]:
            rep.fail(where, "C27", "cells に未定義の論点／観点: %s × %s" % key)
            continue
        if key in seen:
            rep.fail(where, "C27", "cells に同じマスが 2 回ある: %s × %s" % key)
            continue
        if c.get("status") not in ("planned", "na"):
            rep.fail(where, "C27",
                     "%s × %s の status が planned / na のいずれでもない: %r"
                     % (key[0], key[1], c.get("status")))
            continue
        if not (c.get("note") or "").strip():
            rep.fail(where, "C27", "%s × %s に理由（note）が無い" % key)
            continue
        seen[key] = c

    for topic in studio["topics"]:
        for lens in studio["lenses"]:
            if (topic, lens) in filled:
                continue
            rep.count("C26")
            if (topic, lens) not in seen:
                rep.fail(where, "C26",
                         "記事も判断も無いマスがある: %s × %s\n"
                         "      status（planned / na）と note を cells に書く" % (topic, lens))
    return seen


def validate_studio(studio, corpus, rep, anchors=None):
    """検査 24: studio.json 側の出典も、記事と同じ実在検査に掛ける。"""
    table = (anchors or {}).get("studio", {})
    for group in ("mines", "known"):
        for entry in studio.get(group, []):
            where = "config/studio.json %s" % entry.get("id", "?")
            src = entry.get("source") or {}
            _check_source(src, where, "C24", corpus, rep, table.get(entry.get("id")))
            rep.count("C24")


def load_anchors(path):
    """anchor の控えを読む。

    anchor は原典の逐語である。引用の体裁を持たないので公開物には出さない。
    検証にだけ要るので、公開対象外のファイルに分けてある（.gitignore）。
    無ければ anchor の照合は飛ばす。引用本文の照合は影響を受けない。
    """
    if not os.path.exists(path):
        return None
    return json.load(io.open(path, encoding="utf-8"))


def _check_source(src, where, code, corpus, rep, anchor=None):
    """出典 1 件を検査する。ファイルの実在・anchor の長さ・anchor の実在。

    anchor は引数で渡す。記事の frontmatter には持たせない。
    """
    f = src.get("file")
    if not f:
        rep.fail(where, code, "source に file が要る")
        return
    if anchor is None:
        # 控えが無い。ファイルの実在だけ確かめて戻る。
        if corpus.get(f) is None:
            rep.fail(where, code, "原典に存在しないファイル: %s" % f)
        return
    body = corpus.get(f)
    if body is None:
        rep.fail(where, code, "原典に存在しないファイル: %s" % f)
        return
    # 長さも照合と同じ正規化後で測る。空白込みで数えると
    # 「神 は 原 理 の 主 管 者」のような実質 8 字の anchor が下限を通ってしまう。
    n = count_chars(anchor)
    if not (ANCHOR_MIN <= n <= ANCHOR_MAX):
        rep.fail(where, code,
                 "anchor は %d〜%d 字（現在 %d 字）: %s"
                 % (ANCHOR_MIN, ANCHOR_MAX, n, anchor[:30]))
        return
    hits = body.count(norm(anchor))
    if hits == 0:
        rep.fail(where, code,
                 "anchor が原典に見つからない\n"
                 "      探した先: %s\n"
                 "      探した文字列: %s" % (f, anchor))
        return
    rep.count("anchor_hits", hits)


def validate_article(art, studio, corpus, slugs, rep, anchors=None):
    slug = art["slug"]
    where = "hypotheses/%s.md" % slug

    # 検査 1: frontmatter が JSON として読めるか
    rep.count("C01")
    if art["fm_error"]:
        rep.fail(where, "C01", art["fm_error"])
        return
    fm = art["fm"]
    body = art["body"]

    # 検査 2: 必須キーが揃っているか
    rep.count("C02")
    missing = [k for k in REQUIRED_KEYS if k not in fm]
    if missing:
        rep.fail(where, "C02", "frontmatter のキーが足りない: %s" % ", ".join(missing))

    # 検査 25: 未知のキーが混じっていないか（生成物の許可リストを守るため）
    rep.count("C25")
    unknown = [k for k in fm if k not in REQUIRED_KEYS]
    if unknown:
        rep.fail(where, "C25", "frontmatter に未知のキー: %s" % ", ".join(unknown))

    if missing:
        return  # キーが無いまま先へ進むと例外だらけになる

    # 検査 2b: 型が期待どおりか
    # キーの有無しか見ていないと、型違いは「例外で落ちる」か「黙って誤出力」になる。
    # 例: questions が文字列だと 1 文字ずつ別々の問いとして出力されてしまう。
    rep.count("C02T")
    wrong = []
    for key, kind in EXPECTED_TYPES.items():
        v = fm[key]
        if kind == "str" and not isinstance(v, str):
            wrong.append("%s は文字列であること（現在 %s）" % (key, type(v).__name__))
        elif kind == "list[str]":
            if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
                wrong.append("%s は文字列の配列であること（現在 %s）" % (key, type(v).__name__))
        elif kind == "list[dict]":
            if not isinstance(v, list) or not all(isinstance(x, dict) for x in v):
                wrong.append("%s はオブジェクトの配列であること（現在 %s）" % (key, type(v).__name__))
    if wrong:
        rep.fail(where, "C02T", "frontmatter の型が違う\n      " + "\n      ".join(wrong))
        return  # 型が違うまま進むと例外になる

    # 検査 3: 経験的主張は置かない
    rep.count("C03")
    if fm["mode"] == "経験的主張":
        rep.fail(where, "C03",
                 "mode が 経験的主張。検証不能な現実世界の主張は置かない（非目標）")

    # 検査 4: 語彙が studio.json の中にあるか
    rep.count("C04")
    for key, vocab in (("lens", "lenses"), ("topics", "topics")):
        for v in fm[key]:
            if v not in studio[vocab]:
                rep.fail(where, "C04", "%s に未定義の値: %s" % (key, v))
    if fm["mode"] not in studio["modes"]:
        rep.fail(where, "C04", "mode に未定義の値: %s" % fm["mode"])
    if fm["terrain"] not in studio["terrains"]:
        rep.fail(where, "C04", "terrain に未定義の値: %s" % fm["terrain"])
    if not fm["lens"]:
        rep.fail(where, "C04", "lens が空")
    if not fm["topics"]:
        rep.fail(where, "C04", "topics が空")

    # 検査 5: 必須 8 節がこの順で揃っているか
    rep.count("C05")
    sections = split_sections(body)
    names = [h for h, _ in sections]
    if names != REQUIRED_SECTIONS:
        rep.fail(where, "C05",
                 "必須の節が揃っていない\n"
                 "      期待: %s\n"
                 "      実際: %s" % (" / ".join(REQUIRED_SECTIONS), " / ".join(names) or "（なし）"))

    # 検査 6: 各節が 200 字以上か
    rep.count("C06")
    for h, b in sections:
        n = count_chars(b)
        if n < SECTION_MIN:
            rep.fail(where, "C06", "節「%s」が %d 字（%d 字以上）" % (h, n, SECTION_MIN))

    # 検査 7: 本文の総字数
    rep.count("C07")
    total = count_chars(body)
    if not (BODY_MIN <= total <= BODY_MAX):
        rep.fail(where, "C07",
                 "本文が %d 字（%d〜%d 字）" % (total, BODY_MIN, BODY_MAX))

    # 検査 8: sources が 2 件以上
    rep.count("C08")
    if len(fm["sources"]) < 2:
        rep.fail(where, "C08", "sources が %d 件（2 件以上）" % len(fm["sources"]))

    # 検査 9〜11: 出典の実在と anchor
    art_anchors = (anchors or {}).get("articles", {}).get(slug)
    for idx, src in enumerate(fm["sources"]):
        rep.count("C09_11")
        a = art_anchors[idx] if art_anchors and idx < len(art_anchors) else None
        _check_source(src, "%s sources[%d]" % (where, idx), "C09_11", corpus, rep, a)

    # 本文を一度変換して、引用と相互参照を renderer と同じ見方で取り出す
    quotes, xrefs = [], set()
    M.render(body, sources=fm["sources"], titles={s: s for s in slugs},
             xrefs=xrefs, quotes=quotes)

    # 検査 12b: ::: で始まる行が、すべて正しい記法になっているか
    # 記法を外すと段落に化け、引用の照合も字数制限もすべて回避されてしまう。
    # 未知のディレクティブを黙殺しないこと自体が、著作権の歯止めになっている。
    rep.count("C12D")
    depth = 0
    for i, line in enumerate(body.split("\n"), 1):
        s = line.strip()
        if not s.startswith(":::"):
            continue
        if depth == 0:
            if M.QUOTE_OPEN_RE.match(s):
                depth = 1
            else:
                rep.fail(where, "C12D",
                         "%d 行目の ::: が引用の記法として読めない\n"
                         "      書いてあるもの: %s\n"
                         "      正しい形: :::quote <sources の添字>" % (i, s))
        else:
            if M.QUOTE_CLOSE_RE.match(s):
                depth = 0
            else:
                rep.fail(where, "C12D",
                         "%d 行目: 引用が閉じる前に別の ::: が現れた: %s" % (i, s))
    if depth != 0:
        rep.fail(where, "C12D", "引用が ::: で閉じられていないまま本文が終わっている")

    # 検査 12: :::quote が 1 箇所以上
    rep.count("C12")
    if not quotes:
        rep.fail(where, "C12", ":::quote が 1 箇所も無い")

    total_q = 0
    used_idx = {}
    placed = {}
    for q in quotes:
        idx, text = q["index"], q["text"]

        # 検査 13: 添字が sources の範囲内か
        rep.count("C13")
        if not (0 <= idx < len(fm["sources"])):
            rep.fail(where, "C13", ":::quote %d は sources の範囲外" % idx)
            continue

        # 検査 14: 引用本文が原典に逐語で実在するか
        rep.count("C14")
        f = fm["sources"][idx].get("file")
        corpus_body = corpus.get(f)
        if corpus_body is None:
            rep.fail(where, "C14", ":::quote %d の出典ファイルが無い: %s" % (idx, f))
        elif norm(text) not in corpus_body:
            rep.fail(where, "C14",
                     ":::quote %d の引用が原典と一致しない（誤記・要約・捏造）\n"
                     "      照合先: %s\n"
                     "      引用: %s" % (idx, f, text[:40]))

        # 検査 15: 1 箇所 200 字以内
        rep.count("C15")
        n = count_chars(text)
        if n > QUOTE_MAX:
            rep.fail(where, "C15", ":::quote %d が %d 字（%d 字以内）" % (idx, n, QUOTE_MAX))
        total_q += n

        # 検査 17: 同一の sources[n] からの引用は 1 記事 1 箇所まで
        rep.count("C17")
        used_idx[idx] = used_idx.get(idx, 0) + 1
        if used_idx[idx] == 2:
            rep.fail(where, "C17", "sources[%d] からの引用が 2 箇所ある（1 箇所まで）" % idx)

        # 原典上の位置を控える。検査 17b で近接を見るために使う。
        if corpus_body is not None:
            pos = corpus_body.find(norm(text))
            if pos >= 0:
                placed.setdefault(f, []).append((pos, pos + len(norm(text)), idx))

    # 検査 17b: 引用どうしが原典上で近接していないか
    # 守りたいのは「連続した本文を再構成させない」ことであって、
    # 同じ文献を二度引くこと自体ではない。別々の節からの引用は連続していない。
    # 近さを直接見るほうが、ファイル単位で禁じるより実態に合う。
    rep.count("C17B")
    for f, spans in placed.items():
        spans.sort()
        for a, b in zip(spans, spans[1:]):
            gap = b[0] - a[1]
            if gap < QUOTE_MIN_GAP:
                rep.fail(where, "C17B",
                         "引用どうしが原典上で近すぎる（間隔 %d 字、%d 字以上あけること）\n"
                         "      %s の sources[%d] と sources[%d]\n"
                         "      連続した本文を継ぎ足して再構成できてしまう"
                         % (gap, QUOTE_MIN_GAP, f, a[2], b[2]))

    # 検査 16: 引用合計
    rep.count("C16")
    if total_q > QUOTE_TOTAL_MAX:
        rep.fail(where, "C16",
                 "引用の合計が %d 字（%d 字以内）" % (total_q, QUOTE_TOTAL_MAX))

    # 検査 18: 反証条件
    rep.count("C18")
    if not fm["falsifiers"]:
        rep.fail(where, "C18", "falsifiers が空。反証条件のない仮説は置かない")

    # 検査 19: 開かれた問い
    rep.count("C19")
    if not fm["questions"]:
        rep.fail(where, "C19", "questions が空")

    # 検査 20: 参照先の実在
    rep.count("C20")
    for s in fm["related"]:
        if s not in slugs:
            rep.fail(where, "C20", "related の参照先が無い: %s" % s)
        elif s == slug:
            rep.fail(where, "C20", "related が自分自身を指している")
    for s in sorted(xrefs):
        if s not in slugs:
            rep.fail(where, "C20", "[[%s]] の参照先が無い" % s)
        elif s == slug:
            rep.fail(where, "C20", "[[%s]] が自分自身を指している" % s)

    # 検査 21/22: 地雷は全件を列挙する
    rep.count("C21")
    mine_ids = [m["id"] for m in studio["mines"]]
    listed = {}
    for entry in fm["mines"]:
        if not isinstance(entry, dict) or "id" not in entry:
            rep.fail(where, "C21", "mines の要素に id が無い")
            continue
        # 後勝ちで上書きすると、先に書いた判断が検査されないまま出力に残る。
        if entry["id"] in listed:
            rep.fail(where, "C21",
                     "mines に同じ id が 2 回ある: %s。"
                     "重複すると片方が検査されないまま出力に載る" % entry["id"])
            continue
        listed[entry["id"]] = entry
    lack = [i for i in mine_ids if i not in listed]
    if lack:
        rep.fail(where, "C21",
                 "mines に列挙されていない地雷: %s\n"
                 "      全 %d 件を touches と reason つきで列挙する"
                 % (", ".join(lack), len(mine_ids)))
    for mid, entry in listed.items():
        if mid not in mine_ids:
            rep.fail(where, "C21", "mines に未定義の id: %s" % mid)
            continue
        if "touches" not in entry or "reason" not in entry:
            rep.fail(where, "C21", "mines[%s] に touches と reason が要る" % mid)
            continue
        # 真偽値でないと truthy 判定になり、文字列 "false" が「触れている」に化ける。
        if not isinstance(entry["touches"], bool):
            rep.fail(where, "C21",
                     "mines[%s] の touches が真偽値でない（現在 %r）。"
                     "文字列は真として扱われ、逆の意味で表示される"
                     % (mid, entry["touches"]))
            continue
        rep.count("C22")
        if entry["touches"] and not (entry["reason"] or "").strip():
            rep.fail(where, "C22",
                     "mines[%s] は touches が真。触れる理由を書く" % mid)

    # 検査 23: 既出の対応づけを扱うなら terrain は 拡張
    rep.count("C23")
    known_ids = {k["id"] for k in studio["known"]}
    for kid in fm["known"]:
        if kid not in known_ids:
            rep.fail(where, "C23", "known に未定義の id: %s" % kid)
        elif fm["terrain"] != "拡張":
            rep.fail(where, "C23",
                     "known に %s を挙げているのに terrain が「%s」。"
                     "原典が既に持つ対応づけを扱うなら「拡張」にする" % (kid, fm["terrain"]))

    # 検査（警告のみ）: 本文が上限に近いか
    if BODY_MAX * 0.9 <= total <= BODY_MAX:
        rep.warn(where, "本文が %d 字。上限 %d 字に近い" % (total, BODY_MAX))


def validate_all(articles, studio, corpus, anchors=None):
    rep = Report()
    slugs = {a["slug"] for a in articles}
    if anchors is None:
        rep.warn("config/anchors.local.json",
                 "anchor の控えが無いので、原典との照合を飛ばした（引用本文の照合は行う）")
    validate_studio(studio, corpus, rep, anchors)
    for art in articles:
        validate_article(art, studio, corpus, slugs, rep, anchors)
    return rep
