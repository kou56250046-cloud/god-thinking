# 創造シミュレータ — タスク

上から順に処理する。1 タスクごとに動作確認してから次へ進む。

---

## T1 プロジェクトの骨組みを作る

- 触るファイル: `index.html` / `assets/css/*.css` / `.gitignore` / `.claude/CLAUDE.md`
- やること: `static-zero` テンプレから `.claude/CLAUDE.md` を作る。`index.html` と空の CSS 4 枚を置く。
  `.gitignore` に `data/sources.local.js` を書く。requirements の「このツールが主張しないこと」の
  固定文を画面に配置する。
- **完了条件:**
  - `index.html` をダブルクリックして開くとタイトルが表示される
  - JavaScript の例外が 0 件
  - 固定文が画面の所定位置に常時表示されている（文言は requirements のものと一字一句一致）
  - `.gitignore` に `data/sources.local.js` の行がある

## T2 パラメータと評価軸を定義する

- 触るファイル: `data/params.js` / `data/axes.js`
- やること: design のとおりに 7 パラメータと 5 評価軸を定義する。既定値は実際の創造に揃える。
- **完了条件:**
  - `window.PARAMS.length === 7` かつ `window.AXES.length === 5`
  - `PARAMS` の各 `values` の総積を算出して画面かコンソールに表示でき、その値が 1152 である
  - 既定値が requirements の表と一致している

## T3 実効値の導出を実装する

- 触るファイル: `assets/js/derive.js`
- やること: `derive(config)` を実装。design の導出表を**上から順に適用**する。
  `nullified` の各項目に `confidence` と `source` を持たせる。
- **完了条件:**
  - `dominion='always'` → `eff.freedomEff === 'none'`、`nullified` に自由意志が入る
  - `commandment='none'` → `eff.responsibilityEff === 'p0'`
  - `growth='none'` → `eff.responsibilityEff === 'p0'`
  - `commandment='none'` かつ `growth='none'` → `nullified` に**理由が 2 件**入る
  - `freedom='none'` かつ `dominion='always'` で `freedomEff` が `none` より下にならない
  - 既定値を渡すと `nullified` が空配列
  - `nullified` の全項目が `confidence` を持つ

## T4 判定ルールを書き、評価エンジンを実装する

- 触るファイル: `data/rules.js` / `assets/js/engine.js`
- やること: design の**ルール骨格表のとおりに 18 本**書く。骨格表に無いルールを勝手に足さない。
  理由文は 150 字程度まで。`evaluate(eff)` を実装する。
- **完了条件:**
  - `RULES.length === 18` で、全 id が骨格表と一致
  - 全ルールが `confidence` と `source` と `principles` を持つ（走査して確認）
  - 既定値で評価すると `impossible` の軸が 0 個、`noFall` が `contingent`
  - `freedom='none'` で `loveObject` が `impossible` になり、`hits` に理由・原理・出典が入る
  - `growth='none'` で `sonship` の `hits` が 2 件以上（R-S01 と R-S02 が同時に立つ）
  - `freedomEff` が `none` より下にならない

## T5 出典と引用の解決を実装する

- 触るファイル: `assets/js/sources.js` / `data/sources.local.example.js`
- やること: `resolve(rule)` が出典位置を必ず返し、`window.SOURCES_LOCAL` があれば本文も返す。
- **完了条件:**
  - `data/sources.local.js` が**存在しない**状態で開いても **JavaScript の例外が 0 件**で、
    出典位置が表示される（`net::ERR_FILE_NOT_FOUND` のネットワークエラー表示は許容する）
  - `sources.local.example.js` を `sources.local.js` にコピーすると本文欄が表示に加わる

## T6 パラメータ設定UIを作る

- 触るファイル: `assets/js/ui-params.js` / `assets/js/app.js` / `assets/css/components.css`
- やること: 7 パラメータを操作できるUI。変更のたびに `derive` → `evaluate` を回す。
- **完了条件:**
  - 値を変えると再読み込みなしに判定表示が更新される
  - 既定値から変更した行に変更マークが付き、「既定値から N 項目を変更中」が表示される
    （3 項目変えて N=3 になることを確認）
  - 神の主管を「常に直接」にすると自由意志の行がグレーになり、理由文が出る
  - その理由文に「明示／推論」の印が付いている
  - `assets/js/` 配下に `innerHTML` が 0 件

## T7 判定結果UIを作る

- 触るファイル: `assets/js/ui-result.js` / `assets/css/components.css`
- やること: 5 軸を `○` / `✕` / `△` のバッジで表示。`✕` と `△` は `hits` の**全件**を表示。
- **完了条件:**
  - 既定値で `noFall` に `△` が出て、理由を開くと原理名と出典位置が見える
  - `growth='none'` で `sonship` の理由が **2 件とも**表示される（1 件に省略されない）
  - `○` の軸に「不成立とする根拠が無い」と表示され、出典欄が無い
  - `R-N01` が発火する設定（`freedom='none'`）では `noFall` が `○` かつ理由と出典が出る
  - `confidence: 'derived'` の根拠が `explicit` と視覚的に区別できる

## T8 全ルール一覧UIを作る

- 触るファイル: `assets/js/ui-rules.js`
- やること: **現在の判定に関わらず全 18 本**を一覧表示。「推論のみ」で絞り込める。
- **完了条件:**
  - 18 本すべてが、どの設定にいても一覧に出る
  - 「推論のみ」で絞ると `derived` のルールだけが残る
  - 絞り込み結果に、現在発火していない `derived` ルールも含まれている
  - 各行に id / 対象軸 / 条件 / 判定 / 原理名 / 出典位置が出る

## T9 総当たりを実装する

- 触るファイル: `assets/js/sweep.js` / `assets/js/ui-sweep.js`
- やること: 1152 通りを全探索し、`impossible` ゼロの設定を**実測で**集約表示する。
- **完了条件:**
  - 探索件数が 1152 と表示され、実行が 1 秒以内に終わる
  - `✕` ゼロの件数、共通する値、影響しなかった項目が**すべて実測で**表示される
  - 抽出された設定群での `noFall` の判定が表示される
  - 期待値（design の予測: 32 件）がコードに書かれていない
  - ルールを 1 本コメントアウトすると結果の数字が変わることを確認する

## T10 創造の実行とアダムの選択画面を作る

- 触るファイル: `assets/js/ui-choice.js` / `data/narratives.js`
- やること: 分岐を実装。`✕` を含む → 導入文 + 軸ごとの機械的な列挙。
  `△` を含む → 選択画面 → `obeyed` / `disobeyed`。`reversible` で堕落後の記述のみ分岐。
- **完了条件:**
  - 既定値で実行すると選択画面に入り、ユーザーが選ぶまで結果が確定しない
  - 選択画面の上部に requirements の固定文が一字一句一致で表示される
  - 結果画面の末尾に requirements の固定文が一字一句一致で表示される
  - `assets/js/` 配下に `Math.random` が 0 件
  - `freedom='none'` で実行すると選択画面に入らず、`✕` の軸が列挙される
  - `reversible` を切り替えると堕落後の記述だけが変わり、判定は変わらない
  - `narratives` の各文が 400 字以内

## T11 試行履歴を実装する

- 触るファイル: `assets/js/store.js` / `assets/js/ui-history.js` / `assets/js/app.js`
- やること: debate-app の `read()/write()` を移植し接頭辞を `god-thinking:` に変える。
  最新 20 件まで保持。一覧・復元・全件削除。
- **完了条件:**
  - 実行後にページを再読み込みすると履歴が残っている
  - 21 件目を実行すると最も古い 1 件が消えて 20 件のまま
  - 各行に「変更件数 / ✕ の軸数 / 選択の結果」が出る
  - 行を選ぶとその設定が画面に読み込まれ、判定が再計算される
  - 全件削除ボタンで履歴が空になる
  - プライベートウィンドウで開いても JavaScript の例外が 0 件で履歴以外が動作する

## T12 表示を整える

- 触るファイル: `assets/css/*.css`
- やること: トークン整備、ライト／ダーク両対応、狭い幅での折り返し。
- **完了条件:**
  - DevTools で幅 360px にして横スクロールが発生しない
  - OS のダークモードを切り替えて、両方で全テキストが判読できる

## T13 通しで確認する

- 触るファイル: なし（確認のみ）
- やること: `file://` で開いて全機能を通す。オフラインでも通す。
- **完了条件:**
  - ローカルサーバーを使わず `index.html` のダブルクリックだけで全機能が動く
  - DevTools を Offline にしても全機能が動く
  - `index.html` と `assets/` に `fetch(` / `type="module"` / `cdn` / `https://` が 0 件
  - requirements.md の受入条件を上から読み、すべてにチェックが入る
