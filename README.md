# ClaudeCodeCommunication

## 概要
ClaudeCodeCommunicationは、Claudeとの効率的なコード通信を実現するためのツールセットです。

## 🚀 理想的な日常運用（推奨）

### 🎯 設計思想
1. **PC負荷軽減**: 自動負荷監視とクリーンアップ
2. **タスク細分化**: 大きなタスクを小さな単位に分割
3. **自動再起動**: 作業完了後の自動クリーンアップ＆再起動
4. **Obsidian最適化**: ログローテーションと圧縮記録
5. **セッション管理**: President + MultiAgent の2セッション構成

### 📋 毎日の運用手順

#### 1. 初回セットアップ（一度だけ実行）
```bash
# エイリアス設定
./scripts/Claude-Code-Communication/setup-daily-aliases.sh
source ~/.zshrc
```

#### 2. 日常運用開始
```bash
# 毎日の作業開始
tf-daily
```

**自動実行される処理:**
- システム負荷チェック（CPU70%以上で軽量モード）
- 既存セッションクリーンアップ
- President + MultiAgent セッション作成
- Claude起動（全エンジニア）
- Alacritty起動（President画面メイン）
- タスク状態初期化
- 自動再起動システム設定

#### 3. 作業実行
```bash
# President画面で指令を出す
# 例: "RSI計算の精度を向上させてください"

# 必要に応じてMultiAgent画面を監視
tf-attach-multiagent
```

#### 4. 進捗管理
```bash
# 進捗更新
tf-progress 25   # 25%完了
tf-progress 50   # 50%完了
tf-progress 100  # 完了（自動再起動トリガー）

# 状態確認
tf-status
```

#### 5. 自動再起動
タスクが100%完了すると、5秒後に自動的に：
- 現在のセッションを終了
- 新しいサイクルを開始
- 新しいPresident画面が表示

### 🎮 便利コマンド

#### 基本コマンド
```bash
tf-daily           # 日常運用開始
tf-status          # タスク状態確認
tf-progress <数値> # 進捗更新（0-100）
tf-restart         # 手動再起動
tf-load            # システム負荷確認
tf-logs            # 最新ログ確認
```

#### セッション管理
```bash
tf-attach-president    # President画面に接続
tf-attach-multiagent   # MultiAgent画面に接続
tf-kill-all           # 全セッション終了
```

### 📊 セッション構成

#### President セッション
```
┌─────────────────────────────────────┐
│                                     │
│            PRESIDENT                │
│         (メイン指令画面)              │
│                                     │
└─────────────────────────────────────┘
```

#### MultiAgent セッション（監視用）
```
┌─────────────┬─────────────┬─────────────┐
│ ANALYSIS    │ DATA        │ TRADING     │
│ ENGINEER    │ ENGINEER    │ ENGINEER    │
├─────────────┼─────────────┼─────────────┤
│ RISK        │ TECH        │ MONITORING  │
│ ENGINEER    │ LEAD        │             │
└─────────────┴─────────────┴─────────────┘
```

### 🔄 自動再起動システム

#### 仕組み
1. **タスク完了検出**: 進捗が100%になると自動検出
2. **待機時間**: 5秒間の確認時間
3. **クリーンアップ**: 現在のセッションを安全に終了
4. **新サイクル開始**: 新しいPresident画面で再開

#### 手動再起動
```bash
# 緊急時の手動再起動
tf-restart

# 完全リセット
tf-kill-all
tf-daily
```

### 📝 ログ管理

#### Obsidianログ
- **保存場所**: `~/ObsidianVault/claude_logs/`
- **ローテーション**: 7日以上古いログを自動削除
- **形式**: Markdown形式で圧縮記録

#### ログ確認
```bash
# 最新ログ確認
tf-logs

# 特定のログ確認
ls -la ~/ObsidianVault/claude_logs/
```

### 🔧 トラブルシューティング

#### よくある問題

1. **Alacrittyが起動しない**
   ```bash
   # 既存セッションを終了
   tf-kill-all
   
   # 再起動
   tf-daily
   ```

2. **PC負荷が高い**
   ```bash
   # 負荷確認
   tf-load
   
   # 軽量モードで再起動
   tf-kill-all
   tf-daily  # 自動的に軽量モードが適用される
   ```

3. **タスクが途中で止まった**
   ```bash
   # 現在の状態確認
   tf-status
   
   # 手動で進捗更新
   tf-progress 100
   
   # 自動再起動
   tf-restart
   ```

4. **セッションが見つからない**
   ```bash
   # セッション一覧確認
   tmux list-sessions
   
   # 手動でセッション作成
   tf-daily
   ```

### 💡 運用のコツ

#### 効率的な使い方
1. **朝の起動**: `tf-daily`で一日の作業開始
2. **指令の出し方**: President画面で具体的な指示
3. **監視**: 必要に応じてMultiAgent画面で進捗確認
4. **進捗更新**: 25%、50%、75%、100%で段階的に更新
5. **自動再起動**: 100%完了後は自動的に次のサイクル

#### タスク細分化
- 大きなタスクは小さな単位に分割
- 各サブタスクは1-2時間で完了可能なサイズ
- 進捗を定期的に更新してチェックポイント作成

#### PC負荷軽減
- CPU使用率70%以上で自動的に軽量モード
- 不要なログは自動削除
- セッションの適切なクリーンアップ

### 🎯 期待される効果

#### ユーザーの手間軽減
- **起動**: 1コマンド（`tf-daily`）で全環境構築
- **監視**: President画面で報告待ち
- **再起動**: 自動的にクリーンアップ＆再開
- **進捗管理**: 簡単な数値更新のみ

#### PC負荷軽減
- **自動負荷監視**: 高負荷時の軽量モード切り替え
- **ログ管理**: 古いログの自動削除
- **プロセス管理**: 適切なクリーンアップ
- **メモリ最適化**: 不要なプロセスの終了

#### 作業継続性
- **タスク状態管理**: JSON形式での永続化
- **チェックポイント**: 進捗に応じた復旧ポイント
- **ログ記録**: Obsidianでの詳細記録
- **自動再開**: 中断後の自動復旧

## 🔧 従来の手動運用（非推奨）

<details>
<summary>従来の手動運用方法（クリックで展開）</summary>

### 軽量最適化版（手動）
- `tf-light-start`: 軽量Alacrittyウィンドウ起動
- `tf-light-claude`: 軽量Claude起動
- `tf-light-switch`: エンジニア切り替え

### マルチエージェント接続（手動）
- `tmux attach -t president`: President接続
- `tmux attach -t multiagent`: MultiAgent接続

</details>

---

## 📚 技術仕様

### 対応環境
- **OS**: macOS (Darwin)
- **ターミナル**: Alacritty（推奨）
- **セッション管理**: tmux
- **ログ管理**: Obsidian

### 依存関係
- tmux
- jq
- bc
- Alacritty
- Claude CLI

### ファイル構成
```
scripts/Claude-Code-Communication/
├── optimized-daily-workflow.sh    # メイン運用スクリプト
├── setup-daily-aliases.sh         # エイリアス設定
├── auto-restart-cycle.sh          # 自動再起動
├── lightweight-update-progress.sh # 進捗更新
├── .task_state.json               # タスク状態管理
└── README.md                      # このファイル
```

---

## 🎉 まとめ

この日常運用システムにより：

1. **毎日の作業開始**: `tf-daily`コマンド1つで完全な環境構築
2. **効率的な作業**: President画面での指令出し、MultiAgent監視
3. **自動管理**: 進捗に応じた自動再起動とクリーンアップ
4. **負荷軽減**: システム負荷に応じた自動最適化
5. **継続性**: タスク状態管理とログ記録による作業継続

**理想的な1日の流れ:**
1. 朝: `tf-daily`で環境起動
2. 作業: President画面で指令、進捗更新
3. 完了: 自動再起動で次のサイクル開始
4. 繰り返し: 必要に応じて複数サイクル実行

これにより、手間を最小限に抑えながら、PC負荷を軽減し、効率的な開発サイクルを実現できます。 