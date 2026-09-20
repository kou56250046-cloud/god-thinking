/* 問い一覧。全記事の questions を横断で並べる。

   この工房は答えより問いを残すための場所なので、
   問いだけを集めた画面を独立して持つ。 */
window.Views = window.Views || {};

Views.questions = (function () {

  function item(q) {
    return U.el('div', { class: 'question' }, [
      U.el('p', { class: 'question__text', text: q.text }),
      U.el('p', { class: 'question__from' }, [
        'から: ', Partials.link(q.slug, q.title)
      ])
    ]);
  }

  function render() {
    var list = Store.questions;
    return {
      title: '問い',
      node: U.frag([
        U.el('header', { class: 'page-head' }, [
          U.el('p', { class: 'page-head__eyebrow', text: 'Questions' }),
          U.el('h1', { text: '開かれた問い' }),
          U.el('p', { class: 'page-head__lead',
            text: list.length
              ? list.length + ' 件。いずれもまだ答えが出ていない。'
              : '' })
        ]),
        list.length
          ? U.el('div', { class: 'stack' }, list.map(item))
          : Partials.noData()
      ])
    };
  }

  return { render: render };
})();
