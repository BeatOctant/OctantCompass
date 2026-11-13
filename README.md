# OctantCompass

> **To use BeatOctant** (install, known issues): [Getting Started](https://github.com/BeatOctant/OctantSpecs/blob/main/GettingStarted_en.md) · [はじめかた（日本語）](https://github.com/BeatOctant/OctantSpecs/blob/main/GettingStarted_ja.md)
>
> BeatOctant is written mostly with AI coding agents (Anthropic's Claude). The maintainer decides what to build and reviews every change. It does not generate maps; it recommends existing maps from BeatSaver. ([作り方（AI の使い方）](https://github.com/BeatOctant/OctantSpecs/blob/main/README.md#作り方ai-の使い方))
>
> OctantCompass is the local recommendation server for the Beat Saber mods OctantPath (Beat Saber on PC) and OctantPath for Quest (OctantPathAndroid, Beat Saber on Meta Quest).
>
> BeatOctant is an unofficial fan project for Beat Saber. It is not affiliated with, endorsed by, or sponsored by Beat Games or Meta. Beat Saber and Meta Quest are trademarks of their respective owners. Beat Games・Meta とは関係のない非公式の MOD・ツールです。
>

Beat Saber の MOD [OctantPath](https://github.com/BeatOctant/OctantPath)（と OctantPath Desktop、Quest 版の OctantPathAndroid）に推薦を返す、ゲームの外で動くローカルの推薦サーバーです。配布 DB を読み、推薦はこの PC の中で計算します。BeatOctant 全体の中での位置は [OctantSpecs の概要](https://github.com/BeatOctant/OctantSpecs#概要)にあります。

## 入れ方

入れ方、DB の取り込み、OctantPath とのペアリング、既知の問題は [はじめかた](https://github.com/BeatOctant/OctantSpecs/blob/main/GettingStarted_ja.md)（[English](https://github.com/BeatOctant/OctantSpecs/blob/main/GettingStarted_en.md)）にあります。

[Releases](https://github.com/BeatOctant/OctantCompass/releases) の単体実行ファイル（Linux・Windows）を使います。Python と OctantVector は入っているので要りません。DB は窓の「詳細設定」の「索引から取り込む」で取ります（既定の索引は [OctantDB](https://github.com/BeatOctant/OctantDB/releases) の最新の Release）。同じ Release の tar を「ファイルから取り込む」で入れることもできます。BeatOctant の部品は、どれも最新の版どうしで使ってください。古い版の組み合わせはサポートしていません。

- Linux: OS の WebKitGTK 4.1 と GTK 3 が要ります（Debian・Ubuntu は `libwebkit2gtk-4.1-0`、Fedora は `webkit2gtk4.1`、Arch は `webkit2gtk-4.1`）。Ubuntu 24.04 で試しました。ほかのディストリビューションは試していません
- Windows: Windows 10 と 11 に入っている WebView2 を使います。「ログイン時に起動する」は、Windows の利用者に試してもらいました（2026-11）。ショートカットは、Windows ではまだ試していません

## 使い方

実行ファイルをダブルクリックするか `octantcompass gui` で、OctantCompass の窓が開きます。動いていなければ起動します。窓を閉じても OctantCompass は動き続け、OctantPath に推薦を返します。止めるのは窓の「停止」です。

- 「状態」のタブ: 状態（ready / loading / degraded と理由）、つないだ OctantPath の一覧と取り消し、ペアリングの合言葉の発行、種類（手札の一覧）、ログ
- 「詳細設定」のタブ: DB の中身、DB の切り替えと取り込み、待ち受けるアドレスやポートなどの設定

OctantPath とのペアリングは、窓に出る合言葉を OctantPath に 1 回入れます。同じ PC でも要ります。既定のポートは 23287 です。

DB は使う間だけ読み込みます（読み込むと 1 GB ほど）。要求が `idle_minutes`（既定 30 分）なければ手放し、次の要求でまた読み込みます。その間は「loading」と出ます。

「ログイン時に起動する」を入れると、Linux ではログインしたときに窓を出さずに起動します。Windows では窓を最小化で開き、タスクバーで動いているのが分かるようにします（窓を閉じても裏で動き続けます）。Linux では systemd のユーザーユニットに書くので、`systemctl --user status octantcompass` で状態を、`systemctl --user stop octantcompass` で止められます。

### コマンド

```sh
octantcompass gui                 # 窓を開く（動いていなければ起動する）
octantcompass serve               # 窓を出さずに前で動く（Ctrl+C で終わる）
octantcompass pair code           # ペアリングの合言葉を出す
octantcompass env list            # ペアリングした環境の一覧
octantcompass env revoke <環境ID>  # 環境を取り消す
octantcompass db import <tar>     # 配布 DB の tar を取り込む
octantcompass db switch <フォルダ>  # 手元の DB のフォルダに切り替える
octantcompass db update [--check] [--index <https の URL>]  # 索引から取り込む
octantcompass shortcut            # アプリ一覧（Windows はスタートメニュー）に窓のショートカットを作る
```

どのコマンドも `--help` で何をするかを出します。`--data-dir <フォルダ>` を付けると、ファイルを全部そのフォルダに置きます。

DB の取り込みと切り替えは、確かめて開けてから使い始めます。失敗したら今の DB を使い続けます。署名がない・合わないなどの警告がある DB も使いますが、警告は窓の結果とコマンドの出力（`signatureWarnings`）に出ます。

### ファイルの置き場所

Linux は次のとおりで、それぞれ `$XDG_CONFIG_HOME`・`$XDG_STATE_HOME`・`$XDG_DATA_HOME`・`$XDG_RUNTIME_DIR` があればその下です。Windows と macOS はユーザーごとのデータフォルダ 1 つです。

| 置き場所 | ファイル | Linux の既定 |
|---|---|---|
| 設定 | `settings.json`、`window.json`（窓の言語・テーマ・位置） | `~/.config/OctantCompass` |
| 状態（消えると困るもの） | `pairing.json`（ペアリングした環境）、`db-selection.json`（使っている DB）、`db-request.json` | `~/.local/state/OctantCompass` |
| データ | `db/`、`dbs/`（取り込んだ DB）、`downloads/`（取り込みの間だけ） | `~/.local/share/OctantCompass` |
| 動いている間だけのもの | `connection.json`、`instance.lock`、`window.lock`、`window-request.json`、`start.log`（窓からの最後の起動の出力） | `$XDG_RUNTIME_DIR/OctantCompass` |

OctantPath から受け取ったプレイの記録はファイルに書かず、動いている間だけメモリに持ちます。起動し直すと OctantPath が送り直します。

## 設定

`settings.json` には変えた値だけを置き、ないものは既定値です。既定値は [`src/octantcompass/defaults.json`](src/octantcompass/defaults.json) にあります。窓で保存すると、その項目だけを書き、既定値と同じなら消します。窓に出ない待ち時間などの内部の値も、`settings.json` に書けば変えられます（窓の「再起動」か次の起動から）。

| 項目 | 中身 |
|---|---|
| `host` | 待ち受けるアドレス。既定は 127.0.0.1（この PC からだけ） |
| `port` | 待ち受けるポート（既定 23287） |
| `idle_minutes` | 要求がなければ DB を手放すまでの分。0 なら手放さない |
| `index_url` | `db update` と画面の更新が読む索引（https の URL）。既定は公式の索引（`https://github.com/BeatOctant/OctantDB/releases/latest/download/index.json`）。null にすると索引を使わない（`db update` には `--index` が要る） |
| `trusted_keys` | OctantVector が同梱する鍵に足して信じる、署名の鍵 |
| `allow_unsigned_db` | 開発用。署名のない DB を取り込むときに警告を出さない。切でも、署名のない DB は警告を出して使う |
| `start_at_login` | ログイン時に起動するか |
| `release_url` | 新しい版の確認に使う、GitHub の最新の Release の API（https の URL）。既定は `https://api.github.com/repos/BeatOctant/OctantCompass/releases/latest`。新しい版があれば、窓の上にその Release のページへのリンクを出し、`serve` はログ（端末で動くときは端末にも）に 1 行出す。窓を開いたときと `serve` の起動のときに 1 回、そのあと開いている・動いている間は 1 日に 1 回見る。取りも入れもしない。null で確かめない |
| `db` | DB のフォルダ。DB を一度も切り替え・取り込みしていないときだけ使う |

`host` を 0.0.0.0 や :: にすると同じネットワークのほかの端末からも届きますが、通信は平文の HTTP なので、合言葉とトークンが暗号化されずに流れます。家など信頼できるネットワークだけで使ってください。Quest は USB（adb reverse）でつなげば 127.0.0.1 のままで使えます。

## 開発

仕様、契約、実装の条件はすべて [OctantSpecs](https://github.com/BeatOctant/OctantSpecs) にあり、入口は [OctantCompass 法](https://github.com/BeatOctant/OctantSpecs/blob/main/octantcompass/law.md)です。

### 開発環境

Python 3.11.4 以上と `uv` がある環境で、次を実行します。依存はこのリポジトリ専用の `.venv/`、取得用キャッシュは `.uv-cache/` に置きます。

```sh
bash scripts/setup-python.sh
.venv/bin/python -m pytest -q
.venv/bin/octantcompass serve --fake-engine   # 人工データで接続を試す
```

窓を開くには `--extra gui`（pywebview）を足します。Linux では gobject-introspection と cairo の開発用ファイル（Debian・Ubuntu は `libgirepository1.0-dev libcairo2-dev pkg-config`）と、WebKitGTK 4.1 とその typelib（`gir1.2-webkit2-4.1`）が要ります。

テストが読む契約の例は `tests/examples/` に写してあります（取得元は各フォルダの `SOURCE`）。`OCTANTSPECS_REF` の版の OctantSpecs は `bash scripts/fetch-octantspecs.sh` で `.octantspecs/` に取れます。

### OctantVector アダプタの結合テスト

`pyproject.toml` の `tool.uv.sources` で固定した OctantVector から推薦側の依存だけを入れ、テスト用の DB で試します。`OCTANTCOMPASS_TEST_DB` がないか OctantVector がなければ、本物との共通テストは飛ばします。

```sh
bash scripts/setup-python.sh --extra octantvector
OCTANTCOMPASS_TEST_DB=/absolute/path/to/test-db .venv/bin/python -m pytest tests/test_octantvector.py -q
```

### 単体実行ファイル

対象の OS の上で作ります。何を入れるかは [`scripts/octantcompass.spec`](scripts/octantcompass.spec) にあります。

```sh
bash scripts/setup-python.sh --extra build --extra gui --extra octantvector
.venv/bin/python scripts/build-standalone.py
OCTANTCOMPASS_TEST_EXECUTABLE=dist/octantcompass .venv/bin/python -m pytest tests/test_standalone.py -q
```

成果物は `dist/octantcompass`（Windows は `dist/octantcompass.exe`）です。同梱したもののライセンスは `build/octantcompass/THIRD-PARTY-NOTICES.txt` に書き出し（[`scripts/third_party_notices.py`](scripts/third_party_notices.py)）、実行ファイルにも入れます。Linux の実行ファイルは WebKitGTK と GTK を同梱せず、OS のものを使います。開発用には `build-standalone.py --without-octantvector` で代役用の実行ファイルを作れます。

### CI

pull request ごとに GitHub Actions（[test.yml](.github/workflows/test.yml)）が Python 3.11 でテストを動かします。文書だけの変更では動きません。

[build.yml](.github/workflows/build.yml) は Linux と Windows で単体実行ファイルを作り、起動を確かめます。動くのは、ビルドにかかわるファイルを変えた pull request、`v*` のタグ、手動の実行です。`v*` のタグでは両方を下書きの GitHub Release に置きます。

## ライセンス

[MIT](LICENSE)。
