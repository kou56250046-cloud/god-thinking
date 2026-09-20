/* 画面をまたいで使う小さな部品。すべて DOM ノードを返す。 */
window.Partials = (function () {

  /* mode は読者が最初に見るべきもの。比喩と構造的対応を色で分ける。 */
  function modeBadge(mode) {
    return U.el('span', { class: 'badge badge--mode-' + mode, text: mode });
  }

  function terrainBadge(terrain) {
    return U.el('span', { class: 'badge badge--terrain', text: terrain });
  }

  function chip(text) {
    return U.el('span', { class: 'chip', text: text });
  }

  function lensLine(lens) {
    return U.el('span', { class: 'article-meta__lens', text: '観点: ' + lens.join(' / ') });
  }

  function link(slug, text) {
    return U.el('a', { href: '#/h/' + slug, text: text });
  }

  /* 一覧に並ぶカード。 */
  function card(h) {
    return U.el('article', { class: 'card' }, [
      U.el('h3', { class: 'card__title' }, link(h.slug, h.title)),
      U.el('p', { class: 'card__claim', text: h.claim }),
      U.el('div', { class: 'card__foot' }, [
        modeBadge(h.mode),
        terrainBadge(h.terrain),
        h.lens.map(chip),
        U.el('span', { class: 'chip', text: h.chars + ' 字' })
      ])
    ]);
  }

  function empty(mark, message, hint) {
    return U.el('div', { class: 'empty' }, [
      U.el('span', { class: 'empty__mark', text: mark }),
      U.el('p', { text: message }),
      hint && U.el('p', null, hint)
    ]);
  }

  /* 記事が 1 本も無いとき。ビルド前の状態でも画面が壊れないようにする。 */
  function noData() {
    return empty('—', 'まだ仮説がありません。',
      [U.el('code', { text: 'python scripts/build.py' }), ' を実行すると記事が読み込まれます。']);
  }

  return {
    modeBadge: modeBadge, terrainBadge: terrainBadge, chip: chip,
    lensLine: lensLine, link: link, card: card, empty: empty, noData: noData
  };
})();
