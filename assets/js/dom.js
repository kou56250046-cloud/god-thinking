/* DOM を組むための最小限のヘルパ。

   流用元（四柱推命鑑定）はテンプレートリテラルと HTML 文字列の代入で描いていたが、
   この工房では HTML 文字列の代入を views/article.js の本文挿入 1 箇所に限る。
   そのため createElement 版として書き直してある。
   文字列を組み立てないので、エスケープ漏れという失敗の形が存在しない。 */
window.U = (function () {

  function append(node, kids) {
    if (kids == null || kids === false) return;
    if (Array.isArray(kids)) {
      kids.forEach(function (k) { append(node, k); });
      return;
    }
    if (kids instanceof Node) { node.appendChild(kids); return; }
    node.appendChild(document.createTextNode(String(kids)));
  }

  /**
   * el('div', {class:'card'}, [ el('h3', {text:'題'}), '素のテキスト' ])
   * text を渡すと textContent になる。HTML 文字列を組み立てる必要がない。
   */
  function el(tag, attrs, kids) {
    var node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        var v = attrs[k];
        if (v == null || v === false) return;
        if (k === 'text') { node.textContent = v; return; }
        if (k === 'class') { node.className = v; return; }
        if (k === 'dataset') {
          Object.keys(v).forEach(function (d) { node.dataset[d] = v[d]; });
          return;
        }
        node.setAttribute(k, v === true ? '' : v);
      });
    }
    append(node, kids);
    return node;
  }

  function frag(kids) {
    var f = document.createDocumentFragment();
    append(f, kids);
    return f;
  }

  function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
    return node;
  }

  /* 検索の照合用。全角・半角と大文字・小文字の揺れを潰す。 */
  function normalize(s) {
    s = String(s == null ? '' : s);
    return (s.normalize ? s.normalize('NFKC') : s).toLowerCase();
  }

  function on(target, type, fn, opts) {
    target.addEventListener(type, fn, opts);
    return function off() { target.removeEventListener(type, fn, opts); };
  }

  /* 委譲。画面ごとに teardown を返して、遷移時にリスナーを残さない。 */
  function delegate(root, selector, type, fn) {
    function handler(ev) {
      var node = ev.target.closest ? ev.target.closest(selector) : null;
      if (node && root.contains(node)) fn(ev, node);
    }
    root.addEventListener(type, handler);
    return function off() { root.removeEventListener(type, handler); };
  }

  function qsa(selector, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(selector));
  }

  return {
    el: el, frag: frag, clear: clear, append: append,
    normalize: normalize, on: on, delegate: delegate, qsa: qsa
  };
})();
