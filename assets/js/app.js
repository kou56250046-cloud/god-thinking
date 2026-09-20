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

  function start() {
    var root = document.getElementById('view');
    if (!root) return;
    bindSearch();
    Router.start(root);
  }

  return { start: start };
})();

document.addEventListener('DOMContentLoaded', App.start);
