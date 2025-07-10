#!/bin/bash

# TradeFlow自動再起動サイクル
# 作業完了後の自動クリーンアップ＆再起動

CLAUDE_DIR="/Users/yono/Build/TradeFlow/scripts/Claude-Code-Communication"
TASK_STATE_FILE="$CLAUDE_DIR/.task_state.json"

# 現在のタスクが完了しているかチェック
check_task_completion() {
    if [ -f "$TASK_STATE_FILE" ]; then
        local progress=$(cat "$TASK_STATE_FILE" | jq -r '.current_session.progress // 0')
        if [ "$progress" -eq 100 ]; then
            return 0  # 完了
        fi
    fi
    return 1  # 未完了
}

# 自動再起動実行
if check_task_completion; then
    echo "🎉 タスク完了検出 - 自動再起動開始"
    
    # 5秒待機（ユーザーが結果を確認する時間）
    sleep 5
    
    # 現在のセッションを終了
    tmux kill-session -t president 2>/dev/null || true
    tmux kill-session -t multiagent 2>/dev/null || true
    
    # 新しいサイクルを開始
    "$CLAUDE_DIR/optimized-daily-workflow.sh"
else
    echo "⏳ タスク進行中 - 再起動をスキップ"
fi
