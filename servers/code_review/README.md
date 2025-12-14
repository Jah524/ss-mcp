# MCP Code Review Server

OpenAI を使用した Git diff のコードレビューを行う MCP サーバーです。

## セットアップ

まず、このディレクトリに移動します：

```bash
cd servers/code_review
```

### 1. 環境変数の設定

```bash
cp .env.example .env
```

`.env` ファイルを編集して `OPENAI_API_KEY` を設定：

```
OPENAI_API_KEY=sk-your-api-key-here
```

### 2. インストール

```bash
pip install -e .
```

**`-e`（編集可能モード）について：**
- ソースコードへのシンボリックリンクとしてインストール
- `server.py` などの変更が再インストールなしで即座に反映される
- 開発中は `-e` を使用し、本番では `pip install .` を推奨

### 3. Claude Code への登録

```bash
claude mcp add code-review --transport stdio -- mcp-code-review
```

登録確認：

```bash
claude mcp list
```

## アップデート

### ソースコードの更新時

**`-e` モードでインストールした場合：**
- `server.py` の変更は自動的に反映される（再インストール不要）
- `pyproject.toml` の依存関係を変更した場合のみ再インストールが必要：

```bash
pip install -e .
```

**通常モードでインストールした場合：**
- すべての変更に対して再インストールが必要：

```bash
pip install .
```

### Claude Code への再登録

MCP サーバーの登録情報（コマンド名やパス）を変更しない限り、再登録は不要です。
サーバーは起動時に最新のコードを読み込みます。

## 利用可能なツール

### `review_git_diff`

Git diff をレビューし、問題点を指摘します。

**パラメータ：**

| パラメータ | 型 | デフォルト | 説明 |
|-----------|-----|---------|------|
| `repo_root` | string | (必須) | レビュー対象のリポジトリパス |
| `diff_source` | string | `"staged"` | `"staged"`, `"working"`, `"branch"` のいずれか |
| `base_ref` | string | null | branch diff 時のベース参照 |
| `head_ref` | string | null | branch diff 時のヘッド参照 |
| `focus` | string | `"bugs, edge cases, security, performance, readability"` | レビューの観点 |
| `model` | string | `"gpt-4o-2024-08-06"` | 使用する OpenAI モデル |
| `include_context_files` | bool | `true` | 変更ファイルの全文をコンテキストに含める |

### `repo_info`

リポジトリの基本情報を取得します。

**パラメータ：**

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `repo_root` | string | 対象のリポジトリパス |

## 環境変数（オプション）

| 変数名 | デフォルト | 説明 |
|--------|---------|------|
| `OPENAI_API_KEY` | (必須) | OpenAI API キー |
| `OPENAI_REVIEW_MODEL` | `gpt-4o-2024-08-06` | 使用するモデル |
| `REVIEW_ALLOWED_ROOTS` | (なし) | 許可するリポジトリパス（`:`区切り） |
| `REVIEW_MAX_DIFF_CHARS` | `120000` | diff の最大文字数 |
| `REVIEW_MAX_CTX_BYTES` | `160000` | コンテキストファイルの最大バイト数 |
| `REVIEW_MAX_FILES` | `30` | コンテキストに含める最大ファイル数 |

## 開発

```bash
pip install -e ".[dev]"
pytest
```
