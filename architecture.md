# ポモドーロタイマー Web アプリ アーキテクチャ案

## 目的

集中作業と休憩をポモドーロ手法 (25分作業 + 5分休憩 など) に基づいて管理し、1日の達成状況 (完了サイクル数・集中時間合計) を視覚化する軽量な Web アプリを提供する。

## スコープ (MVP)

- 作業(フォーカス)タイマー開始 / 休憩タイマー開始 / 中断 / リセット
- 残り時間の円形プログレス表示 (添付モック参照)
- 当日統計: 完了フォーカス数 / 集中合計時間
- ブラウザリロード後も現在のセッション状態を復元
- 単一ユーザー前提 (後で認証導入可能)

## 技術スタック

| レイヤ | 技術 | 備考 |
| ------ | ---- | ---- |
| Webフレームワーク | Flask | Blueprintでモジュール分離 |
| テンプレート | Jinja2 | 初期 HTML を SSR |
| フロント | HTML/CSS/Vanilla JS | UI操作はシンプルに開始/停止/表示更新 |
| リアルタイム | (MVP: なし) / 拡張: Flask-SocketIO or SSE | 状態同期/通知用途 |
| DB | SQLite (開発) / PostgreSQL (本番) | SQLAlchemy ORM採用 |
| マイグレーション | Alembic (拡張) | 初期は不要でも可 |
| 認証 | Flask-Login (拡張) | MVPでは省略 |

## 全体構成図 (論理)

```text
[Browser]
  ├── index.html + timer.js
  ├── API fetch -> /api/pomodoro/*
  └── (拡張) WebSocket/SSE 受信

[Flask App]
  ├── Routes (pomodoro.routes)
  ├── Services (pomodoro.services)
  ├── Repository/Models (SQLAlchemy)
  └── (拡張) Sockets (pomodoro.sockets)

[DB]
  ├── users
  ├── pomodoro_sessions
  ├── daily_stats
  └── (拡張) cycles
```

## ディレクトリ構成案

```text
project_root/
  app.py                # Flaskアプリ初期化
  config.py             # 設定クラス/環境変数読込
  requirements.txt
  architecture.md       # この文書
  /pomodoro/
    __init__.py
    routes.py           # /api/pomodoro/* エンドポイント
    services.py         # ビジネスロジック (開始/終了/集計)
    models.py           # SQLAlchemyモデル定義
    repository.py       # DB操作ラッパ (抽象化)
    sockets.py          # WebSocketイベント (後で追加)
  /templates/
    base.html
    pomodoro/
      index.html
  /static/
    css/style.css
    js/timer.js         # 残り時間描画・開始/停止操作
    js/api.js           # fetchラッパ
    js/socket.js        # リアルタイム同期 (後で)
  /tests/
    test_services.py
    test_routes.py
  /migrations/          # Alembic (後で)
```

## データモデル

### PomodoroSession

| カラム | 型 | 説明 |
| ------ | -- | ---- |
| id | PK | 一意ID |
| user_id | FK(User.id) nullable(MVPはnull) | 所有ユーザー |
| type | enum('focus','break') | セッション種別 |
| planned_duration_sec | int | 予定秒数 (例 1500) |
| start_at | datetime(UTC) | 開始時刻 |
| planned_end_at | datetime(UTC) | 開始 + 予定秒数 |
| end_at | datetime(UTC, nullable) | 実終了 |
| status | enum('active','completed','aborted') | 状態 |

### DailyStat (キャッシュ)

| カラム | 型 | 説明 |
| ------ | -- | ---- |
| id | PK | 一意ID |
| user_id | FK | ユーザー |
| date | date | ローカル日付 |
| total_focus_seconds | int | 集中合計秒 |
| completed_focus_count | int | 完了フォーカス数 |
| updated_at | datetime | 更新タイムスタンプ |

### Cycle (拡張)

| カラム | 型 | 説明 |
| ------ | -- | ---- |
| id | PK | 一意ID |
| user_id | FK | ユーザー |
| focus_session_id | FK | 対応フォーカス |
| break_session_id | FK nullable | 対応休憩 |
| completed | bool | ブレークまで終了したか |

## サービスインターフェイス (services.py)

```python
start_focus(duration_minutes: int = 25) -> PomodoroSession
start_break(duration_minutes: int = 5) -> PomodoroSession
stop_active_session() -> None
get_state() -> dict  # {mode, remaining_seconds, planned_end_at, completed_focus_count, total_focus_seconds}
complete_session(session_id: int) -> None  # status更新 + 日次集計反映
```

残り時間計算: クライアントは `planned_end_at - now` を1秒毎に再計算。ズレ許容しつつ、定期的に `GET /api/pomodoro/state` で再同期。

## API設計 (MVP)

| メソッド | パス | 説明 | 入力 | 出力 |
| -------- | ---- | ---- | ---- | ---- |
| GET | /api/pomodoro/state | 現在セッション状態 | - | state JSON |
| POST | /api/pomodoro/start | フォーカス開始 | {duration_minutes?} | 新規セッション情報 |
| POST | /api/pomodoro/break | 休憩開始 | {duration_minutes?} | 新規休憩セッション |
| POST | /api/pomodoro/stop | 現在セッション中断 | - | 成功/失敗 |
| GET | /api/pomodoro/stats/daily | 今日統計 | ?date=YYYY-MM-DD | 統計JSON |

拡張API:

- POST /api/pomodoro/reset (強制初期化)
- GET /api/pomodoro/stats/summary (週/月統計)

## リアルタイム同期 (段階的導入)

1. MVP: ポーリング (60秒毎 + 初期ロード時)
2. 拡張: WebSocketで `state_update` / `stats_update` イベント push
3. さらに: 長期サイクル完了時通知 / デスクトップ通知

## タイマー実装戦略比較

| 方式 | 利点 | 欠点 | 採用 |
| ---- | ---- | ---- | ---- |
| クライアントカウントダウン | 軽量・実装容易 | 複数タブズレ | MVP採用 |
| サーバカウントダウン配信 | 正確同期 | サーバ負荷増 | 拡張オプション |

## エッジケース & バリデーション

- 既存activeセッション中に再度開始 → 409エラー
- durationが極端 (<1分, >4時間) → 400バリデーション
- 時刻変更/PCスリープ → 再同期APIで残り補正
- セッション終了の遅延検知 (JS停止) → サーバ側で `planned_end_at < now` のactiveを定期的に掃除

## 非機能要件

| 項目 | 内容 |
| ---- | ---- |
| セキュリティ | CSRF (拡張時), 入力バリデーション, XSS対策 (自動エスケープ) |
| パフォーマンス | 状態計算は軽量、DB更新は開始/終了時のみ |
| スケール | SocketIO導入時は Redis message broker で水平スケール |
| ログ | 開始/終了/エラーを構造化ログ出力 (JSON) |
| テスト | servicesユニット + routes統合テスト + タイマーUI軽量E2E |
| メトリクス | (拡張) Prometheusエンドポイント |

## 段階的ロードマップ

1. Scaffold & 基本モデル/サービス/ルート作成
2. フロントUI + 円形プログレス (CSS + JS) 実装
3. 日次統計表示 & 集計更新
4. WebSocket導入 (状態/統計 push)
5. 認証 + 複数ユーザー + Cycle/長休憩ロジック
6. CI/CD・Alembic・追加テスト
7. 拡張機能 (タグ、バッジ、通知)

## 今後の初期実装ステップ (具体)

- requirements.txt へ Flask, SQLAlchemy, python-dotenv 追加
- `app.py` に create_app パターン & DB初期化
- `pomodoro/models.py` 定義 & SQLite生成
- `pomodoro/services.py` start_focus 等のスタブ
- `pomodoro/routes.py` で API 実装
- `templates/pomodoro/index.html` & `static/js/timer.js` 最小実装

---

この文書は MVP〜拡張までを俯瞰するためのガイドラインとして利用できます。必要に応じて更新してください。
