# ss-mcp

複数のMCPサーバーを1つのGitプロジェクト（モノレポ）で管理するリポジトリです。

## ディレクトリ構成

```
ss-mcp/
├── README.md
├── scripts/
│   └── register_user.sh      # 全サーバーをuser scopeで一括登録
├── configs/
│   └── claude/
│       └── servers.json      # mcpServers定義（テンプレート）
├── shared/
│   └── mcp_shared/           # 共通ユーティリティ
│       ├── __init__.py
│       ├── repo_guard.py     # リポジトリアクセス制御
│       └── limits.py         # リソース制限
└── servers/
    └── _template/            # 新規サーバー作成用テンプレート
        ├── pyproject.toml
        ├── src/_template/
        │   ├── __init__.py
        │   └── server.py
        └── tests/
```

## 使い方

### 新しいMCPサーバーを追加する

1. `servers/_template` をコピーして新しいサーバーディレクトリを作成
2. `pyproject.toml` のパッケージ名・依存関係を編集
3. `src/` 内にサーバー実装を作成
4. `scripts/register_user.sh` に登録コマンドを追加

```bash
# 例: my_server を作成
cp -r servers/_template servers/my_server
# ディレクトリ名とファイル内容を適宜変更
```

### Claude Codeへの登録

#### User Scope（推奨：全プロジェクトで共通利用）

```bash
./scripts/register_user.sh
```

または個別に登録：

```bash
claude mcp add-json my-server \
  --scope user \
  '{"type":"stdio","command":"python","args":["-m","my_server.server"]}'
```

#### Project Scope（チーム共有向け）

プロジェクトルートに `.mcp.json` を作成：

```json
{
  "mcpServers": {
    "my-server": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "my_server.server"]
    }
  }
}
```

## 共通ユーティリティ

`shared/mcp_shared/` には各サーバーで共通利用できるユーティリティが含まれています：

- **RepoGuard**: リポジトリパスのアクセス制御
- **Limits**: ファイルサイズ・数の制限管理

```python
from mcp_shared import RepoGuard, Limits

guard = RepoGuard(allowed_paths=["/path/to/repo"])
limits = Limits(max_file_size=5 * 1024 * 1024)
```

## 開発

```bash
# 依存関係のインストール（各サーバーディレクトリで）
pip install -e ".[dev]"

# リント
ruff check .

# テスト
pytest
```

## ライセンス

MIT
