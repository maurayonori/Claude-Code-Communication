#!/bin/bash

# TradeFlow 日常運用最適化スクリプト
# 毎日の作業サイクルを自動化

set -e

# 色付きログ
log_info() { echo -e "\\033[1;36m[INFO]\\033[0m $1"; }
log_success() { echo -e "\\033[1;32m[SUCCESS]\\033[0m $1"; }
log_warning() { echo -e "\\033[1;33m[WARNING]\\033[0m $1"; }
log_error() { echo -e "\\033[1;31m[ERROR]\\033[0m $1"; }

PROJECT_ROOT="/Users/yono/Build/TradeFlow"
CLAUDE_DIR="$PROJECT_ROOT/scripts/Claude-Code-Communication"
TASK_STATE_FILE="$CLAUDE_DIR/.task_state.json"
LOG_DIR="$HOME/ObsidianVault/claude_logs"

echo "🚀 TradeFlow 日常運用開始"
echo "========================="
echo ""

# システム負荷チェック
check_system_load() {
    local cpu_usage=$(top -l 1 -n 0 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
    
    log_info "💻 システム負荷チェック"
    echo "  CPU使用率: ${cpu_usage}%"
    
    # CPU使用率が70%以上の場合は軽量モードを強制
    if (( $(echo "$cpu_usage > 70" | bc -l) )); then
        log_warning "⚠️  高負荷検出 - 軽量モードを適用"
        export LIGHTWEIGHT_MODE=true
    else
        export LIGHTWEIGHT_MODE=false
    fi
}

# 既存セッションクリーンアップ
cleanup_sessions() {
    log_info "🧹 既存セッションクリーンアップ"
    
    # 既存セッションを安全に終了
    tmux kill-session -t president 2>/dev/null || true
    tmux kill-session -t multiagent 2>/dev/null || true
    
    # プロセスクリーンアップ
    pkill -f "claude.*dangerously" 2>/dev/null || true
    sleep 2
    
    log_success "✅ クリーンアップ完了"
}

# 最適化されたセッション作成
create_optimized_sessions() {
    log_info "📺 最適化セッション作成"
    
    # メインセッション作成（president用）
    tmux new-session -d -s president -n main -c "$CLAUDE_DIR"
    
    # multiagentセッション作成（6ペイン構成）
    tmux new-session -d -s multiagent -n main -c "$CLAUDE_DIR"
    
    # multiagentセッションのペイン分割
    tmux split-window -t multiagent:main -h
    tmux split-window -t multiagent:main.0 -v
    tmux split-window -t multiagent:main.2 -v
    tmux split-window -t multiagent:main.1 -v
    tmux split-window -t multiagent:main.4 -v
    
    # ペインサイズ調整
    tmux select-layout -t multiagent:main tiled
    
    log_success "✅ セッション作成完了"
}

# Claude起動（最適化版）
start_claude_optimized() {
    log_info "🤖 Claude起動（最適化版）"
    
    # セッション情報
    SESSION_ID=$(date +%Y%m%d_%H%M%S)
    
    # Obsidianログディレクトリ準備
    mkdir -p "$LOG_DIR"
    
    # 古いログクリーンアップ（7日以上）
    find "$LOG_DIR" -name "*.md" -mtime +7 -delete 2>/dev/null || true
    
    # President用Claude起動
    log_info "  President起動中..."
    tmux send-keys -t president:main "claude --dangerously-skip-permissions 2>&1 | tee $LOG_DIR/president_${SESSION_ID}.md" C-m
    
    # MultiAgent用Claude起動
    log_info "  MultiAgent起動中..."
    ENGINEERS=("analysis_engineer" "data_engineer" "trading_engineer" "risk_engineer" "tech_lead" "monitoring")
    
    for i in "${!ENGINEERS[@]}"; do
        engineer="${ENGINEERS[$i]}"
        log_file="$LOG_DIR/${engineer}_${SESSION_ID}.md"
        tmux send-keys -t "multiagent:main.$i" "claude --dangerously-skip-permissions 2>&1 | tee $log_file" C-m
        sleep 1
    done
    
    log_success "✅ Claude起動完了"
}

# Alacritty起動（修正版）
start_alacritty_optimized() {
    log_info "🖥️ Alacritty起動（最適化版）"
    
    # President用ウィンドウ（メイン）
    alacritty --working-directory "$CLAUDE_DIR" \
              --title "TradeFlow-President" \
              --command tmux attach-session -t president &
    
    sleep 2
    
    # MultiAgent監視用ウィンドウ（オプション）
    if [ "$LIGHTWEIGHT_MODE" != "true" ]; then
        alacritty --working-directory "$CLAUDE_DIR" \
                  --title "TradeFlow-MultiAgent" \
                  --command tmux attach-session -t multiagent &
    fi
    
    log_success "✅ Alacritty起動完了"
}

# タスク状態初期化
initialize_task_state() {
    log_info "📋 タスク状態初期化"
    
    cat > "$TASK_STATE_FILE" << EOF
{
  "current_session": {
    "id": "$(date +%Y%m%d_%H%M%S)",
    "start_time": "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)",
    "active_engineer": "president",
    "current_task": "daily_startup",
    "progress": 0,
    "lightweight_mode": $LIGHTWEIGHT_MODE
  },
  "tasks": [],
  "checkpoints": [],
  "issue_tracker": {
    "enabled": true,
    "auto_create": true,
    "auto_update": true
  },
  "daily_cycle": {
    "cycle_count": 1,
    "last_restart": "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)",
    "auto_restart_enabled": true
  }
}
EOF
    
    log_success "✅ タスク状態初期化完了"
}

# 自動再起動システム
setup_auto_restart() {
    log_info "🔄 自動再起動システム設定"
    
    # 自動再起動スクリプト作成
    cat > "$CLAUDE_DIR/auto-restart-cycle.sh" << 'EOF'
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
EOF
    
    chmod +x "$CLAUDE_DIR/auto-restart-cycle.sh"
    
    log_success "✅ 自動再起動システム設定完了"
}

# メイン実行
main() {
    # 1. システム負荷チェック
    check_system_load
    
    # 2. クリーンアップ
    cleanup_sessions
    
    # 3. セッション作成
    create_optimized_sessions
    
    # 4. Claude起動
    start_claude_optimized
    
    # 5. Alacritty起動
    start_alacritty_optimized
    
    # 6. タスク状態初期化
    initialize_task_state
    
    # 7. 自動再起動システム
    setup_auto_restart
    
    echo ""
    echo "🎯 日常運用開始完了！"
    echo "====================="
    echo ""
    echo "📋 使用方法:"
    echo "  1. President画面で指令を出す"
    echo "  2. MultiAgent画面で作業状況を監視（オプション）"
    echo "  3. タスク完了後は自動的に再起動サイクルが開始"
    echo ""
    echo "⚡ 便利コマンド:"
    echo "  tf-status          # 現在のタスク状態確認"
    echo "  tf-update-progress # 進捗更新"
    echo "  tf-restart-cycle   # 手動再起動"
    echo "  tf-load            # システム負荷確認"
    echo ""
    echo "💡 システム負荷: $([ "$LIGHTWEIGHT_MODE" = "true" ] && echo "軽量モード" || echo "通常モード")"
    echo ""
    echo "🏃 President画面で作業を開始してください！"
}

# 実行
main "$@" 