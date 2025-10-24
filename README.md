# ポモドーロタイマー Web アプリ

集中作業と休憩をポモドーロ手法に基づいて管理する軽量な Web アプリケーション。

## プロジェクト構成

- `architecture.md`: 全体アーキテクチャ設計
- `features.md`: 実装機能一覧 (MVP〜Phase3+)
- `plan.md`: 段階的実装計画
- `AGENTS.md`: 開発環境固有の注意事項

## 前提条件

- Python 3.10+ (この環境では `py` コマンドで起動)
- PowerShell (Windows環境)

## セットアップ手順

### 1. リポジトリクローン

```powershell
git clone https://github.com/fujimakis-sss/2025-Github-Copilot-Workshop-Python.git
cd 2025-Github-Copilot-Workshop-Python
```

### 2. ブランチ切り替え (開発用)

```powershell
git checkout feature/pomodoro
```

### 3. 仮想環境作成とActivate

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 4. 依存関係インストール

```powershell
py -m pip install -r requirements.txt
```

### 5. 環境変数設定 (オプション)

`.env.example` をコピーして `.env` を作成し、必要に応じて編集:

```powershell
cp .env.example .env
```

## 起動方法

### 開発サーバー起動

```powershell
py app.py
```

ブラウザで `http://127.0.0.1:5000/` にアクセス。

### API エンドポイント (MVP)

- `GET /api/pomodoro/state` - 現在のセッション状態取得
- `POST /api/pomodoro/start` - フォーカス開始 (JSON: `{"duration_minutes": 25}`)
- `POST /api/pomodoro/break` - 休憩開始 (JSON: `{"duration_minutes": 5}`)
- `POST /api/pomodoro/stop` - セッション中断

## テスト実行

```powershell
py -m pytest -q
```

詳細出力:

```powershell
py -m pytest -v
```

## 開発ガイド

### ブランチ運用

- `main`: 安定版
- `feature/<機能ID>-<slug>`: 機能開発 (例: `feature/MVP-1-start-focus`)

詳細は `plan.md` 参照。

### コード品質

- Lintエラーは随時修正
- PR前にテストパス確認
- 新規機能は必ずテスト追加

### 参考資料

- [アーキテクチャ設計](architecture.md)
- [機能一覧](features.md)
- [実装計画](plan.md)
- [Agent開発者向けメモ](AGENTS.md)

---

ワークショップ元資料: [GitHub Copilot Workshop](https://moulongzhang.github.io/2025-Github-Copilot-Workshop/github-copilot-workshop/#0)
