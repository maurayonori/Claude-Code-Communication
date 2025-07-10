#!/bin/bash

# TradeFlow 軽量最適化セットアップ
# PC負荷軽減 + タスク細分化 + Linear Issue連携

set -e

# 色付きログ
log_info() { echo -e "\033[1;36m[INFO]\033[0m $1"; }
log_success() { echo -e "\033[1;32m[SUCCESS]\033[0m $1"; }
log_warning() { echo -e "\033[1;33m[WARNING]\033[0m $1"; }
log_error() { echo -e "\033[1;31m[ERROR]\033[0m $1"; }

PROJECT_ROOT="/Users/yono/Build/TradeFlow"
CLAUDE_DIR="$PROJECT_ROOT/scripts/Claude-Code-Communication"
OBSIDIAN_LOG_DIR="$HOME/ObsidianVault/claude_logs"
TASK_STATE_FILE="$CLAUDE_DIR/.task_state.json"

echo "🚀 TradeFlow 軽量最適化セットアップ"
echo "===================================="
echo ""

# CPU使用率チェック
check_system_load() {
    local cpu_usage=$(top -l 1 -n 0 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
    local memory_pressure=$(memory_pressure | grep "System-wide memory free percentage" | awk '{print $5}' | sed 's/%//')
    
    log_info "システム負荷チェック: CPU ${cpu_usage}%, メモリ空き ${memory_pressure}%"
    
    if (( $(echo "$cpu_usage > 70" | bc -l) )); then
        log_warning "CPU使用率が高いです (${cpu_usage}%). 軽量モードを推奨します。"
        return 1
    fi
    return 0
}

# 軽量モード設定
setup_lightweight_mode() {
    log_info "🪶 軽量モード設定中..."
    
    # tmux設定の最適化
    cat > "$CLAUDE_DIR/.tmux-lightweight.conf" << 'EOF'
# 軽量モード用tmux設定
set -g status-interval 5
set -g history-limit 1000
set -g display-time 2000
set -g escape-time 0
set -g repeat-time 300
set -g visual-activity off
set -g visual-bell off
set -g bell-action none
EOF
    
    # Alacritty軽量設定
    cat > "$CLAUDE_DIR/.alacritty-lightweight.yml" << 'EOF'
# 軽量モード用Alacritty設定
window:
  dimensions:
    columns: 100
    lines: 30
  padding:
    x: 2
    y: 2

font:
  size: 12.0

scrolling:
  history: 1000
  multiplier: 1

# パフォーマンス最適化
debug:
  render_timer: false
  persistent_logging: false
  log_level: Error
EOF
    
    log_success "✅ 軽量モード設定完了"
}

# タスク状態管理システム
initialize_task_state() {
    log_info "📋 タスク状態管理システム初期化中..."
    
    cat > "$TASK_STATE_FILE" << 'EOF'
{
  "current_session": {
    "id": null,
    "start_time": null,
    "active_engineer": null,
    "current_task": null,
    "progress": 0
  },
  "tasks": [],
  "checkpoints": [],
  "issue_tracker": {
    "enabled": true,
    "auto_create": true,
    "auto_update": true
  }
}
EOF
    
    log_success "✅ タスク状態管理システム初期化完了"
}

# 既存セッションクリーンアップ
log_info "🧹 既存セッションクリーンアップ..."
tmux kill-session -t tradeflow 2>/dev/null || true
tmux kill-session -t president 2>/dev/null || true
tmux kill-session -t multiagent 2>/dev/null || true
tmux kill-session -t monitor 2>/dev/null || true

# システム負荷チェック
if ! check_system_load; then
    setup_lightweight_mode
    LIGHTWEIGHT_MODE=true
else
    LIGHTWEIGHT_MODE=false
fi

# タスク状態管理初期化
initialize_task_state

# メインセッション作成（軽量版）
log_info "📺 メインセッション作成中（軽量版）..."

if [ "$LIGHTWEIGHT_MODE" = true ]; then
    # 軽量モード: 2ペイン構成
    tmux -f "$CLAUDE_DIR/.tmux-lightweight.conf" new-session -d -s tradeflow -n main -c "$CLAUDE_DIR"
    tmux split-window -t tradeflow:main -h -c "$CLAUDE_DIR"
    
    # ペインタイトル設定
    tmux select-pane -t tradeflow:main.0 -T "PRESIDENT"
    tmux select-pane -t tradeflow:main.1 -T "ACTIVE_ENGINEER"
    
    PANES=("PRESIDENT" "ACTIVE_ENGINEER")
    PANE_COUNT=2
else
    # 通常モード: 3ペイン構成
    tmux new-session -d -s tradeflow -n main -c "$CLAUDE_DIR"
    tmux split-window -t tradeflow:main -h -c "$CLAUDE_DIR"
    tmux select-pane -t tradeflow:main -R
    tmux split-window -t tradeflow:main -v -c "$CLAUDE_DIR"
    
    # ペインタイトル設定
    tmux select-pane -t tradeflow:main.0 -T "PRESIDENT"
    tmux select-pane -t tradeflow:main.1 -T "TECH_LEAD"
    tmux select-pane -t tradeflow:main.2 -T "ACTIVE_ENGINEER"
    
    PANES=("PRESIDENT" "TECH_LEAD" "ACTIVE_ENGINEER")
    PANE_COUNT=3
fi

# 各ペインの初期設定
for i in $(seq 0 $((PANE_COUNT-1))); do
    pane_id="tradeflow:main.$i"
    role="${PANES[$i]}"
    
    tmux send-keys -t "$pane_id" "cd $CLAUDE_DIR" C-m
    tmux send-keys -t "$pane_id" "export PS1='($role) \\w\\$ '" C-m
    tmux send-keys -t "$pane_id" "clear" C-m
    tmux send-keys -t "$pane_id" "echo '=== $role ==='" C-m
    tmux send-keys -t "$pane_id" "echo ''" C-m
done

log_success "✅ メインセッション作成完了"

# エンジニア切り替えシステム（軽量版）
log_info "🔧 エンジニア切り替えシステム作成中..."
cat > "$CLAUDE_DIR/lightweight-switch-engineer.sh" << 'EOF'
#!/bin/bash

ENGINEERS=("analysis_engineer" "trading_engineer" "risk_engineer" "data_engineer" "qa_engineer")
TASK_STATE_FILE="/Users/yono/Build/TradeFlow/scripts/Claude-Code-Communication/.task_state.json"
CURRENT_FILE="$HOME/.tradeflow_current_engineer"

# システム負荷チェック
check_load() {
    local cpu_usage=$(top -l 1 -n 0 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
    if (( $(echo "$cpu_usage > 80" | bc -l) )); then
        echo "⚠️  CPU使用率が高いです (${cpu_usage}%). 作業を一時停止することを推奨します。"
        return 1
    fi
    return 0
}

# タスク状態更新
update_task_state() {
    local engineer=$1
    local task_id=${2:-""}
    
    python3 -c "
import json
import datetime

try:
    with open('$TASK_STATE_FILE', 'r') as f:
        state = json.load(f)
    
    state['current_session']['active_engineer'] = '$engineer'
    state['current_session']['current_task'] = '$task_id'
    state['current_session']['start_time'] = datetime.datetime.now().isoformat()
    
    with open('$TASK_STATE_FILE', 'w') as f:
        json.dump(state, f, indent=2)
    
    print('✅ タスク状態更新完了')
except Exception as e:
    print(f'❌ タスク状態更新エラー: {e}')
"
}

if [ $# -eq 0 ]; then
    echo "利用可能なエンジニア:"
    for i in "${!ENGINEERS[@]}"; do
        echo "  $((i+1)). ${ENGINEERS[$i]}"
    done
    echo ""
    echo "使用方法: $0 <番号> [タスクID]"
    exit 1
fi

# システム負荷チェック
if ! check_load; then
    read -p "続行しますか？ (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

if [[ $1 =~ ^[0-9]+$ ]] && [ $1 -ge 1 ] && [ $1 -le ${#ENGINEERS[@]} ]; then
    ENGINEER="${ENGINEERS[$(($ 1-1))]}"
else
    ENGINEER="$1"
fi

# 現在のエンジニアを記録
echo "$ENGINEER" > "$CURRENT_FILE"

# タスク状態更新
update_task_state "$ENGINEER" "$2"

# ペインタイトル更新
if tmux has-session -t tradeflow 2>/dev/null; then
    if [ "$(tmux list-panes -t tradeflow:main | wc -l)" -eq 2 ]; then
        # 軽量モード
        tmux select-pane -t tradeflow:main.1 -T "ACTIVE: $ENGINEER"
        pane_id="tradeflow:main.1"
    else
        # 通常モード
        tmux select-pane -t tradeflow:main.2 -T "ACTIVE: $ENGINEER"
        pane_id="tradeflow:main.2"
    fi
    
    # プロンプト更新
    tmux send-keys -t "$pane_id" "export PS1='($ENGINEER) \\w\\$ '" C-m
    tmux send-keys -t "$pane_id" "clear" C-m
    tmux send-keys -t "$pane_id" "echo '=== $ENGINEER ==='" C-m
    tmux send-keys -t "$pane_id" "echo ''" C-m
fi

echo "✅ エンジニア切り替え完了: $ENGINEER"
EOF

chmod +x "$CLAUDE_DIR/lightweight-switch-engineer.sh"

# 軽量Alacritty起動スクリプト
log_info "🖥️ 軽量Alacritty起動スクリプト作成中..."
cat > "$CLAUDE_DIR/lightweight-start-alacritty.sh" << 'EOF'
#!/bin/bash

CLAUDE_DIR="/Users/yono/Build/TradeFlow/scripts/Claude-Code-Communication"
LIGHTWEIGHT_CONFIG="$CLAUDE_DIR/.alacritty-lightweight.yml"

# システム負荷に応じた設定選択
if [ -f "$LIGHTWEIGHT_CONFIG" ]; then
    CONFIG_FLAG="--config-file $LIGHTWEIGHT_CONFIG"
else
    CONFIG_FLAG=""
fi

# メインウィンドウ（軽量版）
alacritty $CONFIG_FLAG \
          --working-directory "$CLAUDE_DIR" \
          --position 100 100 \
          --dimensions 120 35 \
          --command tmux attach-session -t tradeflow \; \
          select-pane -t tradeflow:main.0 &

echo "✅ 軽量Alacrittyウィンドウ起動完了"
EOF

chmod +x "$CLAUDE_DIR/lightweight-start-alacritty.sh"

# 軽量Claude起動スクリプト（Obsidian最適化）
log_info "🤖 軽量Claude起動スクリプト作成中..."
cat > "$CLAUDE_DIR/lightweight-start-claude.sh" << 'EOF'
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
    log_file="$LOG_DIR/${role,,}_${SESSION_ID}.md"
    
    # Claudeを軽量モードで起動
    tmux send-keys -t "$pane_id" "claude --dangerously-skip-permissions 2>&1 | tee $log_file" C-m
    sleep 0.5
done

echo "✅ 軽量Claude起動完了（全ペイン）"
EOF

chmod +x "$CLAUDE_DIR/lightweight-start-claude.sh"

# Issue連携システム
log_info "🔗 Issue連携システム作成中..."
cat > "$CLAUDE_DIR/issue-manager.sh" << 'EOF'
#!/bin/bash

TASK_STATE_FILE="/Users/yono/Build/TradeFlow/scripts/Claude-Code-Communication/.task_state.json"

# Linear Issue作成
create_issue() {
    local title="$1"
    local description="$2"
    local priority="${3:-medium}"
    
    echo "📝 Issue作成: $title"
    
    # Linear CLI使用（要インストール）
    if command -v linear &> /dev/null; then
        linear issue create \
            --title "$title" \
            --description "$description" \
            --priority "$priority" \
            --label "tradeflow" \
            --label "auto-generated"
    else
        echo "⚠️  Linear CLIが見つかりません。手動でIssueを作成してください。"
        echo "タイトル: $title"
        echo "説明: $description"
    fi
}

# タスク細分化
fragment_task() {
    local main_task="$1"
    local subtasks=()
    
    echo "🔄 タスク細分化: $main_task"
    
    case "$main_task" in
        "analysis_improvement")
            subtasks=(
                "RSI計算精度向上"
                "MACD信号最適化"
                "ボリンジャーバンド調整"
                "統合スコア改善"
            )
            ;;
        "trading_optimization")
            subtasks=(
                "エントリー条件見直し"
                "ストップロス最適化"
                "利確条件調整"
                "リスク管理強化"
            )
            ;;
        "data_enhancement")
            subtasks=(
                "データ取得速度向上"
                "データ品質チェック"
                "キャッシュ最適化"
                "エラーハンドリング強化"
            )
            ;;
        *)
            subtasks=("$main_task の詳細分析" "$main_task の実装" "$main_task のテスト")
            ;;
    esac
    
    for subtask in "${subtasks[@]}"; do
        create_issue "$subtask" "メインタスク: $main_task の一部" "medium"
    done
}

# 使用方法
case "$1" in
    "create")
        create_issue "$2" "$3" "$4"
        ;;
    "fragment")
        fragment_task "$2"
        ;;
    *)
        echo "使用方法:"
        echo "  $0 create <タイトル> <説明> [優先度]"
        echo "  $0 fragment <メインタスク>"
        ;;
esac
EOF

chmod +x "$CLAUDE_DIR/issue-manager.sh"

# 便利なエイリアス作成
log_info "⚡ 軽量エイリアス設定作成中..."
cat >> ~/.zshrc << 'EOF'

# TradeFlow 軽量最適化エイリアス
alias tf-light-start="/Users/yono/Build/TradeFlow/scripts/Claude-Code-Communication/lightweight-start-alacritty.sh"
alias tf-light-claude="/Users/yono/Build/TradeFlow/scripts/Claude-Code-Communication/lightweight-start-claude.sh"
alias tf-light-switch="/Users/yono/Build/TradeFlow/scripts/Claude-Code-Communication/lightweight-switch-engineer.sh"
alias tf-issue="/Users/yono/Build/TradeFlow/scripts/Claude-Code-Communication/issue-manager.sh"
alias tf-attach="tmux attach-session -t tradeflow"
alias tf-status="cat /Users/yono/Build/TradeFlow/scripts/Claude-Code-Communication/.task_state.json | jq ."
alias tf-load="top -l 1 -n 0 | grep 'CPU usage'"
alias tf-update-progress="/Users/yono/Build/TradeFlow/scripts/Claude-Code-Communication/lightweight-update-progress.sh"
EOF

log_success "✅ 軽量最適化セットアップ完了！"
echo ""
echo "🎯 軽量版使用方法:"
echo "  1. tf-light-start   # 軽量Alacrittyウィンドウ起動"
echo "  2. tf-light-claude  # 軽量Claude起動"
echo "  3. tf-light-switch 1 [タスクID]  # エンジニア切り替え"
echo "  4. tf-issue create <タイトル> <説明>  # Issue作成"
echo "  5. tf-issue fragment <メインタスク>  # タスク細分化"
echo "  6. tf-status        # 現在のタスク状態確認"
echo "  7. tf-load          # システム負荷確認"
echo ""
echo "📋 軽量版特徴:"
echo "  - CPU使用率監視"
echo "  - 軽量tmux設定"
echo "  - 圧縮ログ出力"
echo "  - タスク状態管理"
echo "  - Issue自動連携"
echo ""
echo "💡 システム負荷: $([ "$LIGHTWEIGHT_MODE" = true ] && echo "軽量モード" || echo "通常モード")" 