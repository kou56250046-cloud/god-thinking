/* 観点マトリクス。論点 × 観点。

   **空白のマスを見せることがこの画面の目的である。**
   埋まったマスより、まだ誰も書いていないマスのほうが情報量が多い。
   空白は背景色とラベルの両方で区別する（色だけに頼らない）。 */
window.Views = window.Views || {};

Views.matrix = (function () {

  function cell(c) {
    if (c.status === 'filled') {
      return U.el('td', { class: 'is-filled' }, c.slugs.map(function (slug) {
        var h = Store.bySlug[slug];
        return U.el('a', {
          class: 'matrix__slug',
          href: '#/h/' + slug,
          title: h ? h.title : slug,
          text: h ? h.title : slug
        });
      }));
    }
    if (c.status === 'planned') {
      // 次に書くべきマス。理由を title に入れておくと、何を書くかが分かる。
      return U.el('td', { class: 'is-planned', title: c.note || '' },
        U.el('span', { class: 'matrix__label', text: '未着手' }));
    }
    return U.el('td', { class: 'is-na', title: c.note || '' },
      U.el('span', { class: 'matrix__label', text: '該当なし' }));
  }

  function render() {
    var studio = Store.studio;
    var cells = Store.matrix;
    if (!cells.length) {
      return { title: 'マトリクス', node: U.frag([
        Router.pageHead('Matrix', '観点マトリクス', ''), Partials.noData()]) };
    }

    var byKey = Object.create(null);
    cells.forEach(function (c) { byKey[c.topic + '\u0000' + c.lens] = c; });

    function count(st) {
      return cells.filter(function (c) { return c.status === st; }).length;
    }
    var filled = count('filled'), planned = count('planned'), na = count('na');

    var head = U.el('tr', null, [
      // バックスラッシュは日本語フォントで円記号に化けるので使わない
      U.el('th', { class: 'matrix__rowhead', text: '論点 ／ 観点' }),
      studio.lenses.map(function (l) { return U.el('th', { text: l }); })
    ]);

    var rows = studio.topics.map(function (topic) {
      return U.el('tr', null, [
        U.el('th', { class: 'matrix__rowhead', text: topic }),
        studio.lenses.map(function (lens) {
          return cell(byKey[topic + '\u0000' + lens] || { slugs: [] });
        })
      ]);
    });

    var legend = U.el('div', { class: 'matrix__legend' }, [
      U.el('span', null, [U.el('span', { class: 'matrix__swatch matrix__swatch--filled' }), '仮説がある']),
      U.el('span', null, [U.el('span', { class: 'matrix__swatch matrix__swatch--planned' }), '未着手（問いは立つ）']),
      U.el('span', null, [U.el('span', { class: 'matrix__swatch matrix__swatch--na' }), '該当なし（理由つき・マスに触れると出る）'])
    ]);

    return {
      title: '観点マトリクス',
      node: U.frag([
        U.el('header', { class: 'page-head' }, [
          U.el('p', { class: 'page-head__eyebrow', text: 'Matrix' }),
          U.el('h1', { text: '観点マトリクス' }),
          U.el('p', { class: 'page-head__lead',
            text: studio.topics.length + ' 論点 × ' + studio.lenses.length + ' 観点 = '
                + cells.length + ' マス。記事あり ' + filled + ' / 未着手 ' + planned
                + ' / 該当なし ' + na + '。空白は手つかずではなく、判断の結果である。' })
        ]),
        legend,
        U.el('div', { class: 'matrix' },
          U.el('table', null, [
            U.el('thead', null, head),
            U.el('tbody', null, rows)
          ]))
      ])
    };
  }

  return { render: render };
})();
