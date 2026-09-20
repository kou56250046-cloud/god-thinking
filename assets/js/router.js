/* ハッシュルーター。

   流用元（四柱推命鑑定）は view.html を HTML 文字列として流し込んでいたが、
   この工房では画面は DOM ノードで受け取り replaceChildren で差し替える。
   HTML 文字列の代入を views/article.js の本文挿入 1 箇所だけにするため。

   URL に # は1つしか置けないので、見出しへのディープリンクは ?h=<id> で表す
   （目次のリンク自体は scrollIntoView で動くのでハッシュを触らない）。 */
window.Views = window.Views || {};

window.Router = (function () {

  var viewRoot = null;
  var teardown = null;

  var ROUTES = [
    { name: 'list',      nav: '#/',          match: function (s) { return s.length === 0; } },
    { name: 'article',   nav: '#/',          match: function (s) { return s[0] === 'h' && s[1]; } },
    { name: 'questions', nav: '#/questions', match: function (s) { return s[0] === 'questions'; } },
    { name: 'matrix',    nav: '#/matrix',    match: function (s) { return s[0] === 'matrix'; } },
    { name: 'mines',     nav: '#/mines',     match: function (s) { return s[0] === 'mines'; } },
    { name: 'search',    nav: null,          match: function (s) { return s[0] === 'search'; } }
  ];

  function parse() {
    var raw = location.hash.slice(1) || '/';
    var qi = raw.indexOf('?');
    var path = qi === -1 ? raw : raw.slice(0, qi);
    var query = new URLSearchParams(qi === -1 ? '' : raw.slice(qi + 1));
    var segs = path.split('/').filter(Boolean).map(function (s) {
      try { return decodeURIComponent(s); } catch (e) { return s; }
    });
    return { path: path, segs: segs, query: query };
  }

  function navigate(to, opts) {
    opts = opts || {};
    var target = '#' + to;
    if (opts.replace) {
      history.replaceState(null, '', target);
      render();
    } else if (location.hash === target) {
      render();
    } else {
      location.hash = target;
    }
  }

  function pageHead(eyebrow, title, lead) {
    return U.el('header', { class: 'page-head' }, [
      eyebrow && U.el('p', { class: 'page-head__eyebrow', text: eyebrow }),
      U.el('h1', { text: title }),
      lead && U.el('p', { class: 'page-head__lead', text: lead })
    ]);
  }

  function empty(mark, message, hint) {
    return U.el('div', { class: 'empty' }, [
      U.el('span', { class: 'empty__mark', text: mark }),
      U.el('p', { text: message }),
      hint && U.el('p', null, hint)
    ]);
  }

  function notFound(what) {
    return {
      title: '見つかりません',
      node: U.frag([
        pageHead(null, '見つかりません', (what || '') + ' は存在しません。'),
        U.el('a', { href: '#/', text: '仮説の一覧へ戻る' })
      ])
    };
  }

  /* 画面がまだ実装されていないときの置き（ビューアの骨格の段階で使う）。 */
  function placeholder(route) {
    return {
      title: route.name,
      node: U.frag([
        pageHead(null, '準備中', 'この画面はまだありません。'),
        empty('—', 'この画面はまだ作られていません。')
      ])
    };
  }

  function resolve(route) {
    var segs = route.segs;
    for (var i = 0; i < ROUTES.length; i++) {
      if (!ROUTES[i].match(segs)) continue;
      var name = ROUTES[i].name;
      var view = Views[name];
      if (!view) return placeholder(ROUTES[i]);
      var result = view.render(route);
      return result || notFound(segs[1] || route.path);
    }
    return notFound(route.path);
  }

  function activeNav(route) {
    for (var i = 0; i < ROUTES.length; i++) {
      if (ROUTES[i].match(route.segs)) return ROUTES[i].nav;
    }
    return null;
  }

  function failed(err) {
    return {
      title: 'エラー',
      node: U.frag([
        pageHead(null, '画面を表示できませんでした', String(err && err.message || err)),
        U.el('a', { href: '#/', text: '仮説の一覧へ戻る' })
      ])
    };
  }

  function render() {
    var route = parse();

    // 画面を組むのは、前のリスナーを外す前。ここで例外が出ると、
    // リスナーだけ外れて前の画面が残り、以後どこも反応しなくなる。
    var view;
    try {
      view = resolve(route);
    } catch (err) {
      view = failed(err);
    }

    // 前の画面のリスナー（IntersectionObserver・委譲）を必ず外す
    if (teardown) { teardown(); teardown = null; }

    U.clear(viewRoot);
    viewRoot.appendChild(view.node);

    document.title = view.title ? view.title + ' | 仮説工房' : '仮説工房';
    syncNav(activeNav(route));

    if (typeof view.mount === 'function') {
      try { teardown = view.mount(viewRoot) || null; }
      catch (err) { teardown = null; }
    }

    var anchor = route.query.get('h');
    if (anchor) {
      var el = document.getElementById(anchor);
      if (el) { el.scrollIntoView({ block: 'start' }); return; }
    }
    window.scrollTo(0, 0);
  }

  function syncNav(href) {
    U.qsa('[data-nav]').forEach(function (a) {
      a.classList.toggle('is-active', a.getAttribute('href') === href);
    });
  }

  function start(root) {
    viewRoot = root;
    U.on(window, 'hashchange', render);
    render();
  }

  return {
    start: start, render: render, navigate: navigate, parse: parse,
    pageHead: pageHead, empty: empty, notFound: notFound
  };
})();
