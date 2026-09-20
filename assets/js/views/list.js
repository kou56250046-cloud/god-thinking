/* 仮説の一覧と、全文検索の画面。 */
window.Views = window.Views || {};

Views.list = (function () {

  // 絞り込みの状態。画面を離れても残す（戻ってきたとき同じ見え方にするため）。
  var filters = { lens: null, mode: null, terrain: null };

  function matches(h) {
    if (filters.lens && h.lens.indexOf(filters.lens) === -1) return false;
    if (filters.mode && h.mode !== filters.mode) return false;
    if (filters.terrain && h.terrain !== filters.terrain) return false;
    return true;
  }

  function filterRow(label, key, values) {
    var buttons = values.map(function (v) {
      return U.el('button', {
        type: 'button',
        class: 'filter-btn' + (filters[key] === v ? ' is-on' : ''),
        'data-filter': key,
        'data-value': v,
        text: v
      });
    });
    return U.el('div', { class: 'filter-row' }, [
      U.el('span', { class: 'filter-row__label', text: label }),
      buttons
    ]);
  }

  function render() {
    var studio = Store.studio;
    var grid = U.el('div', { class: 'grid' });
    var count = U.el('p', { class: 'page-head__lead' });

    function paint() {
      U.clear(grid);
      var hits = Store.hypotheses.filter(matches);
      count.textContent = Store.hypotheses.length
        ? hits.length + ' 件 / 全 ' + Store.hypotheses.length + ' 件'
        : '';
      if (!Store.hypotheses.length) { grid.appendChild(Partials.noData()); return; }
      if (!hits.length) {
        grid.appendChild(Partials.empty('—', 'この条件に当てはまる仮説はありません。'));
        return;
      }
      hits.forEach(function (h) { grid.appendChild(Partials.card(h)); });
    }

    var filterBox = U.el('div', { class: 'filters' }, [
      filterRow('観点', 'lens', studio.lenses),
      filterRow('モード', 'mode', studio.modes.filter(function (m) { return m !== '経験的主張'; })),
      filterRow('地形', 'terrain', studio.terrains)
    ]);

    paint();

    return {
      title: '仮説',
      node: U.frag([
        U.el('header', { class: 'page-head' }, [
          U.el('p', { class: 'page-head__eyebrow', text: 'Hypotheses' }),
          U.el('h1', { text: '仮説' }),
          count
        ]),
        filterBox,
        grid
      ]),
      mount: function (root) {
        return U.delegate(root, '[data-filter]', 'click', function (ev, node) {
          var key = node.getAttribute('data-filter');
          var value = node.getAttribute('data-value');
          filters[key] = filters[key] === value ? null : value;   // 同じものを押したら解除
          U.qsa('[data-filter="' + key + '"]', root).forEach(function (b) {
            b.classList.toggle('is-on', b.getAttribute('data-value') === filters[key]);
          });
          paint();
        });
      }
    };
  }

  return { render: render };
})();

Views.search = (function () {

  function result(r) {
    return U.el('div', { class: 'result' }, [
      U.el('h3', { class: 'card__title' }, Partials.link(r.article.slug, r.article.title)),
      U.el('div', { class: 'card__foot' }, [
        Partials.modeBadge(r.article.mode),
        Partials.terrainBadge(r.article.terrain)
      ]),
      U.el('p', { class: 'result__snippet' }, Search.renderSnippet(r.snippet))
    ]);
  }

  function render(route) {
    var raw = route.query.get('q') || '';
    var q = raw.trim();          // URL 直打ちの「空白だけ」を空として扱う
    var hits = q ? Search.query(q, 40) : [];
    var body;
    if (!q) {
      body = Partials.empty('⌕', '語を入力してください。');
    } else if (!hits.length) {
      body = Partials.empty('⌕', '「' + q + '」に一致する仮説はありません。');
    } else {
      body = U.frag(hits.map(result));
    }
    return {
      title: q ? q + ' の検索結果' : '検索',
      node: U.frag([
        U.el('header', { class: 'page-head' }, [
          U.el('p', { class: 'page-head__eyebrow', text: 'Search' }),
          U.el('h1', { text: '検索' }),
          q && U.el('p', { class: 'page-head__lead', text: q + ' — ' + hits.length + ' 件' })
        ]),
        body
      ])
    };
  }

  return { render: render };
})();
