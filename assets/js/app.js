/* 起動。検索欄の受け取りとルーターの開始だけを担う。 */
window.App = (function () {

  function bindSearch() {
    var form = document.getElementById('searchForm');
    var input = document.getElementById('searchInput');
    if (!form || !input) return;

    U.on(form, 'submit', function (ev) {
      ev.preventDefault();
      var q = input.value.trim();
      Router.navigate(q ? '/search?q=' + encodeURIComponent(q) : '/');
    });

    // 検索画面を開き直したとき、入力欄に語を戻す
    U.on(window, 'hashchange', syncSearchInput);
    syncSearchInput();
  }

  function syncSearchInput() {
    var input = document.getElementById('searchInput');
    if (!input) return;
    var route = Router.parse();
    input.value = route.segs[0] === 'search' ? (route.query.get('q') || '') : '';
  }

  /* 明暗切替。初期値は index.html の <head> 内で反映済み。ここではボタンだけを扱う。 */
  var THEME_KEY = 'god-thinking:theme';

  function bindTheme() {
    var btn = document.getElementById('themeToggle');
    if (!btn) return;
    var root = document.documentElement;

    function label() {
      var dark = root.getAttribute('data-theme') !== 'light';
      btn.textContent = dark ? '明' : '暗';
      btn.setAttribute('aria-label', dark ? 'ライトモードにする' : 'ダークモードにする');
      btn.title = btn.getAttribute('aria-label');
    }

    U.on(btn, 'click', function () {
      var next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem(THEME_KEY, next); } catch (e) {}
      label();
    });
    label();
  }

  function start() {
    bindTheme();
    var root = document.getElementById('view');
    if (!root) return;
    bindSearch();
    Router.start(root);
  }

  return { start: start };
})();

document.addEventListener('DOMContentLoaded', App.start);
