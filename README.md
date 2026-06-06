# AIマスター

G検定・生成AIパスポートなど、AI関連資格の学習支援サイト（静的HTML）。

本番URL: https://ai-master.jp/

## ローカルで確認する

`fetch()` で問題データを読み込むため、ファイルを直接開く（`file://`）のではなくローカルサーバーを使ってください。

```bash
cd /path/to/ai-master
python3 -m http.server 8080
```

ブラウザで http://localhost:8080/ を開きます。

## GitHub Pages で公開する

1. リポジトリを GitHub に push する
2. **Settings → Pages → Build and deployment** で Source を `Deploy from a branch` に設定
3. Branch を `main`、フォルダを `/ (root)` に設定
4. 数分後、`https://<username>.github.io/<repo>/` で公開される

カスタムドメイン（`ai-master.jp`）を使う場合は、DNS とリポジトリの **Custom domain** 設定を合わせてください。

## 問題データの再生成

Excel を `~/Downloads` に置いたうえで:

```bash
python3 tools/build_g_kentei_questions.py
python3 tools/build_genai_passport_questions.py
```

生成先: `assets/data/g-kentei/`、`assets/data/genai-passport/`

## 問題ページ（SEO）の生成

一問一答・実践演習の各問題を静的 HTML として出力します（模擬試験は対象外）。

```bash
python3 tools/build_question_pages.py
```

生成先:

- `exams/{試験}/{モード}/q/{id-slug}/index.html` — 1問1ページ
- `exams/{試験}/{モード}/domain/{slug}/index.html` — 分野一覧
- `exams/{試験}/{モード}/questions/index.html` — 問題ハブ
- `data/question-index.json` — 全問題のインデックス
- `sitemap.xml` — `question-pages` ブロックを更新

部分ビルド: `python3 tools/build_question_pages.py --exam g-kentei --mode drill`

## 模擬試験の有効化

`assets/js/exam-flags.js` のフラグを変更します。

```javascript
window.AI_MASTER.mockExamsEnabled = true;
```

## ディレクトリ構成

| パス | 内容 |
|------|------|
| `exams/` | 試験対策ページ・プレイヤー |
| `assets/data/` | 問題 JSON |
| `assets/js/` | 共通スクリプト |
| `glossary/` | 用語辞典 |
| `tools/` | AIツール紹介・ビルドスクリプト |
| `legal/` | プライバシーポリシー・利用規約 |

## 免責

当サイトは G検定・生成AIパスポートの公式サイトではありません。試験問題は運営者が自作した学習用コンテンツです。
