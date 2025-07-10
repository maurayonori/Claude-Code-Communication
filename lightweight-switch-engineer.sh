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
    ENGINEER="${ENGINEERS[$((${1}-1))]}"
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
