# 公開手順（GitHub Pages）

関連: [[operations]] / [[strategy]]。ここから先は**アカウントの作成・push・公開**を含むので、ユーザーの操作か明確な指示が要る。

## 準備済み（2026-11-23）
- 品質チェック（check.py）と自動ビルド・予約公開の Actions（`.github/workflows/pages.yml`）。
- 公開URLは Actions がリポジトリ名から自動で決める（`https://<ユーザー名>.github.io/<リポジトリ名>`）。build.py を直す必要はない。
- 個人情報・秘密情報の混入検査（本名・メール・パス・キー類）：なし。
- git は、このリポジトリだけ匿名の名前 `choiraku-note` で設定済み（push 前なら名前を変えて履歴を直せる）。

## ユーザーが決めること
1. **GitHub アカウント**：新規に匿名アカウントを作る（推奨。ポケットログと結びつかない）か、`pocketlog-note` を使い回すか。
2. リポジトリ名：`choiraku-note`（推奨）。公開リポジトリになる。

## 公開の流れ
1. GitHub でリポジトリ `choiraku-note` を作る（README・.gitignore は足さない）。
2. `git branch -M main`（今のブランチ名 feat/first-article を main に改名）→ `git remote add origin https://github.com/<ユーザー名>/choiraku-note.git` → `git push -u origin main`。
3. リポジトリの Settings → Pages → Source を「GitHub Actions」にする。
4. Actions の `build-and-deploy` が緑になったら、公開URLを開いて表示を確認する。

## 公開後
- お問い合わせ（pages/contact.md）は「準備中」のまま。広告やアフィリエイトを入れる前に、匿名で使えるフォームを用意する。
- Search Console の登録、独自ドメインは [[strategy]] のフェーズ2。
- 60日間リポジトリに動きがないと、定期実行が止められる。
