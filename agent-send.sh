#!/bin/bash

# 🚀 TradeFlow Agent間メッセージ送信スクリプト

# tmuxのbase-indexとpane-base-indexを動的に取得
get_tmux_indices() {
    local session="$1"
    local window_index=$(tmux show-options -t "$session" -g base-index 2>/dev/null | awk '{print $2}')
    local pane_index=$(tmux show-options -t "$session" -g pane-base-index 2>/dev/null | awk '{print $2}')

    # デフォルト値
    window_index=${window_index:-0}
    pane_index=${pane_index:-0}

    echo "$window_index $pane_index"
}

# エージェント→tmuxターゲット マッピング (TradeFlow専門チーム対応)
get_agent_target() {
    case "$1" in
        "president") echo "president:0.0" ;;
        "tech_lead") echo "multiagent:0.0" ;;
        "analysis_engineer") echo "multiagent:0.1" ;;
        "trading_engineer") echo "multiagent:0.2" ;;
        "risk_engineer") echo "multiagent:0.3" ;;
        "data_engineer") echo "multiagent:0.4" ;;
        "qa_engineer") echo "multiagent:0.5" ;;
        "boss1") get_agent_target "tech_lead" ;;
        "worker1") get_agent_target "analysis_engineer" ;;
        "worker2") get_agent_target "trading_engineer" ;;
        "worker3") get_agent_target "risk_engineer" ;;
        *) echo "" ;;
    esac
}

show_usage() {
    cat << EOF
🤖 TradeFlow Agent間メッセージ送信

使用方法:
  $0 [エージェント名] [メッセージ]
  $0 --list

利用可能エージェント:
  president          - Product Owner / Project Manager
  tech_lead          - Tech Lead / Architecture Lead
  analysis_engineer  - 分析エンジン担当（4つの分析システム）
  trading_engineer   - 取引システム担当（17ファイル取引システム）
  risk_engineer      - リスク管理担当（需給リスク分析）
  data_engineer      - データ処理担当（50並列データ取得）

使用例:
  $0 president "あなたはpresidentです。指示書に従って"
  $0 tech_lead "TradeFlow開発開始 - システム設計確認とTDD実践指導を開始"
  $0 analysis_engineer "あなたはanalysis_engineerです。4つの分析システムTDD実装を開始"
  $0 trading_engineer "あなたはtrading_engineerです。17ファイル取引システムTDD実装を開始"
EOF
}

# エージェント一覧表示
show_agents() {
    echo "📋 TradeFlow専門チーム構成:"
    echo "============================================"

    # presidentセッション確認
    if tmux has-session -t president 2>/dev/null; then
        echo "  president          → president           (Product Owner / Project Manager)"
    else
        echo "  president          → [未起動]            (Product Owner / Project Manager)"
    fi

    # multiagentセッション確認
    if tmux has-session -t multiagent 2>/dev/null; then
        local tech_lead_target=$(get_agent_target "tech_lead")
        local analysis_target=$(get_agent_target "analysis_engineer")
        local trading_target=$(get_agent_target "trading_engineer")
        local risk_target=$(get_agent_target "risk_engineer")
        local data_target=$(get_agent_target "data_engineer")

        echo "  tech_lead          → ${tech_lead_target:-[エラー]}      (Tech Lead / Architecture Lead)"
        echo "  analysis_engineer  → ${analysis_target:-[エラー]}      (分析エンジン担当)"
        echo "  trading_engineer   → ${trading_target:-[エラー]}      (取引システム担当)"
        echo "  risk_engineer      → ${risk_target:-[エラー]}      (リスク管理担当)"
        echo "  data_engineer      → ${data_target:-[エラー]}      (データ処理担当)"
    else
        echo "  tech_lead          → [未起動]            (Tech Lead / Architecture Lead)"
        echo "  analysis_engineer  → [未起動]            (分析エンジン担当)"
        echo "  trading_engineer   → [未起動]            (取引システム担当)"
        echo "  risk_engineer      → [未起動]            (リスク管理担当)"
        echo "  data_engineer      → [未起動]            (データ処理担当)"
    fi
    
    echo ""
    echo "💡 利益目標: 日次5,000円以上、勝率65%以上、プロフィットファクター1.5以上"
}

# ログ記録
log_send() {
    local agent="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    mkdir -p logs
    echo "[$timestamp] $agent: SENT - \"$message\"" >> logs/send_log.txt
}

# メッセージ送信
send_message() {
    local target="$1"
    local message="$2"
    
    echo "📤 送信中: $target ← '$message'"
    
    # Claude Codeのプロンプトを一度クリア
    tmux send-keys -t "$target" C-c
    sleep 0.3
    
    # メッセージ送信
    tmux send-keys -t "$target" "$message"
    sleep 0.1
    
    # エンター押下
    tmux send-keys -t "$target" C-m
    sleep 0.5
}

# ターゲット存在確認
check_target() {
    local target="$1"
    local session_name="${target%%:*}"
    
    if ! tmux has-session -t "$session_name" 2>/dev/null; then
        echo "❌ セッション '$session_name' が見つかりません"
        return 1
    fi
    
    return 0
}

# メイン処理
main() {
    if [[ $# -eq 0 ]]; then
        show_usage
        exit 1
    fi
    
    # --listオプション
    if [[ "$1" == "--list" ]]; then
        show_agents
        exit 0
    fi
    
    if [[ $# -lt 2 ]]; then
        show_usage
        exit 1
    fi
    
    local agent_name="$1"
    local message="$2"
    
    # エージェントターゲット取得
    local target
    target=$(get_agent_target "$agent_name")
    
    if [[ -z "$target" ]]; then
        echo "❌ エラー: 不明なエージェント '$agent_name'"
        echo "利用可能エージェント: $0 --list"
        exit 1
    fi
    
    # ターゲット確認
    if ! check_target "$target"; then
        exit 1
    fi
    
    # メッセージ送信
    send_message "$target" "$message"
    
    # ログ記録
    log_send "$agent_name" "$message"
    
    echo "✅ 送信完了: $agent_name に '$message'"
    
    return 0
}

main "$@" 