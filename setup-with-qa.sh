#!/bin/bash

# TradeFlow Multi-Agent Communication Setup Script (With QA Engineer)
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

# Claude起動用のディレクトリ（各役割の指示書がある場所）
CLAUDE_START_DIR="$CLAUDE_COMM_DIR"

# ログディレクトリを作成
mkdir -p ~/ObsidianVault/claude_logs

echo "🤖 TradeFlow Multi-Agent Communication 環境構築 (QA Engineer追加版)"
echo "================================================================"
echo ""

# 既存セッションのクリーンアップ
log_info "🧹 既存セッションクリーンアップ中..."
tmux kill-session -t multiagent 2>/dev/null && log_info "multiagentセッション削除完了"
tmux kill-session -t president 2>/dev/null && log_info "presidentセッション削除完了"
rm -f "$CLAUDE_COMM_DIR/tmp/"*.txt 2>/dev/null
log_success "✅ クリーンアップ完了"
echo ""

# multiagentセッション作成
log_info "📺 multiagentセッション作成中 (6ペイン)..."
tmux new-session -d -s multiagent -n agents -c "$CLAUDE_START_DIR"

# 6ペインレイアウト作成（3x2グリッド）
tmux split-window -t multiagent:agents -v  # 縦に分割（上下2つ）
tmux select-pane -t multiagent:agents -U  # 上のペインを選択
tmux split-window -t multiagent:agents -h  # 横に分割（上段2つ）
tmux split-window -t multiagent:agents -h  # さらに横に分割（上段3つ）
tmux select-pane -t multiagent:agents -D  # 下のペインを選択
tmux split-window -t multiagent:agents -h  # 横に分割（下段2つ）
tmux split-window -t multiagent:agents -h  # さらに横に分割（下段3つ）
tmux select-layout -t multiagent:agents tiled  # レイアウト調整

# ペインIDを取得
PANE_IDS=($(tmux list-panes -t multiagent:agents -F "#{pane_id}" | sort))
ROLES=("tech_lead" "analysis_engineer" "trading_engineer" "risk_engineer" "data_engineer" "qa_engineer")

# 各ペインの設定とClaude起動
for i in {0..5}; do
    pane_id="${PANE_IDS[$i]}"
    role="${ROLES[$i]}"
    
    # ペインタイトル設定
    tmux select-pane -t "$pane_id" -T "$role"
    
    # 初期設定とClaude起動
    tmux send-keys -t "$pane_id" "cd $CLAUDE_START_DIR" C-m
    tmux send-keys -t "$pane_id" "export PS1='($role) \\w\\$ '" C-m
    tmux send-keys -t "$pane_id" "clear" C-m
    tmux send-keys -t "$pane_id" "echo '=== $role エージェント ==='" C-m
    
    # 役割固有のメッセージ
    case $role in
        "tech_lead")
            tmux send-keys -t "$pane_id" "echo 'Tech Lead / Architecture Lead'" C-m
            ;;
        "analysis_engineer")
            tmux send-keys -t "$pane_id" "echo '4つの分析エンジン担当'" C-m
            ;;
        "trading_engineer")
            tmux send-keys -t "$pane_id" "echo '17ファイル取引システム担当'" C-m
            ;;
        "risk_engineer")
            tmux send-keys -t "$pane_id" "echo '需給リスク分析・動的目標設定担当'" C-m
            ;;
        "data_engineer")
            tmux send-keys -t "$pane_id" "echo '50並列データ取得・800銘柄管理担当'" C-m
            ;;
        "qa_engineer")
            tmux send-keys -t "$pane_id" "echo '品質保証・テスト・デバッグ担当'" C-m
            ;;
    esac
    
    tmux send-keys -t "$pane_id" "echo ''" C-m
    
    # Claudeを直接起動（インタラクティブモード）
    tmux send-keys -t "$pane_id" "claude --dangerously-skip-permissions" C-m
    sleep 0.3
done

log_success "✅ multiagentセッション作成完了"
echo ""

# presidentセッション作成
log_info "👑 presidentセッション作成中..."
tmux new-session -d -s president -n zsh -c "$CLAUDE_START_DIR"
tmux send-keys -t president:0 "cd $CLAUDE_START_DIR" C-m
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
echo "✅ multiagentセッション（6ペイン）:"
for i in {0..5}; do
    echo "   - ${ROLES[$i]}"
done
echo ""
echo "✅ presidentセッション（1ペイン）:"
echo "   - PRESIDENT (Product Owner)"
echo ""
log_success "🎉 TradeFlow環境セットアップ完了！"
echo ""
echo "🎯 新機能: QA Engineer追加"
echo "   - 包括的な品質保証とテスト"
echo "   - 品質ゲート管理（カバレッジ85%以上）"
echo "   - 利益目標達成可能性検証"
echo "   - 自動テストスイート実行"
echo ""
echo "📋 開発フロー:"
echo "   PRESIDENT → tech_lead → 5専門エンジニア → qa_engineer → tech_lead → PRESIDENT"
echo ""
echo "💡 利益目標: 日次5,000円以上、勝率65%以上、プロフィットファクター1.5以上"
echo "🔍 品質目標: テストカバレッジ85%以上、テスト成功率100%"
echo ""
echo "Claude Codeが全てのペインで起動しています。"
echo "Alacrittyウィンドウに自動的に接続されます..."