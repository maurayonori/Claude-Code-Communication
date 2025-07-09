#!/bin/bash

# 🚀 TradeFlow Multi-Agent Communication 環境構築
# 専門チーム: tech_lead + 4専門エンジニア

set -e  # エラー時に停止

# 色付きログ関数
log_info() {
    echo -e "\033[1;32m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[1;34m[SUCCESS]\033[0m $1"
}

echo "🤖 TradeFlow Multi-Agent Communication 環境構築"
echo "==============================================="
echo ""

# STEP 1: 既存セッションクリーンアップ
log_info "🧹 既存セッションクリーンアップ開始..."

tmux kill-session -t multiagent 2>/dev/null && log_info "multiagentセッション削除完了" || log_info "multiagentセッションは存在しませんでした"
tmux kill-session -t president 2>/dev/null && log_info "presidentセッション削除完了" || log_info "presidentセッションは存在しませんでした"

# 完了ファイルクリア
mkdir -p ./tmp
rm -f ./tmp/*_engineer_done.txt 2>/dev/null && log_info "既存の完了ファイルをクリア" || log_info "完了ファイルは存在しませんでした"

log_success "✅ クリーンアップ完了"
echo ""

# STEP 2: multiagentセッション作成（5ペイン：tech_lead + 4専門エンジニア）
log_info "📺 multiagentセッション作成開始 (5ペイン)..."

# セッション作成
log_info "セッション作成中..."
tmux new-session -d -s multiagent -n "agents"

# セッション作成の確認
if ! tmux has-session -t multiagent 2>/dev/null; then
    echo "❌ エラー: multiagentセッションの作成に失敗しました"
    exit 1
fi

log_info "セッション作成成功"

# 5ペインレイアウト作成（改良版：縦分割メインで横分割組み合わせ）
log_info "5ペインレイアウト作成中..."

# 方法1: 縦に2つのペインを作成
log_info "縦分割1回目実行中..."
tmux split-window -v -t "multiagent:agents"

# 方法2: 下のペインを3つに分割
log_info "下段を3つに分割中..."
tmux select-pane -t "multiagent:agents" -D  # 下のペインを選択
tmux split-window -h  # 横に分割（2つになる）
tmux split-window -h  # さらに横に分割（3つになる）

# 方法3: 上のペインを2つに分割
log_info "上段を2つに分割中..."
tmux select-pane -t "multiagent:agents" -U  # 上のペインを選択
tmux split-window -h  # 横に分割（2つになる）

# レイアウトを均等に調整
log_info "レイアウト調整中..."
tmux select-layout -t "multiagent:agents" tiled

# ペインの配置確認
log_info "ペイン配置確認中..."
PANE_COUNT=$(tmux list-panes -t "multiagent:agents" | wc -l)
log_info "作成されたペイン数: $PANE_COUNT"

if [ "$PANE_COUNT" -ne 5 ]; then
    echo "❌ エラー: 期待されるペイン数(5)と異なります: $PANE_COUNT"
    exit 1
fi

# ペインの物理的な配置を取得
log_info "ペイン番号取得中..."
PANE_IDS=($(tmux list-panes -t "multiagent:agents" -F "#{pane_id}" | sort))

log_info "検出されたペイン: ${PANE_IDS[*]}"

# ペインタイトル設定とセットアップ
log_info "ペインタイトル設定中..."
PANE_TITLES=("tech_lead" "analysis_engineer" "trading_engineer" "risk_engineer" "data_engineer")

for i in {0..4}; do
    PANE_ID="${PANE_IDS[$i]}"
    TITLE="${PANE_TITLES[$i]}"
    
    log_info "設定中: ${TITLE} (${PANE_ID})"
    
    # ペインタイトル設定
    tmux select-pane -t "$PANE_ID" -T "$TITLE"
    
    # 作業ディレクトリ設定
    tmux send-keys -t "$PANE_ID" "cd $(pwd)" C-m
    
    # カラープロンプト設定（文字化け対策版）
    if [ $i -eq 0 ]; then
        # tech_lead: 赤色（シンプル版）
        tmux send-keys -t "$PANE_ID" "PS1='(tech_lead) \w\$ '" C-m
    else
        # engineers: 青色（シンプル版）
        tmux send-keys -t "$PANE_ID" "PS1='(${TITLE}) \w\$ '" C-m
    fi
    
    # ウェルカムメッセージ
    case $i in
        0) tmux send-keys -t "$PANE_ID" "echo '=== Tech Lead / Architecture Lead ==='" C-m ;;
        1) tmux send-keys -t "$PANE_ID" "echo '=== Analysis Engineer (4つの分析システム) ==='" C-m ;;
        2) tmux send-keys -t "$PANE_ID" "echo '=== Trading Engineer (17ファイル取引システム) ==='" C-m ;;
        3) tmux send-keys -t "$PANE_ID" "echo '=== Risk Engineer (需給リスク分析) ==='" C-m ;;
        4) tmux send-keys -t "$PANE_ID" "echo '=== Data Engineer (50並列データ取得) ==='" C-m ;;
    esac
done

log_success "✅ multiagentセッション作成完了"
echo ""

# STEP 3: presidentセッション作成（1ペイン）
log_info "👑 presidentセッション作成開始..."

tmux new-session -d -s president
tmux send-keys -t president "cd $(pwd)" C-m
tmux send-keys -t president "PS1='(PRESIDENT) \w\$ '" C-m
tmux send-keys -t president "echo '=== PRESIDENT セッション ==='" C-m
tmux send-keys -t president "echo 'Product Owner / Project Manager'" C-m
tmux send-keys -t president "echo '============================='" C-m

log_success "✅ presidentセッション作成完了"
echo ""

# STEP 4: 環境確認・表示
log_info "🔍 環境確認中..."

echo ""
echo "📊 セットアップ結果:"
echo "==================="

# tmuxセッション確認
echo "📺 Tmux Sessions:"
tmux list-sessions
echo ""

# ペイン構成表示
echo "📋 ペイン構成:"
echo "  multiagentセッション（5ペイン）:"
tmux list-panes -t "multiagent:agents" -F "    Pane #{pane_id}: #{pane_title}"
echo ""
echo "  presidentセッション（1ペイン）:"
echo "    Pane: PRESIDENT (Product Owner / Project Manager)"

echo ""
log_success "🎉 TradeFlow環境セットアップ完了！"
echo ""
echo "📋 次のステップ:"
echo "  1. 🔗 セッションアタッチ:"
echo "     tmux attach-session -t multiagent   # 専門エンジニアチーム確認"
echo "     tmux attach-session -t president    # Product Owner確認"
echo ""
echo "  2. 🤖 Claude Code起動:"
echo "     # 手順1: President認証"
echo "     tmux send-keys -t president 'claude' C-m"
echo "     #実行時の許可を不要にする場合
echo "     tmux send-keys -t president 'claude --dangerously-skip-permissions' C-m”
echo "     # 手順2: 認証後、multiagent一括起動"
echo "     # 各ペインのIDを使用してclaudeを起動"
echo "     tmux list-panes -t multiagent:agents -F '#{pane_id}' | while read pane; do"
echo "         tmux send-keys -t \"\$pane\" 'claude --dangerously-skip-permissions' C-m"
echo "     done"
echo ""
echo "  3. 📜 指示書確認:"
echo "     PRESIDENT: instructions/president.md"
echo "     tech_lead: instructions/boss.md"
echo "     analysis_engineer: instructions/worker.md"
echo "     trading_engineer: instructions/trading_engineer.md"
echo "     risk_engineer: instructions/risk_engineer.md"
echo "     data_engineer: instructions/data_engineer.md"
echo "     システム構造: CLAUDE.md"
echo ""
echo "  4. 🎯 デモ実行: PRESIDENTに「あなたはpresidentです。指示書に従って」と入力"
echo ""
echo "💡 利益目標: 日次5,000円以上、勝率65%以上、プロフィットファクター1.5以上"

# 絶対パス指定
PROJECT_ROOT="/Users/yono/Build/TradeFlow"

# ログディレクトリを作成
mkdir -p ~/ObsidianVault/claude_logs

CLAUDE_CMDS=(
    "cd $PROJECT_ROOT && export PS1='(tech_lead) \w\$ ' && claude --dangerously-skip-permissions | tee ~/ObsidianVault/claude_logs/tech_lead_$(date +%F_%H-%M).md"
    "cd $PROJECT_ROOT && export PS1='(analysis_engineer) \w\$ ' && claude --dangerously-skip-permissions | tee ~/ObsidianVault/claude_logs/analysis_$(date +%F_%H-%M).md"
    "cd $PROJECT_ROOT && export PS1='(trading_engineer) \w\$ ' && claude --dangerously-skip-permissions | tee ~/ObsidianVault/claude_logs/trading_$(date +%F_%H-%M).md"
    "cd $PROJECT_ROOT && export PS1='(risk_engineer) \w\$ ' && claude --dangerously-skip-permissions | tee ~/ObsidianVault/claude_logs/risk_$(date +%F_%H-%M).md"
    "cd $PROJECT_ROOT && export PS1='(data_engineer) \w\$ ' && claude --dangerously-skip-permissions | tee ~/ObsidianVault/claude_logs/data_$(date +%F_%H-%M).md"
)
sleep 1
for i in {0..4}; do
    PANE_ID="${PANE_IDS[$i]}"
    case $i in
        0)
            ROLE="tech_lead" ;;
        1)
            ROLE="analysis_engineer" ;;
        2)
            ROLE="trading_engineer" ;;
        3)
            ROLE="risk_engineer" ;;
        4)
            ROLE="data_engineer" ;;
    esac
    tmux send-keys -t "$PANE_ID" "pwd" C-m
    tmux send-keys -t "$PANE_ID" "which claude" C-m
    tmux send-keys -t "$PANE_ID" "ls -la" C-m
    sleep 1
    echo "[DEBUG] Sending to $PANE_ID: cd $PROJECT_ROOT"
    tmux send-keys -t "$PANE_ID" "cd $PROJECT_ROOT" C-m
    sleep 5
    echo "[DEBUG] Sending to $PANE_ID: export PS1='($ROLE) \\w\\$ '"
    tmux send-keys -t "$PANE_ID" "export PS1='($ROLE) \\w\\$ '" C-m
    sleep 5
    # Claudeをインタラクティブモードで起動（ログ記録付き）
    CLAUDE_CMD="claude --dangerously-skip-permissions 2>&1 | tee ~/ObsidianVault/claude_logs/${ROLE}_$(date +%F_%H-%M).md"
    echo "[DEBUG] Sending to $PANE_ID: $CLAUDE_CMD"
    tmux send-keys -t "$PANE_ID" "$CLAUDE_CMD" C-m
    sleep 5
    if tmux list-panes -a | grep -q "$PANE_ID"; then
        tmux capture-pane -t "$PANE_ID" -pS -20 > "./tmp/pane_${i}_last20.txt" 2>/dev/null || echo "[DEBUG] capture-pane failed for $PANE_ID"
        echo "[DEBUG] Last 20 lines of $PANE_ID:"
        tail -n 20 "./tmp/pane_${i}_last20.txt"
    else
        echo "[DEBUG] $PANE_ID is not alive, skipping capture-pane."
    fi
done

# presidentペイン
sleep 5
# Claudeをインタラクティブモードで起動（ログ記録付き）
PRESIDENT_CMD="claude --dangerously-skip-permissions 2>&1 | tee ~/ObsidianVault/claude_logs/president_$(date +%F_%H-%M).md"
echo "[DEBUG] Sending to president:0.0: cd $PROJECT_ROOT"
tmux send-keys -t president:0.0 "cd $PROJECT_ROOT" C-m
sleep 5
echo "[DEBUG] Sending to president:0.0: export PS1='(PRESIDENT) \\w\\$ '"
tmux send-keys -t president:0.0 "export PS1='(PRESIDENT) \\w\\$ '" C-m
sleep 5
echo "[DEBUG] Sending to president:0.0: $PRESIDENT_CMD"
tmux send-keys -t president:0.0 "$PRESIDENT_CMD" C-m
sleep 5
tmux capture-pane -t president:0.0 -pS -20 > "./tmp/pane_president_last20.txt"
echo "[DEBUG] Last 20 lines of president:0.0:"
tail -n 20 "./tmp/pane_president_last20.txt"