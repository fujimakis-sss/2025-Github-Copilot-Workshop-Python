# 開発ガイド (DEV.md)

## ブランチ戦略

### ブランチ命名規約

- `main`: 本番リリース用の安定ブランチ
- `feature/<StoryID>-<slug>`: 機能開発ブランチ
  - 例: `feature/P1-START-focus-api`, `feature/P1-UI-circular-progress`
- `bugfix/<IssueID>-<slug>`: バグ修正ブランチ
- `hotfix/<slug>`: 緊急修正ブランチ

### 作業フロー

1. `main` から最新を取得

   ```powershell
   git checkout main
   git pull origin main
   ```

2. 機能ブランチ作成

   ```powershell
   git checkout -b feature/P1-START-focus-api
   ```

3. 実装 & コミット (小刻みに)

   ```powershell
   git add .
   git commit -m "feat(pomodoro): start_focus API実装"
   ```

4. テスト確認

   ```powershell
   py -m pytest -q
   ```

5. Push & Pull Request作成

   ```powershell
   git push origin feature/P1-START-focus-api
   ```

## Issue運用

### Issueテンプレート構成

各Issueには以下を記載:

- **概要**: 機能/バグの簡潔な説明
- **背景**: なぜ必要か、どのユースケースか
- **受入条件 (AC)**: テスト可能な完了定義
- **実装方針**: 技術的アプローチ
- **テスト項目**: 確認すべきシナリオ
- **参照**: 関連Issue, Story ID (例: P1-START)

### ラベル戦略

- `phase: 0`, `phase: 1`, `phase: 2`, `phase: 3`: フェーズ分類
- `priority: high`, `priority: medium`, `priority: low`: 優先度
- `type: feature`, `type: bug`, `type: refactor`, `type: docs`: 種別
- `status: blocked`: ブロック中
- `needs: review`, `needs: test`: レビュー/テスト待ち

## Pull Request (PR) ガイドライン

### PRサイズ目安

- 変更行数: ~400行以内 (理想は200行前後)
- 1機能1PR (複数機能は分割)
- 大規模機能はサブタスクに分割

### PRチェックリスト

- [ ] テストが追加済み & 全テストパス
- [ ] Lintエラーなし
- [ ] 関連ドキュメント更新 (README, architecture, features, plan)
- [ ] コミットメッセージが規約準拠 (Conventional Commits推奨)
- [ ] 変更内容が受入条件 (AC) を満たす
- [ ] Breaking Changeがあれば明記

### レビュー基準

- **機能性**: ACを満たしているか
- **品質**: テストカバレッジ、エッジケース対応
- **保守性**: 命名、コメント、構造が明確か
- **パフォーマンス**: 既存指標に影響ないか
- **セキュリティ**: 脆弱性混入なし

## コミットメッセージ規約

Conventional Commits形式推奨:

```text
<type>(<scope>): <subject>

<body (optional)>

<footer (optional)>
```

### Type

- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメントのみ変更
- `style`: コード意味に影響しない変更 (空白、フォーマット)
- `refactor`: リファクタリング
- `test`: テスト追加/修正
- `chore`: ビルド、ツール設定など

### 例

```text
feat(pomodoro): フォーカス開始API実装

- POST /api/pomodoro/start エンドポイント追加
- services.start_focus() 実装
- バリデーション (duration 1-240分)
- ユニットテスト追加

Closes #12
```

## 開発環境セットアップ (再掲)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

## テスト実行

```powershell
# 全テスト
py -m pytest

# 詳細出力
py -m pytest -v

# 特定ファイルのみ
py -m pytest tests/test_services.py

# カバレッジ (拡張時)
py -m pytest --cov=pomodoro
```

## コード品質チェック

### Linter (将来導入)

```powershell
py -m flake8 pomodoro tests
py -m black --check pomodoro tests
py -m mypy pomodoro
```

### フォーマット自動修正

```powershell
py -m black pomodoro tests
```

## デバッグ Tips

- Flask Debug モードは `app.py` 内で `debug=True` 設定済み
- ログ出力: `app.logger.info()` 使用
- ブレークポイント: VSCode デバッグ構成追加可能

## トラブルシューティング

### `py` コマンドが認識されない

→ Python 3.10+ が正しくインストールされているか確認。  
→ `python --version` で代替可能な場合もあるが、このプロジェクトでは `py` 推奨。

### モジュールインポートエラー

→ 仮想環境がActivateされているか確認:

```powershell
.\.venv\Scripts\Activate.ps1
```

### テスト失敗

→ 前回のテスト実行でグローバル状態が残っている可能性。  
→ `pomodoro/services.py` のグローバル変数を初期化する fixture 追加検討。

## 参考資料

- [architecture.md](architecture.md): 全体設計
- [features.md](features.md): 機能一覧
- [plan.md](plan.md): 実装計画・タスク分解
- [AGENTS.md](AGENTS.md): 環境固有注意事項

---

質問・提案は Issue または PR コメントで随時歓迎。
