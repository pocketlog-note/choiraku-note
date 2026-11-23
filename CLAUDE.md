# choiraku-note（ちょいラク帳）

## 目的
匿名で運営する試験的な記事サイト。テーマ「パソコンとAIの小さな時短」（2026-11-23 ユーザー了承）。pocket-log（隣のフォルダ）の仕組みを流用した姉妹サイト。方針は [[strategy]]、記事の基準は [[article-guide]]、アイデア出し〜公開の手順は [[operations]]（すべて plan/）。

## ゴール／期限
- 試験運用。期限なし。記事は**中編（本文3,000〜4,500字）**（ユーザー指示 2026-11-23。pocket-log は短すぎたため）。

## 技術スタック
- Python 3.10（標準ライブラリのみ）。`build.py`: `content/*.md` ＋ `pages/*.md` ＋ `style.css` → `docs/`（git管理外）。公開は GitHub Actions → GitHub Pages（設定済み）。
- 公開URL: https://pocketlog-note.github.io/choiraku-note/ 。`SITE_URL` は Actions が自動設定する（build.py の既定値 `example.invalid` はローカル用。直す必要なし）。

## よく使うコマンド
- 新しい記事: `python new_post.py <slug> "<タイトル>" [公開日]`
- 品質チェック: `python check.py`（`-I` は付けない）
- ビルド: `python build.py`（下書き込み: `$env:INCLUDE_DRAFTS=1; python build.py`）

## ルール・注意点
- 記事を書いたら毎回 yomiyasu スキルで推敲 → check.py → build.py。
- 動かしていない手順を「確かめた」と書かない。【体験メモ】は本人が書く。
- 匿名: 本名・個人メールを出さない。git の user はこのリポジトリのローカル設定で`pocketlog-note`（noreply。pocket-log と同じアカウントを使い回す決定）にしてある。
- アカウント作成・ドメイン購入・課金は、ユーザーの指示があるときだけ。push は定期タスク（choiraku-note-daily）が記事公開のために行う。

## 定期運用
- 毎朝8時台に定期タスク `choiraku-note-daily` が動く（Claude アプリが起動中のとき。閉じていれば次回起動時）。手順は plan/operations.md、履歴は plan/log.md。Actions も毎朝6時にビルドする。
- 公開リポジトリの定期実行は、60日間リポジトリに動きがないと GitHub に止められる。

## メモ・決定事項
- 記事の先頭情報（任意・既定あり）: `kind`（手順/AI。一覧の絞り込み）、`time`（所要時間）、`level`、`env`、`verified: true|false`、`verified_note`。見た目は style.css と site.js（JSなしでも読める）。
- 記事にはコードブロック（```）を使える（build.py 対応済み）。手順は必ずテスト用フォルダで動かして確かめてから書く。
- 記事003・004は AI の画面で未確認。確認できたら「動かして確かめたこと」を更新する。
- 2026-11-23 作成。サイト名・キャラ名（ラク田）は仮置き。
