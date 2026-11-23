# 公開手順（GitHub Pages）

関連: [[operations]] / [[strategy]]。ここから先は**アカウントの作成・push・公開**を含むので、ユーザーの操作か明確な指示が要る。

## 準備済み（2026-11-23）
- 品質チェック（check.py）と自動ビルド・予約公開の Actions（`.github/workflows/pages.yml`）。
- 公開URLは Actions がリポジトリ名から自動で決める（`https://<ユーザー名>.github.io/<リポジトリ名>`）。build.py を直す必要はない。
- 個人情報・秘密情報の混入検査（本名・メール・パス・キー類）：なし。
- git は `pocketlog-note`（noreply）で設定済み。既存のコミットも同じ名前に直した（push 前）。

## ユーザーが決めること
1. **GitHub アカウント**：`pocketlog-note` を使い回すと決定済み（2026-11-23）。ポケットログと同じ運営者だと分かる点は了承済み。
2. リポジトリ名：`choiraku-note`（推奨）。公開リポジトリになる。

## 公開の流れ
1. GitHub でリポジトリ `choiraku-note` を作る（README・.gitignore は足さない）。
2. 改名と remote 設定は済み（ブランチ main、origin は `https://github.com/pocketlog-note/choiraku-note.git`）。あとは `git push -u origin main` だけ。
3. リポジトリの Settings → Pages → Source を「GitHub Actions」にする。
4. Actions の `build-and-deploy` が緑になったら、公開URLを開いて表示を確認する。

## 公開後
- お問い合わせ（pages/contact.md）は「準備中」のまま。広告やアフィリエイトを入れる前に、匿名で使えるフォームを用意する。
- Search Console の登録、独自ドメインは [[strategy]] のフェーズ2。
- 60日間リポジトリに動きがないと、定期実行が止められる。
