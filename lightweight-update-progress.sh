#!/bin/bash

# 軽量タスク進捗更新スクリプト
# PC負荷軽減を考慮した進捗管理

set -e

PROJECT_ROOT="/Users/yono/Build/TradeFlow"
CLAUDE_DIR="$PROJECT_ROOT/scripts/Claude-Code-Communication"
TASK_STATE_FILE="$CLAUDE_DIR/.task_state.json"

# 引数チェック
if [ $# -ne 1 ]; then
    echo "使用方法: $0 <進捗率(0-100)>"
    echo "例: $0 50"
    exit 1
fi

PROGRESS=$1

# 進捗率の検証
if ! [[ "$PROGRESS" =~ ^[0-9]+$ ]] || [ "$PROGRESS" -lt 0 ] || [ "$PROGRESS" -gt 100 ]; then
    echo "❌ 進捗率は0-100の整数で入力してください"
    exit 1
fi

# タスク状態ファイルの存在確認
if [ ! -f "$TASK_STATE_FILE" ]; then
    echo "❌ タスク状態ファイルが見つかりません: $TASK_STATE_FILE"
    exit 1
fi

# 現在の状態を読み込み
CURRENT_STATE=$(cat "$TASK_STATE_FILE")
CURRENT_TASK=$(echo "$CURRENT_STATE" | jq -r '.current_task // "unknown"')
ACTIVE_ENGINEER=$(echo "$CURRENT_STATE" | jq -r '.active_engineer // "unknown"')

# 進捗更新
NEW_STATE=$(echo "$CURRENT_STATE" | jq ".current_session.progress = $PROGRESS | .progress = $PROGRESS | .last_updated = \"$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)\"" )

# ファイルに保存
echo "$NEW_STATE" > "$TASK_STATE_FILE"

# 結果表示
echo "✅ 進捗更新完了"
echo "タスク: $CURRENT_TASK"
echo "エンジニア: $ACTIVE_ENGINEER"
echo "進捗: $PROGRESS%"

# 進捗に応じたメッセージ
if [ "$PROGRESS" -eq 0 ]; then
    echo "🚀 タスク開始"
elif [ "$PROGRESS" -eq 100 ]; then
    echo "🎉 タスク完了！"
elif [ "$PROGRESS" -ge 75 ]; then
    echo "🔥 もう少しで完了！"
elif [ "$PROGRESS" -ge 50 ]; then
    echo "⚡ 順調に進行中"
elif [ "$PROGRESS" -ge 25 ]; then
    echo "📈 進捗良好"
else
    echo "🌱 作業開始"
fi

# Obsidianログに記録（軽量版）
LOG_DIR="$HOME/ObsidianVault/claude_logs"
if [ -d "$LOG_DIR" ]; then
    TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
    LOG_FILE="$LOG_DIR/progress_${TIMESTAMP}.md"
    
    cat > "$LOG_FILE" << EOF
# 進捗更新ログ

- **タスク**: $CURRENT_TASK
- **エンジニア**: $ACTIVE_ENGINEER
- **進捗**: $PROGRESS%
- **更新日時**: $(date)

## 進捗状況
\`\`\`json
$NEW_STATE
\`\`\`
EOF
    
    echo "📝 進捗ログ保存: $LOG_FILE"
fi 