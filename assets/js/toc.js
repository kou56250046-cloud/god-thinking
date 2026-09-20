/* 目次の追従ハイライト。
   見出しは記事本文の HTML に id つきで入っているので、データは持たず DOM から読む。
   mount() は teardown を返す。ルーターが遷移のたびに呼ぶのでリスナーは残らない。 */
window.Toc = (function () {

  /* 記事本文の要素から h2/h3 を拾って目次を組む。 */
  function build(articleEl) {
    var heads = U.qsa('h2[id], h3[id]', articleEl);
    if (!heads.length) return null;

    var items = heads.map(function (h) {
      return U.el('li', null, U.el('a', {
        href: '#',
        class: h.tagName === 'H3' ? 'lv3' : 'lv2',
        'data-toc': h.id,
        text: h.textContent
      }));
    });

    return U.el('nav', { class: 'toc' }, [
      U.el('h4', { text: '目次' }),
      U.el('ol', null, items)
    ]);
  }

  /**
   * 目次を有効にする。
   * ハッシュルーティングと衝突するので、リンクは href を書き換えず
   * scrollIntoView で移動させる（# は URL に1つしか置けない）。
   */
  function mount(root) {
    var links = U.qsa('[data-toc]', root);
    if (!links.length) return function () {};

    var targets = links.map(function (a) {
      return document.getElementById(a.getAttribute('data-toc'));
    }).filter(Boolean);

    function activate(id) {
      links.forEach(function (a) {
        a.classList.toggle('is-active', a.getAttribute('data-toc') === id);
      });
    }

    var offClick = U.delegate(root, '[data-toc]', 'click', function (ev, node) {
      ev.preventDefault();
      var el = document.getElementById(node.getAttribute('data-toc'));
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        activate(node.getAttribute('data-toc'));
      }
    });

    var observer = null;
    if (window.IntersectionObserver && targets.length) {
      observer = new IntersectionObserver(function (entries) {
        var visible = entries.filter(function (e) { return e.isIntersecting; });
        // entries の順序は文書順とは限らない。上にあるものを採る。
        visible.sort(function (a, b) {
          return a.target.getBoundingClientRect().top - b.target.getBoundingClientRect().top;
        });
        if (visible.length) activate(visible[0].target.id);
      }, { rootMargin: '-80px 0px -60% 0px', threshold: 0 });
      targets.forEach(function (t) { observer.observe(t); });
    }

    return function teardown() {
      offClick();
      if (observer) observer.disconnect();
    };
  }

  return { build: build, mount: mount };
})();
