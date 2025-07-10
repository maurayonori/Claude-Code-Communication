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
