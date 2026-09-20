/* データの受け口。

   data/*.js はビルドの生成物なので、まだ 1 度もビルドしていない状態では存在しない。
   その場合 <script src> は 404 になり window.HYPOTHESES などは undefined のままだが、
   画面は「まだ記事がない」状態として動かなければならない。
   そのため全部 `window.X || 既定値` で受ける。 */
window.Store = (function () {

  var hypotheses = window.HYPOTHESES || [];
  var matrix = window.MATRIX || [];
  var questions = window.QUESTIONS || [];
  var studio = window.STUDIO || {
    topics: [], lenses: [], modes: [], terrains: [], mines: [], known: []
  };

  var bySlug = Object.create(null);
  hypotheses.forEach(function (h) { bySlug[h.slug] = h; });

  var mineById = Object.create(null);
  (studio.mines || []).forEach(function (m) { mineById[m.id] = m; });

  /* ある地雷に触れている記事を集める。地雷一覧が使う。 */
  function articlesTouching(mineId) {
    return hypotheses.filter(function (h) {
      return (h.mines || []).some(function (m) {
        return m.id === mineId && m.touches;
      });
    });
  }

  /* ある地雷について、各記事が書いた判断を並べる。 */
  function judgementsFor(mineId) {
    return hypotheses.map(function (h) {
      var entry = (h.mines || []).filter(function (m) { return m.id === mineId; })[0];
      return entry ? { article: h, touches: !!entry.touches, reason: entry.reason } : null;
    }).filter(Boolean);
  }

  return {
    hypotheses: hypotheses,
    bySlug: bySlug,
    studio: studio,
    matrix: matrix,
    questions: questions,
    mineById: mineById,
    articlesTouching: articlesTouching,
    judgementsFor: judgementsFor,
    isEmpty: function () { return hypotheses.length === 0; }
  };
})();
