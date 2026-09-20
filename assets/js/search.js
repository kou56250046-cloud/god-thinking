/* 全文検索。外部ライブラリは使わない。
   日本語は語の切れ目が無いので、文字単位の編集距離ではなくバイグラムで寄せる。

   流用元（四柱推命鑑定）から、インデックスの対象フィールドを仮説記事用に差し替え、
   スニペットは HTML 文字列ではなく区間の配列を返すようにした。
   文字列を組み立てないので、描画側が HTML 文字列の代入を使わずに済む。 */
window.Search = (function () {

  var index = null;

  function bigrams(text) {
    var set = Object.create(null);
    for (var i = 0; i < text.length - 1; i++) set[text.slice(i, i + 2)] = true;
    if (text.length === 1) set[text] = true;
    return set;
  }

  function build() {
    if (index) return index;
    index = Store.hypotheses.map(function (h) {
      var plain = U.normalize(h.plain || '');
      return {
        article: h,
        title: U.normalize(h.title),
        claim: U.normalize(h.claim || ''),
        lens: (h.lens || []).map(U.normalize),
        topics: (h.topics || []).map(U.normalize),
        facets: U.normalize((h.mode || '') + ' ' + (h.terrain || '')),
        plain: plain,
        grams: bigrams(plain.slice(0, 4000) + ' ' + U.normalize(h.title))
      };
    });
    return index;
  }

  function occurrences(haystack, needle) {
    if (!needle) return 0;
    var count = 0, pos = 0;
    for (;;) {
      var found = haystack.indexOf(needle, pos);
      if (found === -1) break;
      count++;
      pos = found + needle.length;
    }
    return count;
  }

  /* 語側の bigram のうち、文書に含まれている割合。

     以前は分母に文書側の bigram 数を足していたが、記事 1 本で 1800 個あるため
     分母が常時 +45 され、2〜5 文字の語は閾値にまるで届かなかった。
     日本語の検索語は 2〜5 文字が大半なので、タイポ許容が最も要る場面で
     曖昧検索が効いていなかった。文書の長さに依存しない割合に変える。 */
  function dice(aSet, term) {
    var b = bigrams(term);
    var keys = Object.keys(b);
    if (!keys.length) return 0;
    var shared = 0;
    keys.forEach(function (k) { if (aSet[k]) shared++; });
    return shared / keys.length;
  }

  function scoreItem(item, terms, fuzzy) {
    var total = 0;
    for (var i = 0; i < terms.length; i++) {
      var t = terms[i];
      var s = 0;
      if (item.title.indexOf(t) !== -1) s += item.title.indexOf(t) === 0 ? 150 : 100;
      if (item.claim.indexOf(t) !== -1) s += 80;
      item.lens.forEach(function (v) { if (v === t) s += 60; else if (v.indexOf(t) !== -1) s += 40; });
      item.topics.forEach(function (v) { if (v === t) s += 60; else if (v.indexOf(t) !== -1) s += 40; });
      if (item.facets.indexOf(t) !== -1) s += 40;
      var hits = occurrences(item.plain, t);
      if (hits) s += Math.min(30, 6 * hits);
      if (!s && fuzzy && t.length >= 2) {
        // 割合なので閾値の意味が変わる。6 割の bigram が一致したら拾う。
        var d = dice(item.grams, t);
        if (d >= 0.6) s += Math.round(40 * d);
      }
      if (!s) return -1;         // 語は AND。ひとつでも外れたら落とす
      total += s;
    }
    return total;
  }

  function query(text, limit) {
    var terms = U.normalize(text).split(/[\s　]+/).filter(Boolean);
    if (!terms.length) return [];
    var items = build();

    function run(fuzzy) {
      var out = [];
      items.forEach(function (item) {
        var s = scoreItem(item, terms, fuzzy);
        if (s > 0) out.push({ item: item, score: s });
      });
      return out;
    }

    var results = run(false);
    if (!results.length) results = run(true);

    results.sort(function (a, b) {
      if (b.score !== a.score) return b.score - a.score;
      return a.item.article.slug.localeCompare(b.item.article.slug);
    });

    return results.slice(0, limit || 24).map(function (r) {
      return {
        article: r.item.article,
        score: r.score,
        snippet: snippet(r.item.article.plain || '', terms)
      };
    });
  }

  /**
   * ヒット箇所の前後を切り出し、[{text, mark}] の区間に分けて返す。
   * 描画側はこれを textContent と <mark> に落とすだけでよい。
   */
  /**
   * 正規化後の文字列と、そこから元の文字列への位置の対応表を作る。
   *
   * 以前は norm と plain の長さが一致するかどうかだけを見て、
   * 違えば先頭 150 字を返していた。しかし ㍻→平成（1→2）と ｶﾞ→ガ（2→1）が
   * 同数あると長さが一致してしまい、位置がずれたままマークを打つことになる。
   * 1 文字ずつ正規化して対応表を持てば、長さがどう変わっても位置は正しい。
   */
  function normMap(plain) {
    var text = '', idx = [];
    for (var i = 0; i < plain.length; i++) {
      var n = U.normalize(plain[i]);
      for (var j = 0; j < n.length; j++) { text += n[j]; idx.push(i); }
    }
    idx.push(plain.length);   // 終端。区間の右端を引くため
    return { text: text, idx: idx };
  }

  function snippet(plain, terms) {
    var nm = normMap(plain);
    var at = -1;
    for (var i = 0; i < terms.length; i++) {
      var p = nm.text.indexOf(terms[i]);
      if (p !== -1 && (at === -1 || p < at)) at = p;
    }
    if (at === -1) {
      return [{ text: plain.slice(0, 150) + (plain.length > 150 ? '…' : ''), mark: false }];
    }

    var hit = nm.idx[at];                                   // 元の文字列での位置
    var from = Math.max(0, hit - 50);
    var to = Math.min(plain.length, hit + 130);
    var slice = plain.slice(from, to);

    // 区間は正規化側で探し、対応表で元の位置へ戻す
    var marks = [];
    terms.forEach(function (t) {
      var pos = 0;
      for (;;) {
        var f = nm.text.indexOf(t, pos);
        if (f === -1) break;
        var s = nm.idx[f], e = nm.idx[f + t.length];
        if (s >= from && e <= to) marks.push([s - from, e - from]);
        pos = f + t.length;
      }
    });

    // 重なる区間はまとめる。捨てると後ろの語がマークされない。
    marks.sort(function (a, b) { return a[0] - b[0] || a[1] - b[1]; });
    var merged = [];
    marks.forEach(function (m) {
      var last = merged[merged.length - 1];
      if (last && m[0] <= last[1]) last[1] = Math.max(last[1], m[1]);
      else merged.push([m[0], m[1]]);
    });

    var out = [], cursor = 0;
    if (from > 0) out.push({ text: '…', mark: false });
    merged.forEach(function (m) {
      if (m[0] > cursor) out.push({ text: slice.slice(cursor, m[0]), mark: false });
      out.push({ text: slice.slice(m[0], m[1]), mark: true });
      cursor = m[1];
    });
    if (cursor < slice.length) out.push({ text: slice.slice(cursor), mark: false });
    if (to < plain.length) out.push({ text: '…', mark: false });
    return out;
  }

  /* 区間の配列を DOM に落とす。 */
  function renderSnippet(segments) {
    return U.frag(segments.map(function (s) {
      return s.mark ? U.el('mark', { text: s.text }) : document.createTextNode(s.text);
    }));
  }

  return { query: query, snippet: snippet, renderSnippet: renderSnippet };
})();
