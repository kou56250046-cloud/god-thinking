# 創造シミュレータ — 設計

## 全体像

```
[パラメータ設定 config]
        │
        ▼
[derive] 実効値の導出 ─── 無効化された項目と理由を副産物として返す
        │
        ▼
[engine] 軸ごとにルールを評価 ─── ○ / ✕ / △ と理由・原理・出典
        │
        ├──▶ [判定表示]  根拠と出典を添えて5軸を表示
        ├──▶ [ルール一覧] 全ルールを一覧。推論だけに絞り込める
        ├──▶ [総当たり]  1152通りを全探索し ✕ ゼロの設定を抽出
        └──▶ [創造実行]  ✕ を含む → 失われたものの列挙
                         △ を含む → アダムの選択画面
```

依存ゼロ・`file://` 動作のため、ビルド工程を持たない。
データは手書きの `.js` ファイルで `window.X = ...` の形でグローバルに生やす。

組合せ総数 = `3 × 2 × 4 × 3 × 4 × 2 × 2` = **1152 通り**。

---

## データ構造

### `data/params.js` — 創造の設計変数

```js
/* 創造の設計変数。id は rules.js の when から参照される */
window.PARAMS = [
  {
    id: 'freedom',
    label: '自由意志',
    help: '人間が神の意に反する選択を取りうる余地',
    values: [
      { id: 'none',    label: 'なし'     },
      { id: 'limited', label: '制限付き' },
      { id: 'full',    label: '完全'     }
    ],
    default: 'full'
  },
  { id: 'growth',         label: '成長期間',     values: ['yes','none'],                      default: 'yes' },
  { id: 'responsibility', label: '人間の責任分担', values: ['p0','p5','p50','p100'],           default: 'p5' },
  { id: 'dominion',       label: '神の主管',     values: ['always','afterOnly','never'],       default: 'afterOnly' },
  { id: 'archangel',      label: '天使長の位置', values: ['beforeContact','beforeNoContact','after','none'], default: 'beforeContact' },
  { id: 'commandment',    label: '戒め',         values: ['given','none'],                     default: 'given' },
  { id: 'reversible',     label: '堕落の可逆性', values: ['yes','no'],                          default: 'yes' }
];
```

既定値は**実際の創造（原理講論が述べる構成）**に一致させる。
ユーザーはそこから動かして何が壊れるかを見る。

### `data/axes.js` — 神が望んだもの

| id | ラベル |
|---|---|
| `loveObject` | 愛の対象の成立 |
| `sonship` | 神の子としての地位 |
| `blessings` | 三大祝福の成就 |
| `noFall` | 堕落の回避 |
| `joy` | 神の喜び |

### `data/rules.js` — 判定ルール

```js
window.RULES = [
  {
    id: 'R-L01',
    axis: 'loveObject',
    when: { freedomEff: 'none' },
    verdict: 'impossible',              // impossible | contingent | ok
    reason: '自由意志を持たない対象は、神の愛の呼びかけに応じることを自ら選べない。' +
            '授受作用は一方向にとどまり、授け受ける関係が閉じない。' +
            '神が受け取るのは応答ではなく反射である。',
    principles: ['授受作用', '四位基台'],
    confidence: 'explicit',             // explicit | derived
    source: { work: '原理講論', section: '創造原理 第一節' },
    quoteKey: 'DP-C1-S1-a'
  },
  ...
];
```

**`when` の評価規則**（単純に保つ）

| 書き方 | 意味 |
|---|---|
| `{ freedomEff: 'none' }` | 実効値が `none` と等しい |
| `{ responsibility: ['p50','p100'] }` | 配列のいずれかに一致 |
| 複数キー | **すべて**満たしたときに発火（AND） |
| `{ freedomEff: { not: 'none' } }` | 否定 |

OR が要る場合はルールを 2 本に分ける。条件式に表現力を持たせない。
ルールの意味が式に埋もれると、原典と突き合わせられなくなるため。

---

## ルールの骨格（★ ここが承認の本体）

初版のルール一覧。**理由文の本文は実装時に書くが、判定の骨格はここで確定する。**
上限 24 本に対し 18 本。

`conf` 列は `E` = 原典に明示、`D` = 推論で補った。

### 愛の対象の成立 `loveObject`

| id | 条件 | 判定 | 骨子 | 原理 | conf |
|---|---|---|---|---|---|
| R-L01 | `freedomEff = none` | ✕ | 応答を選べない対象とは授受作用が一方向にとどまる。神が得るのは反射であって応答ではない | 授受作用 / 四位基台 | E |
| R-L02 | `freedomEff = limited` | △ | 応答の幅が制限された相対者は、愛の対象として部分的にしか成立しない | 授受作用 | D |
| R-L03 | `dominion = never` | ✕ | 神が主管に関与しない世界では、神と人間の間に授受の関係が結ばれない | 授受作用 | D |

### 神の子としての地位 `sonship`

| id | 条件 | 判定 | 骨子 | 原理 | conf |
|---|---|---|---|---|---|
| R-S01 | `growth = none` | ✕ | 完成体として創造された人間は、自らの功として完成を持てない。被造物ではあるが子ではない | 成長期間 / 三大祝福 | E |
| R-S02 | `responsibilityEff = p0` | ✕ | 責任分担がゼロなら完成は全面的に神の業であり、人間は創造物にとどまる | 人間の責任分担 | E |
| R-S03 | `responsibility = p100` | ✕ | 神の創造の分担がゼロなら、人間は神の子ではなく神から独立した他者になる | 人間の責任分担 | D |
| R-S04 | `responsibility = p50` | △ | 原理が示す比率（神の創造95%／人間の責任5%）から外れた世界であり、子としての地位の成立が保証されない | 人間の責任分担 | D |

### 三大祝福の成就 `blessings`

| id | 条件 | 判定 | 骨子 | 原理 | conf |
|---|---|---|---|---|---|
| R-B01 | `growth = none` | ✕ | 個性完成は成長期間を経て達成されるものであり、完成体での創造とは両立しない | 三大祝福（第一祝福） | E |
| R-B02 | `freedomEff = none` | ✕ | 万物の主管は自らの判断で治めることであり、自由意志なしには成立しない | 三大祝福（第三祝福） | D |
| R-B03 | `dominion = always` | ✕ | 神が常に直接主管する世界には、人間が被造世界の主管主体となる余地が残らない | 間接主管圏 / 第三祝福 | D |
| R-B04 | `archangel = none` | △ | 主管すべき被造世界の一部が存在しない世界であり、第三祝福の範囲が欠ける | 三大祝福（第三祝福） | D |

### 堕落の回避 `noFall`

| id | 条件 | 判定 | 骨子 | 原理 | conf |
|---|---|---|---|---|---|
| R-N01 | `freedomEff = none` | ○ | 意に反する選択を取りえない以上、堕落は起こりえない | 自由意志 | E |
| R-N02 | `commandment = none` | ○ | 守るべき戒めが与えられなければ、それを破ることもない | 戒め / 人間の責任分担 | D |
| R-N03 | `freedomEff ≠ none` かつ `commandment = given` かつ `responsibilityEff ≠ p0` | △ | 堕落するか否かは人間の選択によってのみ決まる。神の側に結果を決める手段はない | 間接主管圏 / 人間の責任分担 | E |
| R-N04 | `archangel = beforeContact` | △ | 人間より先に創造され接触を持つ天使長の存在が、堕落の誘因として働きうる | 堕落論 | E |

### 神の喜び `joy`

| id | 条件 | 判定 | 骨子 | 原理 | conf |
|---|---|---|---|---|---|
| R-J01 | `freedomEff = none` | ✕ | 喜びは対象からの刺激として受け取るもの。自ら応答しない対象からは得られない | 創造目的 / 授受作用 | E |
| R-J02 | `dominion = never` | ✕ | 授受の関係が結ばれない以上、対象からの刺激も生じない | 授受作用 | D |
| R-J03 | `freedomEff = limited` | △ | 応答が部分的である以上、神が受け取る喜びも部分的なものにとどまる | 創造目的 | D |

### `reversible`（堕落の可逆性）の扱い

**このパラメータは 5 軸の判定に一切効かせない。**

可逆性は創造時点の設計判断ではなく、堕落が起きた後の摂理に属するため。
効かせるのは `narratives` の分岐だけで、「堕ちた後どうなるか」の記述を変える。
判定に効かないことを画面上でも明示する。

→ ゲートで「それでもパラメータとして残すか」を確認する（SPEC-105）。

### この骨格から予測される総当たりの結果

`✕` を一つも生まない条件は次のとおり。

```
growth         = yes          （R-S01 / R-B01 を避ける）
responsibility = p5 または p50（R-S02 / R-S03 を避ける）
dominion       = afterOnly    （R-L03 / R-B03 / R-J02 を避ける）
commandment    = given        （戒めなし → responsibilityEff = p0 → R-S02）
freedom        = limited または full（R-L01 / R-B02 / R-J01 を避ける）
archangel      = 4値すべて可  （R-B04 は △ であって ✕ ではない）
reversible     = 2値とも可    （判定に効かない）
```

→ `2 × 2 × 4 × 2` = **32 件 / 1152 件**。
そのすべてで `noFall` が `△`（R-N03 が必ず発火する）。

**これは予測であって、受入条件ではない。** 実測が食い違ったら、
直すのは実測ではなくルールかこの予測である。結論に合わせてルールを逆算しない。

---

## 処理の流れ

### 1. `derive(config)` — 実効値の導出

```js
/* @returns {{ eff: Object, nullified: Array<{param, reason, principles, confidence, source}> }} */
```

**適用順序を固定する。上から順に適用し、後の規則は前の結果に対して働く。**

| # | 条件 | 実効値 | `nullified` に入れるか | conf |
|---|---|---|---|---|
| 1 | `dominion = always` | `freedomEff = none` | 入れる（自由意志の行をグレーに） | D |
| 2 | `commandment = none` | `responsibilityEff = p0` | 入れる（責任分担の行をグレーに） | D |
| 3 | `growth = none` | `responsibilityEff = p0` | 入れる（責任分担の行をグレーに） | E |
| 上記以外 | — | 生の値をそのまま使う | — | — |

- 規則 2 と 3 は同じ結果を書き込む。両方当たった場合、`nullified` には**両方の理由**を入れる
- 段階の下限は `none` / `p0`。それより下は無い
- 実効値が生の値と同じになる場合は `nullified` に入れない
- **`nullified` の各項目も `confidence` と `source` を持ち、ルールと同じ表示規約に乗せる**

**規則 2 の設計判断:** 戒めを与えない世界では、守るべき対象が無いため責任分担が
果たされる場がない。よって `freedomEff` を下げるのではなく `responsibilityEff` を 0 にする。
結果として「戒めを与えなければ堕ちないが、神の子は得られない」という構造になる。
これは `derived` として扱う。

### 2. `evaluate(eff)` — 軸ごとの判定

```js
/* @returns {Object<axisId, { verdict, hits: Rule[] }>} */
```

1. 全ルールを走査し、`when` が一致するものを軸ごとに集める
2. 集まった `verdict` の**最も強いもの**を軸の判定とする（`impossible > contingent > ok`）
3. 発火したルールが 1 本も無い軸は `ok`、`hits` は空配列
4. 発火したルール**全部**を `hits` に保持し、理由・原理・出典をすべて表示する

**一つの軸に複数の理由が立つことを潰さない。** 最初に当たったものだけ見せると、
その条件を外せば解決すると誤解させる。実際には複数の理由で同時に壊れている。

**`○` の表示:** `hits` が空、または `ok` のルールしか無い軸は
「不成立とする根拠が無い」と表示する。**`○` は出典を持たない。**
ただし `R-N01` / `R-N02` のように `ok` を明示するルールが発火した場合は、
その理由と出典を表示する。

### 3. `sweep()` — 総当たり

1152 通りを全探索し、`impossible` を含まない設定を集める。

表示は羅列ではなく集約する。**すべて実測で出す。**

```
✕ がゼロになる設定: N 件 / 1152 件

すべてに共通している値
  （実測で算出して表示）

✕ の有無に影響しなかった項目
  （実測で算出して表示）

抽出された設定群での「堕落の回避」の判定
  （実測で算出して表示）
```

### 4. 創造の実行

```
✕ を含む  → 選択画面に入らない
             汎用の導入文 1 本 + ✕ が立った軸ごとの機械的な列挙
             （AXES のラベル + 発火ルールの理由文）
△ を含む  → 選択画面へ
すべて ○  → 現在のルールでは発生しない見込みだが、経路は用意する
```

**`NARRATIVES.void` は単一の固定文ではなく、導入文 + 生成された列挙。**
軸の組合せごとに文言を用意しない（非目標の分量上限）。

**アダムの選択画面**

- 上部に固定文を表示（requirements に文言を確定済み）
- 戒めの提示と選択肢の提示。選ぶのはユーザー。乱数を使わない
- 選択後、`NARRATIVES.obeyed` / `disobeyed` を表示
- `reversible` の値によって、堕ちた後の記述だけが分岐する
- 結果画面の末尾に固定文を表示（requirements に文言を確定済み）

### 5. 試行履歴

`localStorage` に保存。debate-app の `assets/store.js:14-30` を移植し、
接頭辞を `god-thinking:` に変える。

```js
{ config, verdictSummary, changedCount, choice, at }   // 1試行
```

- **最新 20 件まで。** 超えたら古いものから捨てる
- 一覧の各行に「変更件数 / ✕ の軸数 / 選択の結果」を表示
- 行を選ぶと、その `config` を画面に読み込む
- 全件削除ボタンのみ（個別削除は非目標）
- 全読み書きを try/catch で包み、失敗時は履歴機能だけを黙って無効化する

---

## 触るファイル

すべて新規作成。

| ファイル | 内容 |
|---|---|
| `index.html` | 唯一のページ。`<script src>` を依存順に並べる |
| `assets/css/tokens.css` | 色・間隔・書体の変数。ライト／ダーク両対応 |
| `assets/css/base.css` | 要素の既定スタイル |
| `assets/css/layout.css` | 画面構成 |
| `assets/css/components.css` | 判定バッジ・パラメータ行・出典ブロック |
| `assets/js/store.js` | `localStorage` ラッパー（debate-app から移植） |
| `assets/js/derive.js` | 実効値の導出と無効化の検出 |
| `assets/js/engine.js` | ルール評価。三値判定 |
| `assets/js/sources.js` | 出典と引用本文の解決。未配置時のフォールバック |
| `assets/js/sweep.js` | 総当たりと集約 |
| `assets/js/ui-params.js` | パラメータ設定UI |
| `assets/js/ui-result.js` | 判定結果UI |
| `assets/js/ui-rules.js` | **全ルール一覧UI。推論だけに絞り込める** |
| `assets/js/ui-sweep.js` | 総当たり一覧UI |
| `assets/js/ui-choice.js` | アダムの選択画面 |
| `assets/js/ui-history.js` | **試行履歴UI** |
| `assets/js/app.js` | 起動・状態保持・画面遷移 |
| `data/params.js` | 創造の設計変数 |
| `data/axes.js` | 評価軸 |
| `data/rules.js` | 判定ルール（骨格表のとおり 18 本） |
| `data/narratives.js` | 実行後の記述 |
| `data/sources.local.example.js` | 引用本文の形式見本（本文なし・コミットする） |
| `.gitignore` | `data/sources.local.js` を除外 |
| `.claude/CLAUDE.md` | `static-zero` テンプレから作成 |

**JS の書き方**（四柱推命鑑定の流儀に倣う）

- `<script type="module">` を使わない。`window.Xxx = (function(){ ... })()` の IIFE
- `fetch()` を使わない
- DOM は `document.createElement`。`innerHTML` に外部由来文字列を渡さない
- データの受け取りは必ず `window.X || 既定値`

---

## 検討した代替案

| 案 | 採らなかった理由 |
|---|---|
| 堕落を乱数で判定する | 「神には結果が分からなかった」という構造が壊れる。確率で回すと神が期待値を計算できたことになり、問いの核心がすり替わる |
| 判定を二値にする | `△` が表現できない。実際の創造の設定を他と区別できず、到達点が消える |
| LLM を呼んで判定させる | オフライン制約に反する。再現性が無い。根拠がルールとして書かれず、原典と突き合わせて検証できない |
| ルールを JS のコードに直書きする | どこが原典由来でどこが推論かを区別できない。`data/rules.js` にデータとして出し `confidence` を持たせる |
| ルールの骨格を仕様に載せず実装に委ねる | このフローは仕様ゲートの後に人間が入らない。原理の解釈という本件の核心が一度も承認を通らずに完成してしまう |
| 「戒めなし」で `freedomEff` を下げる | 自由意志そのものは残るはずで、失われるのは責任分担を果たす場である。`responsibilityEff` を 0 にする方が筋が通る |
| `reversible` を 5 軸の判定に効かせる | 創造時点の設計判断ではなく堕落後の摂理に属する。`narratives` の分岐にのみ効かせる |
| 引用本文をリポジトリに含める | 著作権。`.gitignore` でローカル限定にする |
| 除外リスト方式で公開対象を決める | 原典由来のファイルが取りこぼしで公開されうる。許可リスト方式にする |
| `build.mjs` でデータを生成する | データは手書きで生成元が無い。ビルド工程を持つ理由が無い |
| 総当たりの結論をコードに書く | ルールを変えれば結論も変わる。結論は実測で出す |
