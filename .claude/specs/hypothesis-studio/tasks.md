# 仮説工房 — タスク

上から順に処理する。1 タスクごとに動作確認してから次へ進む。

**T1〜T5 で「検証が効く空の工房」を先に完成させ、T6 以降で記事を書く。**
順序を逆にすると、検証が無いまま記事を書き、後から全部直すことになる。

---

## T1 プロジェクトの骨組みと設定を作る

- 触るファイル: `.gitignore` / `.claude/CLAUDE.md` / `config/studio.json` / `index.html`
- やること: `static-zero` テンプレから `.claude/CLAUDE.md` を作る。`.gitignore` に `docs/` を書く。
  `config/studio.json` に 論点 8・観点 8・モード 3・地形 4・地雷 7・既出対応づけ 7 を定義する。
  `mines[].source` と `known[].source` の `anchor` は、**実際に原典を開いて確認した文字列**にする。
- **完了条件:**
  - `.gitignore` に `docs/` の行がある
  - `python -c "import json;d=json.load(open('config/studio.json',encoding='utf-8'));print(len(d['topics']),len(d['lenses']),len(d['mines']),len(d['known']))"` が `8 8 7 7` を出す
  - `topics` に `宇宙の自律的発展の機構` が含まれる
  - `lenses` に `複雑系` が含まれる
  - 地雷 7 件と既出 7 件すべてが `source` を持ち、`anchor` が 10〜40 字である

## T2 Markdown 変換器を移植して拡張する

- 触るファイル: `scripts/markdown.py`
- やること: `四柱推命鑑定/scripts/markdown.py` をコピーし、`:::quote n` と `[[slug]]` を足す。
  frontmatter 由来文字列と引用本文の HTML エスケープを入れる。
- **完了条件:**
  - 見出し・表・リスト・強調を含む文字列を渡すと HTML が返る
  - `:::quote 0` が引用として描画され、添字が取り出せる
  - `[[foo]]` が `#/h/foo` へのリンクになる
  - `<script>` を含む文字列を渡すとエスケープされて出力される
  - `strip_tags()` がタグを落とした素文を返す
  - 標準ライブラリ以外を import していない

## T3 検証を実装する

- 触るファイル: `scripts/validate.py`
- やること: design の検査表 **25 項目**を実装する。失敗は**全件集めて**返す。
  照合は空白類を除去した正規化後に行う。
- **完了条件:**
  - 検査 25 項目すべてが実装されている
  - わざと壊した記事を用意し、**8 件の違反が 1 回の実行でまとめて報告される**
    （frontmatter キー欠落 / 節の欠落 / 節が 200 字未満 / 実在しない `anchor` /
    `anchor` が 5 字 / `:::quote` 本文が原典と不一致 / `falsifiers` 空 / `mines` が空配列）
  - `anchor` が見つからない場合、ファイル名と探した文字列が表示される
  - `anchor` が見つかった場合、出現回数が表示される
  - 空白を挟んだ `anchor` でも、正規化により照合が成立する
  - `mode` が `経験的主張` の記事が失敗する
  - `known` に id を挙げて `terrain` が `空白地` の記事が失敗する

## T4 ビルドを実装する

- 触るファイル: `scripts/build.py`
- やること: コーパス読み込み → 検証 → 変換 → 集計 → `data/*.js` 生成。
- **完了条件:**
  - `python scripts/build.py` の 1 コマンドで完走する
  - `pip install` なしで動く（標準ライブラリのみ）
  - 既知のコーパス欠損 4 件が警告として表示され、**ビルドは失敗しない**
  - 検証が失敗したとき、`data/*.js` が更新されない
  - 成功時に「検査した項目と件数」が表示される
  - `data/*.js` の 1 行目に `AUTO-GENERATED` のコメントがある
  - **`data/*.js` に `anchor` の文字列が 1 件も含まれない**（grep で 0 件）
  - **許可リスト外のキーが `data/*.js` に出力されていない**
  - **`docs/` 配下の更新日時がビルド前後で変わらない**

## T5 ビューアの骨格を作る

- 触るファイル: `index.html` / `assets/css/*.css` / `assets/js/{dom,store,router,search,toc}.js` / `assets/js/app.js`
- やること: `toc.js` を流用、`router.js` を DOM ノードを返す形に改修、`dom.js` を
  `createElement` 版で新規に書く。`search.js` のフィールド名を `Store` の公開キーに合わせる。
  requirements の固定文を画面に常時配置する。
- **完了条件:**
  - `index.html` をダブルクリックして開くと画面が出る（ローカルサーバー不要）
  - JavaScript の例外が 0 件
  - 固定文が常時表示されている（文言は requirements と一字一句一致）
  - `#/` `#/h/x` `#/questions` `#/matrix` `#/mines` `#/search` が切り替わる（中身は空でよい）
  - `assets/js/` に `type="module"` と `fetch(` が 0 件
  - **`assets/js/` の `innerHTML` が 0 件**（この時点では `article.js` がまだ無い）
  - `search.js` に `readings` という語が残っていない
  - `data/*.js` が 1 つも無い状態でも例外が出ず、空の状態として表示される

## T6 仮説 1 本目を書いて、工房が回ることを確かめる

- 触るファイル: `hypotheses/computational-irreducibility.md`
- やること: 計算論的既約性の記事を書く。`anchor` と `:::quote` は
  **実際に原典を開いて確認した逐語**を使う。必須 8 節すべてを埋める。
  `mines` に全 7 件を列挙する。
- **完了条件:**
  - ビルドが通る（検査 25 項目すべて）
  - `sources` が 2 件以上、`:::quote` が 1 箇所以上
  - 本文が 3000〜8000 字、各節が 200 字以上
  - `mines` に 7 件すべてが列挙され、`M-06`（マルチバース）が `touches: false` で
    理由が書かれている
  - `falsifiers` が「〜ならば成立しない」形の条件文を含む
  - `questions` が 1 件以上

### ★ T6 の後に一度止まる（承認済みの例外）

1 本目を書き上げたら、**ユーザーに本文を読んでもらってから T7 へ進む。**
文体・深さ・神学的な扱いのズレを、残り 5 本に反映するため。
止まるのはここ一度だけ。

## T7 記事本文の画面を作る

- 触るファイル: `assets/js/views/article.js` / `assets/js/views/partials.js` / `assets/css/prose.css`
- やること: 本文・目次・出典ブロック・被リンクを表示。冒頭に `mode` / `terrain` / `lens`。
- **完了条件:**
  - T6 の記事が読める
  - 冒頭に `mode` と `terrain` と `lens` が表示される
  - `比喩` と `構造的対応` が色で区別できる
  - 引用ブロックの直下に `label` が出典として表示される
  - 見出しから目次が自動生成され、追従する
  - **`assets/js/` の `innerHTML` が 1 件のみ**（`views/article.js` の本文挿入）
  - 記事本文の `max-width` が 40em 以下

## T8 残り 5 本を書く

- 触るファイル: `hypotheses/*.md` 5 本
- やること: `transition-state` / `irreversibility` / `control-autonomy` /
  `symmetry-breaking` / `mutual-information` を書く。`[[slug]]` で相互に参照させる。
- **完了条件:**
  - 6 本すべてがビルドを通る
  - 各記事の `lens` / `topics` / `mode` / `terrain` が design の骨子表と**完全に一致**する
  - `mutual-information` が `known` に `K-01`〜`K-04` を挙げ、`terrain` が `拡張` である
  - `symmetry-breaking` の `terrain` が `留保地` である
  - `control-autonomy` の `topics` に `宇宙の自律的発展の機構` が含まれる
  - 相互参照が最低 4 本張られ、被リンクが逆算されている
  - 6 本すべてで `mines` に 7 件が列挙されている

## T9 一覧と検索の画面を作る

- 触るファイル: `assets/js/views/list.js`
- やること: カード一覧、`lens` / `mode` / `terrain` の絞り込み、全文検索。
- **完了条件:**
  - 6 本がカードで並ぶ
  - `lens` で `計算論` を選ぶと 1 本だけ残る
  - `mode` で `比喩` を選ぶと `irreversibility` と `symmetry-breaking` の 2 本が残る
  - `terrain` で `空白地` を選ぶと 4 本が残る
  - 検索語を入れるとヒット記事とスニペットが出る
  - 検索結果に `docs/` の原典本文が**含まれていない**

## T10 問い一覧・観点マトリクス・地雷一覧を作る

- 触るファイル: `assets/js/views/questions.js` / `matrix.js` / `mines.js`
- やること: 3 画面を作る。マトリクスは空のマスを空として見せる。
- **完了条件:**
  - 問い一覧に全 6 本の `questions` が横断で並び、出典記事へ移動できる
  - マトリクスが **8 論点 × 8 観点 = 64 マス**で表示される
  - **埋まったマスが 10、空白が 54** である
  - 空白のマスが、**背景色と「空」のラベルの両方**で区別される
  - `複雑系` の列が丸ごと空であることが見て分かる
  - 地雷一覧に 7 件が並び、各記事が触れていない旨と理由が表示される

## T11 表示を整える

- 触るファイル: `assets/css/*.css`
- やること: トークン整備、ライト／ダーク両対応、記事の読みやすさ。
- **完了条件:**
  - 幅 360px で横スクロールが発生しない
  - **本文と背景のコントラスト比が、明暗どちらのモードでも 4.5:1 以上**（計算値を示す）
  - 記事本文の `max-width` が 40em 以下

## T12 通しで確認する

- 触るファイル: なし（確認のみ）
- やること: ビルドしてから **claude-in-chrome で `file://` を直接開き**、全機能を通す。
  Playwright は `file://` を開けないので使わない。
- **完了条件:**
  - `python scripts/build.py` → `index.html` をダブルクリック、で全機能が動く
  - DevTools を Offline にしても全機能が動く
  - `index.html` と `assets/` に `fetch(` / `type="module"` / `cdn` / `https://` が 0 件
  - `assets/js/` の `innerHTML` が 1 件のみ
  - `data/*.js` に `anchor` の文字列が 0 件
  - **生成物に原典の本文が引用部分以外まぎれ込んでいない**
    （`data/*.js` を原典の長い一節で grep して 0 件）
  - `docs/` の更新日時が、作業開始時から変わっていない
  - requirements.md の受入条件を上から読み、すべてにチェックが入る
