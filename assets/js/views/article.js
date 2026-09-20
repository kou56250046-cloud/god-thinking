/* 記事本文の画面。

   **このファイルだけが HTML 文字列をそのまま要素へ入れる。**
   入るのは scripts/build.py が hypotheses/*.md から生成した本文であり、
   外部由来ではない。エスケープはビルド側で済ませてある。
   他の場所では一切使わない（.claude/CLAUDE.md の制約）。 */
window.Views = window.Views || {};

Views.article = (function () {

  function section(title, items) {
    if (!items || !items.length) return null;
    return U.frag([
      U.el('h3', { text: title }),
      U.el('ul', null, items.map(function (t) { return U.el('li', { text: t }); }))
    ]);
  }

  /* 出典。anchor は生成物に無いので、ラベルとファイル名だけを出す。 */
  function sources(h) {
    var list = h.sources || [];
    if (!list.length) return null;
    return U.frag([
      U.el('h3', { text: '出典' }),
      U.el('ul', null, list.map(function (s) {
        return U.el('li', null, [s.label, U.el('br'), U.el('code', { text: s.file })]);
      }))
    ]);
  }

  /* 地雷。触れていない判断も残す。書き忘れと区別するため。 */
  function mines(h) {
    var all = h.mines || [];
    var touched = all.filter(function (m) { return m.touches; });
    return U.frag([
      U.el('h3', { text: '原典が否定する立場との関係' }),
      U.el('p', { class: 'card__claim',
        text: touched.length
          ? touched.length + ' 件に触れている。詳細は地雷一覧を参照。'
          : '全 ' + all.length + ' 件を検討し、いずれにも触れていない。' }),
      U.el('p', null, U.el('a', { href: '#/mines', text: '地雷一覧を見る' }))
    ]);
  }

  function backlinks(h) {
    var list = h.backlinks || [];
    if (!list.length) return null;
    return U.frag([
      U.el('h3', { text: 'この仮説を参照している仮説' }),
      U.el('ul', null, list.map(function (slug) {
        var other = Store.bySlug[slug];
        return U.el('li', null, Partials.link(slug, other ? other.title : slug));
      }))
    ]);
  }

  function render(route) {
    var h = Store.bySlug[route.segs[1]];
    if (!h) return null;

    var prose = U.el('div', { class: 'prose' });
    prose.innerHTML = h.bodyHtml;   // ← 許可された唯一の箇所

    var aside = U.el('aside', { class: 'article-aside' });

    var node = U.frag([
      U.el('header', { class: 'page-head' }, [
        U.el('p', { class: 'page-head__eyebrow', text: (h.topics || []).join(' / ') }),
        U.el('h1', { text: h.title })
      ]),
      U.el('div', { class: 'article-meta' }, [
        Partials.modeBadge(h.mode),
        Partials.terrainBadge(h.terrain),
        Partials.lensLine(h.lens || [])
      ]),
      U.el('p', { class: 'article-claim', text: h.claim }),
      U.el('div', { class: 'article-layout' }, [
        U.el('div', null, [
          prose,
          U.el('footer', { class: 'article-foot' }, [
            sources(h),
            section('科学側の典拠', h.science || []),
            section('反証条件', h.falsifiers || []),
            section('開かれた問い', h.questions || []),
            mines(h),
            backlinks(h)
          ])
        ]),
        aside
      ])
    ]);

    return {
      title: h.title,
      node: node,
      mount: function (root) {
        // 目次は本文の見出しから組む。データに持たせない。
        var toc = Toc.build(prose);
        if (toc) aside.appendChild(toc);
        return Toc.mount(root);
      }
    };
  }

  return { render: render };
})();
