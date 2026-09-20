/* 地雷一覧。原典が明示的に否定している立場と、各仮説がそれをどう扱ったか。

   触れていないことも表示する。書き忘れと「検討して触れないと判断した」を
   区別するのがこの画面の役目である。 */
window.Views = window.Views || {};

Views.mines = (function () {

  function judgement(j) {
    return U.el('li', null, [
      Partials.link(j.article.slug, j.article.title),
      ' — ',
      U.el('span', { text: j.reason })
    ]);
  }

  function mine(m) {
    var judgements = Store.judgementsFor(m.id);
    var touched = judgements.filter(function (j) { return j.touches; });
    var clear = judgements.filter(function (j) { return !j.touches; });

    return U.el('div', { class: 'mine' }, [
      U.el('p', { class: 'mine__id', text: m.id }),
      U.el('h3', { class: 'mine__position', text: m.position }),
      U.el('p', { class: 'mine__note', text: m.note }),
      m.sourceLabel && U.el('p', { class: 'question__from', text: '出典: ' + m.sourceLabel }),
      touched.length
        ? U.el('div', { class: 'mine__touch mine__touch--yes' }, [
            U.el('strong', { text: '触れている仮説 ' + touched.length + ' 件' }),
            U.el('ul', null, touched.map(judgement))
          ])
        : U.el('div', { class: 'mine__touch' }, clear.length
            // 記事が 0 本のとき「0 件すべてが判断している」と書くと、
            // 検討していないことを検討済みとして見せてしまう。この画面の目的の逆。
            ? [U.el('strong', { text: '触れている仮説はない' }),
               U.el('p', { text: clear.length + ' 件の仮説すべてが、触れていないと判断している。' })]
            : [U.el('strong', { text: 'まだ判断した仮説がない' }),
               U.el('p', { text: 'この地雷について検討した仮説は 1 本もない。' })]),
      clear.length ? U.el('details', null, [
        U.el('summary', { text: '各仮説の判断を見る' }),
        U.el('ul', null, clear.map(judgement))
      ]) : null
    ]);
  }

  function render() {
    var list = Store.studio.mines || [];
    return {
      title: '地雷',
      node: U.frag([
        U.el('header', { class: 'page-head' }, [
          U.el('p', { class: 'page-head__eyebrow', text: 'Mines' }),
          U.el('h1', { text: '原典が否定する立場' }),
          U.el('p', { class: 'page-head__lead',
            text: list.length + ' 件。仮説はこれらに触れるなら、触れる理由を書かなければならない。' })
        ]),
        list.length
          ? U.el('div', { class: 'stack' }, list.map(mine))
          : Partials.noData()
      ])
    };
  }

  return { render: render };
})();
