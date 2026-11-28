---
title: CSVをExcelで開くと文字化け。元を残して一括で直す手順と予定表示つき
date: 2026-11-29
description: 業務システムから出したCSVをExcelで開くと日本語が化ける原因と、元のファイルを残したままExcel用のコピーを一括で作るPowerShellの手順です。先に予定を見られます。
emoji: 🔤
kind: 手順
time: 10分
level: ふつう
env: Windows 11 / PowerShell 5.1 / Excel（Microsoft 365 Apps）
verified: false
verified_note: 一時フォルダのダミーCSVで、文字化けの再現、変換、元ファイルが変わらないこと、Excelで開いた結果を確認。Excelの「データ」タブから取り込む画面操作と、他バージョンのExcelは未確認。
pr: false
draft: false
---
業務システムや会計ソフトから出したCSVをダブルクリックで開くと、「蜩∝錐」のような読めない文字が並ぶ。月に何度か、そんな経験はありませんか。

この記事では化ける理由を短く説明したうえで、元のCSVは残したまま、Excelで開ける形のコピーをまとめて作るPowerShellの手順を紹介します。先に予定を見られるので、いきなりファイルが増えることはありません。

## 結論：UTF-8のCSVに目印（BOM）をつけたコピーを作る

化ける原因の多くは、CSVの文字コードです。Windows の Excel はダブルクリックで開いたCSVを、目印がなければ日本語のWindows標準の文字コード（Shift_JIS系）として読みます。

一方、最近のシステムが出すCSVは、UTF-8という別の文字コードのことが多くあります。読み方が合わないため、字が化けるわけです。

UTF-8のファイルの先頭に「これはUTF-8です」という目印（BOM）をつけると、Excelはその目印を見て正しく読みます。今回の確認でも、目印のないUTF-8のCSVは化け、目印をつけたコピーは日本語どおりに開けました。

動き方は次のとおりです。

- 最初は「予定の表示」だけで、ファイルは1つも増えない
- 元のCSVは書き換えない。「元の名前_excel.csv」というコピーを作る
- すでに目印があるファイルと、UTF-8ではないファイルは、触らずにスキップする
- 同じ名前のコピーがあるときも、上書きせずにスキップする

## 手順1：テスト用のフォルダを用意する

デスクトップなどに「CSVテスト」フォルダを作り、化けるCSVを2〜3個コピーして入れてください。いきなり本物のフォルダで試すのは避けます。

## 手順2：スクリプトを貼り付ける（まずは予定の表示）

PowerShell を開き、次のコードを貼り付けて Enter を押します。1行目の `$src` を、手順1のフォルダの場所に書き換えてください。

```powershell
$src   = "$env:USERPROFILE\Desktop\CSVテスト"   # 対象フォルダ
$apply = $false                                  # $false=予定を見るだけ / $true=実際にコピーを作る
$strict = New-Object Text.UTF8Encoding($false, $true)
$bomEnc = New-Object Text.UTF8Encoding($true)

$result = foreach ($f in Get-ChildItem -LiteralPath $src -Filter *.csv -File | Where-Object { $_.BaseName -notlike '*_excel' }) {
  $bytes = [IO.File]::ReadAllBytes($f.FullName)
  $new   = $f.BaseName + '_excel.csv'
  $dest  = Join-Path $src $new
  if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
    [pscustomobject]@{ result='skip-hasBOM'; file=$f.Name; to='' }; continue
  }
  try { $text = $strict.GetString($bytes) }
  catch { [pscustomobject]@{ result='skip-notUTF8'; file=$f.Name; to='' }; continue }
  if (Test-Path -LiteralPath $dest) {
    [pscustomobject]@{ result='skip-exists'; file=$f.Name; to=$new }; continue
  }
  if ($apply) {
    [IO.File]::WriteAllText($dest, $text, $bomEnc)
    [pscustomobject]@{ result='converted'; file=$f.Name; to=$new }
  } else {
    [pscustomobject]@{ result='plan'; file=$f.Name; to=$new }
  }
}
$result | Format-Table -AutoSize
```

何をしているかを、順に説明します。

- `$strict` は、UTF-8として厳密に読むための設定です。UTF-8として読めないファイルは、エラーになります
- `$bomEnc` は、目印つきのUTF-8で書き出すための設定です
- 「_excel」で終わる名前のファイルは、変換の対象から外します。自分が作ったコピーをまた変換しないためです
- 先頭の3バイトが EF BB BF なら、すでに目印があるので `skip-hasBOM` にします
- UTF-8として読めなければ `skip-notUTF8` にします。Shift_JIS のファイルはここに入ります
- コピー先に同じ名前があれば `skip-exists` にします

## 手順3：表を見る

実行すると、次のような表が出ます。

```text
result       file  to
------       ----  --
plan         a.csv a_excel.csv
skip-hasBOM  b.csv
skip-notUTF8 c.csv
skip-exists  e.csv e_excel.csv
```

`plan` のものだけがコピーを作る予定です。スキップの理由は右の `result` の列で分かります。

## 手順4：問題なければ、実際にコピーを作る

予定に問題がなければ、2行目を `$apply = $true` に書き換え、同じコードをもう一度貼り付けます。`result` が `converted` になり、「元の名前_excel.csv」ができます。Excelで開くのは、このコピーのほうです。

同じコードをもう一度実行しても、コピーは作り直されません。`skip-exists` になるだけです。元のCSVが更新されたときは、古いコピーを消してから実行してください。

## うまくいかないとき

### `skip-notUTF8` になって、コピーが作られない

そのファイルはUTF-8ではありません。Shift_JIS のCSVなら、Excelはそのまま正しく開けるはずです。それでも化けるなら、元のシステムの出力設定を見直すか、次の「別のやり方」を試してください。

### コピーを開いても、まだ化ける

次の2つを見てください。

- 開いているのが、元のファイル（_excel がつかない名前）になっていないか
- 元のファイルがUTF-8ではなく、別の文字コード（UTF-16 など）になっていないか

UTF-16 のCSVはUTF-8として読めずに `skip-notUTF8` になると考えられますが、今回は動かして確かめていません。

### 先頭の0が消える、長い数字が「1.23E+15」になる

これは文字コードとは別の問題です。Excelが列を数字と見なして書き換えています。コピーで直る話ではないので、次の取り込み方で、その列を「文字列」にして読み込んでください。

## 別のやり方：Excelの取り込み機能を使う

Excelには、CSVを取り込むときに文字コードを選べる機能があります。「データ」タブの「テキストまたはCSVから」を使うと、プレビューを見ながら「元のファイル」の欄で文字コードを選べると、Microsoft のサポートページの説明などで案内されています。

この機能なら、元のファイルに手を入れずに済みます。列ごとの形式も選べるので、先頭の0が消える問題にも向いています。ただし、開くたびに数回のクリックが必要です。毎週何十個も開く人は、今回のコピーを作る方法のほうが楽です。

なお、この記事では取り込み機能の画面操作は動かして確かめていません。画面の名前はお使いのExcelのバージョンで違うことがあります。

## 向いている人・向いていない人

向いているのは、次のような人です。

- 同じシステムから、UTF-8のCSVを何度も出して、Excelで開いている
- 元のCSVをそのまま取っておきたい
- 変換の前に、対象を表で見たい

向いていないのは、次のような人です。

- 1個だけ開きたい人（取り込み機能のほうが早いです）
- CSVを、別のシステムに戻して取り込みたい人。目印つきのコピーは、戻す先のシステムによっては、先頭に余計な文字が入ったと見なされることがあります。戻すときは、元のファイルを使ってください
- CSVに個人情報や顧客情報が入っている人。このスクリプトは中身を外に送りませんが、コピーが増えるぶん、置き場所の管理が要ります。不要になったコピーは消してください

## 動かして確かめたこと

この記事のスクリプトは、Windows 11 の Windows PowerShell 5.1 と Excel（Microsoft 365 Apps、バージョン 16.0）で動かして確かめました（2026年11月28日）。

使ったのは、実際の業務ファイルではなく、一時フォルダに作ったダミーのCSVです。次の動きを見ました。

- 目印のないUTF-8のCSVをExcelで開くと、日本語が化けること
- 目印をつけたコピーをExcelで開くと、日本語が正しく表示されること
- 予定の表示のあいだは、ファイルが増えないこと
- 元のCSVの中身は変わらず、コピーの先頭に目印（EF BB BF）がつくこと
- 目印つきのファイル、Shift_JIS のファイル、コピー先と同名のファイルは、スキップされること
- 同じコードをもう一度実行しても、コピーが作り直されないこと

確かめていないこともあります。

- 「データ」タブの「テキストまたはCSVから」の画面操作
- 他のバージョンのExcelや、Mac 版 Excel
- PowerShell 7 での動作
- 何万行もある大きなCSVでの速さ
- UTF-16 など、UTF-8以外のファイルの扱い（Shift_JIS だけスキップを確認しました）

最初は少ない個数で試してください。

## 明日やること

明日は、手順2の予定の表示だけ実行してみてください。

化けているCSVのうち、どれが `plan` になるかが分かります。`skip-notUTF8` が出たら、そのファイルの出力元の設定を確認する、という次の一手も見えてきます。

## 出典

- Microsoft サポート「テキスト (.txt または .csv) ファイルのインポートまたはエクスポート」https://support.microsoft.com/ja-JP/Excel/get-started/import-or-export-text-txt-or-csv-files （2026年11月28日、検索結果の案内を確認。ページ本文の細部は未確認）
