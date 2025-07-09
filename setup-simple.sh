#!/bin/bash

# TradeFlow Multi-Agent Communication Setup Script (Simple Version)
# このスクリプトはTradeFlowプロジェクトの複数エージェント開発環境を構築します

# ANSI カラーコード
RED='\033[1;31m'
GREEN='\033[1;32m'
BLUE='\033[1;34m'
CYAN='\033[1;36m'
NC='\033[0m' # No Color

# ロギング関数
log_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# プロジェクトルート
PROJECT_ROOT="/Users/yono/Build/TradeFlow"
CLAUDE_COMM_DIR="$PROJECT_ROOT/scripts/Claude-Code-Communication"

# ログディレクトリを作成
mkdir -p ~/ObsidianVault/claude_logs

echo "🤖 TradeFlow Multi-Agent Communication 環境構築"
echo "==============================================="
echo ""

# 既存セッションのクリーンアップ
log_info "🧹 既存セッションクリーンアップ中..."
tmux kill-session -t multiagent 2>/dev/null && log_info "multiagentセッション削除完了"
tmux kill-session -t president 2>/dev/null && log_info "presidentセッション削除完了"
rm -f "$CLAUDE_COMM_DIR/tmp/"*.txt 2>/dev/null
log_success "✅ クリーンアップ完了"
echo ""

# multiagentセッション作成
log_info "📺 multiagentセッション作成中 (5ペイン)..."
tmux new-session -d -s multiagent -n agents -c "$PROJECT_ROOT"

# 5ペインレイアウト作成
tmux split-window -t multiagent:agents -v
tmux select-pane -t multiagent:agents -D
tmux split-window -t multiagent:agents -h
tmux split-window -t multiagent:agents -h
tmux select-pane -t multiagent:agents -U
tmux split-window -t multiagent:agents -h
tmux select-layout -t multiagent:agents tiled

# ペインIDを取得
PANE_IDS=($(tmux list-panes -t multiagent:agents -F "#{pane_id}" | sort))
ROLES=("tech_lead" "analysis_engineer" "trading_engineer" "risk_engineer" "data_engineer")

# 各ペインの設定とClaude起動
for i in {0..4}; do
    pane_id="${PANE_IDS[$i]}"
    role="${ROLES[$i]}"
    
    # ペインタイトル設定
    tmux select-pane -t "$pane_id" -T "$role"
    
    # 初期設定とClaude起動
    tmux send-keys -t "$pane_id" "cd $PROJECT_ROOT" C-m
    tmux send-keys -t "$pane_id" "export PS1='($role) \\w\\$ '" C-m
    tmux send-keys -t "$pane_id" "clear" C-m
    tmux send-keys -t "$pane_id" "echo '=== $role エージェント ==='" C-m
    tmux send-keys -t "$pane_id" "echo ''" C-m
    
    # Claudeを直接起動（インタラクティブモード）
    tmux send-keys -t "$pane_id" "claude --dangerously-skip-permissions" C-m
    sleep 0.3
done

log_success "✅ multiagentセッション作成完了"
echo ""

# presidentセッション作成
log_info "👑 presidentセッション作成中..."
tmux new-session -d -s president -n zsh -c "$PROJECT_ROOT"
tmux send-keys -t president:0 "cd $PROJECT_ROOT" C-m
tmux send-keys -t president:0 "export PS1='(PRESIDENT) \\w\\$ '" C-m
tmux send-keys -t president:0 "clear" C-m
tmux send-keys -t president:0 "echo '=== PRESIDENT セッション ==='" C-m
tmux send-keys -t president:0 "echo 'Product Owner / Project Manager'" C-m
tmux send-keys -t president:0 "echo '============================='" C-m
tmux send-keys -t president:0 "echo ''" C-m

# PRESIDENTでもClaude起動
tmux send-keys -t president:0 "claude --dangerously-skip-permissions" C-m

log_success "✅ presidentセッション作成完了"
echo ""

# セットアップ完了メッセージ
echo "📊 セットアップ結果:"
echo "==================="
echo ""
echo "✅ multiagentセッション（5ペイン）:"
for i in {0..4}; do
    echo "   - ${ROLES[$i]}"
done
echo ""
echo "✅ presidentセッション（1ペイン）:"
echo "   - PRESIDENT (Product Owner)"
echo ""
log_success "🎉 TradeFlow環境セットアップ完了！"
echo ""
echo "Claude Codeが全てのペインで起動しています。"
echo "Alacrittyウィンドウに自動的に接続されます..."