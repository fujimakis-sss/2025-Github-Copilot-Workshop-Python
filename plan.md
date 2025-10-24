# 段階的実装計画 (ポモドーロタイマー)

## 開発フェーズ概要

| フェーズ | 目的 | ゴール (完了条件) |
|----------|------|------------------|
| Phase0 (準備) | 開発基盤整備 | Flask起動/DB接続/最低テスト通過/README更新 |
| Phase1 (MVPコア) | 最小タイマー + 状態/統計 | フォーカス/休憩開始・停止・状態復元・日次統計表示・円形UI動作 |
| Phase2 (拡張) | 快適性 & 継続利用性 | 長休憩/プリセット/週間統計/WebSocket通知/簡易認証 |
| Phase3 (高度) | マルチユーザー & 分析 | 本格認証/タグ・分析/PWA/外部連携 |
| Phase3+ (最適化) | 品質/スケール/成長 | メトリクス・監視・Gamification・A/Bテスト |

## エピックとユーザーストーリー分解

### Phase0 エピック: 基盤整備

| Story ID | ユーザーストーリー | タスク概要 |
|----------|---------------------|-----------|
| P0-ENV | 開発者として、環境変数を使い設定を切替えたい | config.py/.envテンプレ実装, SECRET_KEY/DB URI読込 |
| P0-APP | 開発者として、Flaskアプリを起動したい | create_app関数, Blueprint登録, 起動スクリプト |
| P0-DB  | 開発者として、DBにモデルを作成したい | SQLAlchemy初期化, Sessionモデル作成, Migration準備 |
| P0-TEST | 開発者として、安全に改修できるよう最初のテストを走らせたい | pytest設定, servicesダミーテスト |
| P0-DOC | ユーザーとして、セットアップ手順を知りたい | README基本手順/architecture.mdリンク |

### Phase1 エピック: MVPタイマー

| Story ID | ユーザーストーリー | タスク概要 |
|----------|---------------------|-----------|
| P1-START | 利用者として、フォーカスを開始したい | API POST /start, services.start_focus, バリデーション |
| P1-BREAK | 利用者として、休憩を開始したい | API POST /break, services.start_break |
| P1-STOP  | 利用者として、進行中を中断したい | API POST /stop, active検出/状態更新 |
| P1-STATE | 利用者として、再読込後も正しい状態を見たい | GET /state, remaining計算ロジック |
| P1-STATS | 利用者として、今日の実績を確認したい | DailyStatモデル, 集計更新サービス, GET /stats/daily |
| P1-UI    | 利用者として、残り時間を視覚的に把握したい | 円形プログレスCSS/JS, timer.jsカウントダウン |
| P1-VALID | 利用者として、不正値を弾いてほしい | duration範囲チェック, エラーレスポンス共通化 |
| P1-LOG   | 管理者として、操作履歴を追いたい | ログフォーマット(JSON), start/stop出力 |
| P1-TEST  | 開発者として、主要ロジックを保証したい | servicesユニット, routes統合テスト |
| P1-ACCESS | 利用者として、キーボード操作しやすくあってほしい | aria-label, focus順序確認 |

### Phase2 エピック: 利便性拡張

| Story ID | ユーザーストーリー | タスク概要 |
|----------|---------------------|-----------|
| P2-LBREAK | 利用者として、一定回数後に長休憩を促されたい | cycleカウンタ, 長休憩提案ロジック |
| P2-PRESET | 利用者として、所定プリセットを選択したい | プリセットUI, start時duration差し替え |
| P2-WEEK   | 利用者として、今週/月の進捗を見たい | 集計API summary, 期間フィルタ |
| P2-WSYNC  | 利用者として、複数タブで同期したい | SocketIO導入, state_update push |
| P2-NOTIF  | 利用者として、終了時に通知を受けたい | Notification API許諾/UIフロー |
| P2-LAUTH  | 利用者として、履歴を自分専用にしたい | 単純ユーザー/パスワード, セッション管理 |
| P2-TAG    | 利用者として、作業カテゴリを記録したい | tag入力UI, Sessionタグ保存, 集計拡張 |
| P2-THEME  | 利用者として、暗い環境でも見やすくしたい | ダークテーマCSS切替 |
| P2-I18N   | 利用者として、言語を選びたい | 文言辞書, 言語選択UI, locale保持 |

### Phase3 エピック: 高度化

| Story ID | ユーザーストーリー | タスク概要 |
|----------|---------------------|-----------|
| P3-AUTH  | 利用者として、安全にログインしたい | Flask-Login, パスワードハッシュ化, RBAC(将来) |
| P3-OAUTH | 利用者として、外部アカウントでログインしたい | OAuthフロー, トークン保存 |
| P3-BADGE | 利用者として、達成感を得たい | バッジ条件定義, 付与ロジック, UI表示 |
| P3-ANALYTICS | 利用者として、集中パターンを把握したい | 高度統計計算, グラフ描画 |
| P3-PWA   | 利用者として、モバイルで手軽に使いたい | manifest, service worker, offline fallback |
| P3-EXPORT | 利用者として、履歴を他ツールへ活用したい | CSV/JSON生成API |
| P3-METRICS | 管理者として、稼働状況を監視したい | /metrics導入, Prometheus統合 |
| P3-ABTEST | 管理者として、UI改善を検証したい | バリアント出し分け, 計測集計 |

## 依存関係 / ブロッカー

| 項目 | 依存/前提 | 解決策 |
|------|-----------|--------|
| WebSocket導入 | SocketIOライブラリ/Redis | Phase2開始時にrequirements & コンテナ準備 |
| OAuth | 外部クライアントID/Secret | セキュリティレビュー後に環境変数セット |
| PWA | HTTPS配信 | デプロイ環境でTLS終端設定 |
| 週間統計 | DailyStat精度 | Phase1で集計信頼性テスト追加 |
| Export | 完整合性 | Migration後スキーマ固定化 |

## タスク粒度指針

- 1タスク目安: 30分〜2時間で完了できるサイズ (routes+services+test+docの最小セット)
- 複雑機能は: 設計/モデル/実装/UI/テスト をサブタスク化し並行しない
- WebSocketや認証などクロスカットはスパイク (調査タスク) → 実装タスク

## ブランチ / Issue 運用

| 項目 | 規約例 |
|------|--------|
| Branch命名 | `feature/<id>-<slug>` 例: `feature/MVP-1-start-focus` |
| Issueテンプレ | 概要 / 背景 / 受入条件 / 実装方針 / テスト項目 |
| PRサイズ | 変更行 < ~400行、機能毎に分割 |
| レビュー基準 | AC満足 / テスト緑 / Lintパス / ドキュメント更新 |

## 品質ゲート / 計測

| フェーズ | テスト領域 | 自動化指標 | 成功閾値 |
|----------|------------|------------|----------|
| Phase0 | smoke, 環境読み込み | pytest最小 | PASS |
| Phase1 | servicesユニット/ routes統合 / UIスナップ | 単体/統合成功率 | >95% PASS |
| Phase2 | WebSocketイベント / 通知 / 多言語 | イベントテスト数 | 全主要イベントPASS |
| Phase3 | 認証/権限/バッジ | セキュリティテスト | 重大脆弱性0 |
| Phase3+ | 負荷/パフォーマンス | P95レスポンス <300ms | 維持 |

メトリクス例 (拡張): 平均集中長, 1日あたり完了サイクル数, 失敗(中断)率。

## リリース戦略

| ステップ | 内容 | ロールバック |
|----------|------|--------------|
| Dev環境 | 逐次マージ/小刻みPR | Git revert/前タグ復帰 |
| Staging | Phase完了毎にデプロイ | 直前タグへ戻す |
| Prod MVP | Phase1完了後タグ付与 | Blue/Green切替 |
| 増分リリース | 小機能ごと Feature Flag | Flag OFF |

## リスク軽減策

- 設計ドキュメント更新をPR必須チェックに組込
- 大幅機能 (OAuth/PWA) はスパイク結果共有後に実装着手
- 定期的 (週次) に未使用セッション/統計差異チェックスクリプト

## Phase1 詳細タスク例 (展開サンプル)

| Task ID | Story | 作業内容 | 成果物 |
|---------|-------|----------|--------|
| T1 | P0-APP | create_app + Blueprint登録 | app.py / pomodoro/__init__.py |
| T2 | P0-DB | models: PomodoroSession, DailyStat | models.py |
| T3 | P1-START | service + route + テスト | services.py / routes.py / test_services.py |
| T4 | P1-BREAK | service + route + テスト | 同上 |
| T5 | P1-STATE | state計算 + route | services.get_state |
| T6 | P1-STATS | 集計ロジック + daily route | services.update_stats |
| T7 | P1-UI | index.html + timer.js (円形描画) | templates/static |
| T8 | P1-VALID | durationバリデーション共通化 | validators util |
| T9 | P1-LOG | ログ設定 (JSONFormatter) | logging設定ファイル |
| T10 | P1-TEST | 統合テスト追加 | tests/ |
| T11 | P1-ACCESS | aria属性/キーボード確認 | index.html |
| T12 | リファクタ | 重複コード除去 | 各ファイル |

## 予備調査 (スパイク) タスク例

| Spike ID | 目的 | 成果物 |
|----------|------|--------|
| S1 | 円形プログレスCSS最適化 | サンプルコード/メモ |
| S2 | Flask-SocketIO負荷挙動 | 計測結果/推奨設定 |
| S3 | PWAオフラインキャッシュ範囲 | manifest戦略案 |
| S4 | OAuthライブラリ比較 | 選定理由/設定手順 |

## ロードマップタイムライン (概算)

| 週 | Phase | 主タスク |
|----|-------|----------|
| 1 | Phase0 | 環境/基盤/初期モデル/テスト雛形 |
| 2-3 | Phase1 | コアAPI/UI/統計/ログ/バリデーション |
| 4-5 | Phase2 | 長休憩/プリセット/WebSocket/通知/簡易認証 |
| 6-7 | Phase3 | マルチ認証/タグ/分析/PWA/Export |
| 8+ | Phase3+ | 最適化/監視/Gamification/改善反復 |

## Doneの定義 (Definition of Done)

- コード: Lint/Format PASS + テスト緑
- ドキュメント: 関連 .md 更新済み (architecture/features/plan)
- セキュリティ: 新規機能で明確な脆弱性なし (静的解析 or レビュー)
- パフォーマンス: 既存指標劣化なし (重要APIレスポンスΔ <10%)
- リグレッション: 主要ユースケース手動動作確認

---

この計画は進捗に応じて随時更新してください。Issue化時は Story ID を参照し、PRは Task ID / Spike ID を含めた命名を行います。
