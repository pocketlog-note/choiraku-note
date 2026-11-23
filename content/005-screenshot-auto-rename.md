---
title: スクリーンショットのファイル名を日時つきに一括変更。予定表示と元に戻す手順つき
date: 2026-11-25
description: Windowsで撮ったスクリーンショットの名前を「2026-11-20_090530_screenshot.png」の形にまとめて変える、PowerShellの手順です。先に予定を見られ、改名後は記録から元に戻せます。
emoji: 📸
kind: 手順
time: 5分
level: ふつう
env: Windows 11 / PowerShell 5.1
verified: true
verified_note: 自分のPCの一時フォルダに作ったダミーのファイルで、予定表示・改名・スキップ・使用中の失敗・元に戻す操作を確認。実際のスクリーンショットの保存と、PowerShell 7 は未確認。
pr: false
draft: false
---
スクリーンショットを撮り続けていると、フォルダが「Screenshot (12).png」「Screenshot (13).png」で埋まります。あとで「あの画面、いつ撮ったっけ」と探すとき、名前からは何も分かりません。

この記事では、PowerShell で名前を日時つきの形にまとめて変える方法を紹介します。先に予定を見られて、変えたあとも元に戻せます。

## 結論：更新日時を名前に入れれば、並べ替えるだけで撮った順になる

Windows 11 で Windows ロゴキー＋PrtScn を押すと、画面全体の画像がピクチャフォルダの「スクリーンショット」フォルダに保存されると、マイクロソフトのサポートページに書かれています（英語版では Pictures の Screenshots フォルダ）。

名前は「Screenshot (12).png」のように、連番だけです。

そこで、ファイルの更新日時を使って「年-月-日_時分秒_screenshot.png」に変えます。この形なら、名前順に並べるだけで撮った順になります。秒まで入れているのは、同じ分に何枚か撮ったときに名前が重ならないようにするためです。

動き方は次のとおりです。

- 最初は「予定の表示」だけで、ファイルは1つも変わらない
- 対象は「Screenshot (数字).png」と「スクリーンショット (数字).png」だけ。ほかのファイルには触らない
- 変わった分は、改名ログ（rename-log.csv）に残る
- 同じ名前がすでにあるときは、変えずにスキップする

## 手順1：まずテスト用のフォルダを用意する

いきなり本物のスクリーンショットフォルダで試すのは避けましょう。デスクトップなどに「テスト」フォルダを作り、スクリーンショットを3枚ほどコピーして入れてください。

名前が「Screenshot (数字).png」の形でないファイルは、対象になりません。テスト用に別の画像を使うなら、先に名前をその形に変えておきます。

## 手順2：スクリプトを貼り付ける（まずは予定の表示）

PowerShell を開き、次のコードを貼り付けて Enter を押します。1行目の `$src` は、手順1のフォルダの場所に書き換えてください。

```powershell
$src   = "$env:USERPROFILE\Desktop\テスト"   # 対象フォルダ
$apply = $false                                # $false=予定を見るだけ / $true=実際に改名
$log   = Join-Path $src 'rename-log.csv'

$pattern = '^(Screenshot|スクリーンショット) \(\d+\)\.png$'
$files = Get-ChildItem -LiteralPath $src -File | Where-Object { $_.Name -match $pattern }

$result = foreach ($f in $files) {
  $new  = '{0:yyyy-MM-dd_HHmmss}_screenshot.png' -f $f.LastWriteTime
  $dest = Join-Path $src $new
  if (Test-Path -LiteralPath $dest) {
    [pscustomobject]@{ result='skip'; from=$f.Name; to=$new }; continue
  }
  if ($apply) {
    try {
      Rename-Item -LiteralPath $f.FullName -NewName $new -ErrorAction Stop
      [pscustomobject]@{ result='renamed'; from=$f.Name; to=$new }
    } catch {
      [pscustomobject]@{ result='failed'; from=$f.Name; to=$new }
    }
  } else {
    [pscustomobject]@{ result='plan'; from=$f.Name; to=$new }
  }
}

$result | Format-Table -AutoSize
$done = @($result | Where-Object { $_.result -eq 'renamed' })
if ($done.Count -gt 0) {
  $done | Export-Csv -LiteralPath $log -Append -NoTypeInformation -Encoding UTF8
}
```

何をしているかを、順に説明します。

- `$pattern` が、対象にするファイル名の形です。英語表示の「Screenshot」と、日本語表示の「スクリーンショット」の両方を拾います
- `$new` が新しい名前です。更新日時から作ります
- 同じ名前がすでにあれば `skip`、予定だけなら `plan`、実際に変えたら `renamed`、変えられなかったら `failed` と表に出ます
- 変えたものだけが、rename-log.csv に追記されます

## 手順3：表を見る

実行すると、次のような表が出ます。

```text
result from               to
------ ----               --
plan   Screenshot (1).png 2026-11-20_090530_screenshot.png
plan   Screenshot (3).png 2026-11-21_140000_screenshot.png
```

「from」が今の名前、「to」が変わったあとの名前です。この段階ではファイルは変わっていません。意図どおりの名前になっているか、確かめてください。

## 手順4：問題なければ、実際に改名する

予定に問題がなければ、2行目を `$apply = $true` に書き換え、同じコードをもう一度貼り付けます。表の「result」が `renamed` になり、フォルダの中の名前が変わります。

## うまくいかないとき

### 表に何も出ない

対象の名前の形に合うファイルがないのが原因です。フォルダの場所（`$src`）が合っているか、ファイル名が「Screenshot (数字).png」の形かを見てください。「Screenshot 2026-11-20 090530.png」のように、すでに日時が入っている名前は対象外です。

### `failed` が出る

そのファイルを、別のアプリが開いていることがあります。画像ビューアーや編集ソフトを閉じてから、もう一度実行してください。変えられたファイルは対象から外れるので、再実行しても二重に変わることはありません。

### `skip` が出る

同じ更新日時（秒まで同じ）のファイルが、すでにあります。新しい名前が同じになるため、あとから処理した側を変えずに残しています。残ったファイルは、手で名前をつけてください。

### 日本語が文字化けする

コードをファイルに保存して実行すると、文字コードの違いで「スクリーンショット」が読めなくなることがあります。

今回の確認でも、BOM（文字コードの目印）なしの UTF-8 で保存したファイルを PowerShell 5.1 で動かしたところ、日本語の名前に合いませんでした。この記事のように、画面に貼り付けて動かすなら問題ありません。ファイルにして使うなら、BOM つきの UTF-8 で保存してください。

## 間違えたとき：改名ログから元に戻す

rename-log.csv には、変える前の名前（from）と変えたあとの名前（to）が残っています。次のコードで元に戻せます。`$src` は、手順2と同じフォルダにしてください。

```powershell
$src = "$env:USERPROFILE\Desktop\テスト"
Import-Csv (Join-Path $src 'rename-log.csv') | ForEach-Object {
  Rename-Item -LiteralPath (Join-Path $src $_.to) -NewName $_.from
}
```

戻したあとも、rename-log.csv は残ります。もう一度改名するなら、先に消すか名前を変えておくと、記録が混ざりません。

## 向いている人・向いていない人

向いているのは、次のような人です。

- 資料づくりやマニュアルづくりで、スクリーンショットをよく撮る
- あとで「いつ撮ったか」から画像を探したい
- 先に結果を見てから、実行するか決めたい

向いていないのは、次のような人です。

- 撮った直後に、内容に合わせた名前をつけたい人（このスクリプトは中身を読みません）
- 他の人と共有しているフォルダを整理したい人（名前を変えると、相手が貼ったリンクが切れることがあります）
- 画像に写っている個人情報や社外秘が気になる人。名前を変えても、画像の中身は変わりません。人に渡す前には、中身を確認してください

## 動かして確かめたこと

この記事のスクリプトは、Windows 11 の Windows PowerShell 5.1 で動かして確かめました（2026年11月24日）。

使ったのは、自分の実際のスクリーンショットフォルダではなく、一時フォルダに作ったダミーのファイルです。更新日時をわざと変えた「Screenshot (1).png」「スクリーンショット (2).png」「Screenshot (3).png」「memo.png」の4つを置き、次の動きを見ました。

- 予定の表示のあいだは、ファイル名が変わらないこと
- 「Screenshot (数字).png」が、更新日時つきの名前に変わること
- 対象外の「memo.png」には触らないこと
- 同じ更新日時のファイルは、`skip` になって名前が変わらないこと
- 別の処理がファイルを開いているあいだは `failed` になること
- 改名ログのコードで、元の名前に戻せること

確かめていないこともあります。

- Windows ロゴキー＋PrtScn で実際に撮った画像で動かすこと。保存先は、マイクロソフトのサポートページの説明（2026年11月24日確認）をもとにしています
- PowerShell 7 や、Mac・Linux での動作
- 何千枚ものファイルがあるフォルダでの速さ
- OneDrive でピクチャフォルダを同期している場合の動作

最初は少ない枚数で試してください。

## 明日やること

明日は、手順2の予定の表示だけ実行してみてください。

自分のスクリーンショットが、どの日にどれだけ溜まっているかが表で分かります。改名するかどうかは、それを見てから決めれば十分です。

## 出典

- Microsoft サポート「Keyboard shortcut for print screen」https://support.microsoft.com/en-us/windows/experience/keyboard-shortcut-for-print-screen （2026年11月24日確認）
