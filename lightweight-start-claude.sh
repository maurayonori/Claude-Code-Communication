#!/bin/bash

CLAUDE_DIR="/Users/yono/Build/TradeFlow/scripts/Claude-Code-Communication"
LOG_DIR="$HOME/ObsidianVault/claude_logs"
TASK_STATE_FILE="$CLAUDE_DIR/.task_state.json"

mkdir -p "$LOG_DIR"

# ログローテーション（古いログ削除）
find "$LOG_DIR" -name "*.md" -mtime +7 -delete 2>/dev/null || true

# セッション情報取得
SESSION_ID=$(date +%Y%m%d_%H%M%S)
echo "🚀 セッション開始: $SESSION_ID"

# ペイン数チェック
PANE_COUNT=$(tmux list-panes -t tradeflow:main | wc -l)

if [ "$PANE_COUNT" -eq 2 ]; then
    # 軽量モード
    PANES=("PRESIDENT" "ACTIVE_ENGINEER")
    PANE_INDICES=(0 1)
else
    # 通常モード
    PANES=("PRESIDENT" "TECH_LEAD" "ACTIVE_ENGINEER")
    PANE_INDICES=(0 1 2)
fi

# 各ペインでClaude起動（軽量版）
for i in "${!PANES[@]}"; do
    pane_id="tradeflow:main.${PANE_INDICES[$i]}"
    role="${PANES[$i]}"
    
    # 軽量ログファイル（圧縮形式）
    log_file="$LOG_DIR/$(echo $role | tr '[:upper:]' '[:lower:]')_${SESSION_ID}.md"
    
    # Claudeを軽量モードで起動
    tmux send-keys -t "$pane_id" "claude --dangerously-skip-permissions 2>&1 | tee $log_file" C-m
    sleep 0.5
done

echo "✅ 軽量Claude起動完了（全ペイン）"
