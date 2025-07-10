#!/bin/bash

# TradeFlow Alacritty最適化セットアップ
# シンプルで効率的なマルチエージェント環境

set -e

# 色付きログ
log_info() { echo -e "\033[1;36m[INFO]\033[0m $1"; }
log_success() { echo -e "\033[1;32m[SUCCESS]\033[0m $1"; }
log_error() { echo -e "\033[1;31m[ERROR]\033[0m $1"; }

PROJECT_ROOT="/Users/yono/Build/TradeFlow"
CLAUDE_DIR="$PROJECT_ROOT/scripts/Claude-Code-Communication"

echo "🚀 TradeFlow Alacritty最適化セットアップ"
echo "========================================"
echo ""

# 既存セッションクリーンアップ
log_info "🧹 既存セッションクリーンアップ..."
tmux kill-session -t tradeflow 2>/dev/null || true
tmux kill-session -t president 2>/dev/null || true
tmux kill-session -t multiagent 2>/dev/null || true

# メインセッション作成（2ペイン構成）
log_info "📺 メインセッション作成中..."
tmux new-session -d -s tradeflow -n main -c "$CLAUDE_DIR"

# 縦分割（左：president、右：multiagent）
tmux split-window -t tradeflow:main -h -c "$CLAUDE_DIR"

# 右側をさらに分割（上：tech_lead、下：active_engineer）
tmux select-pane -t tradeflow:main -R
tmux split-window -t tradeflow:main -v -c "$CLAUDE_DIR"

# ペインタイトル設定
tmux select-pane -t tradeflow:main.0 -T "PRESIDENT"
tmux select-pane -t tradeflow:main.1 -T "TECH_LEAD"
tmux select-pane -t tradeflow:main.2 -T "ACTIVE_ENGINEER"

# 各ペインの初期設定
PANES=("PRESIDENT" "TECH_LEAD" "ACTIVE_ENGINEER")
for i in {0..2}; do
    pane_id="tradeflow:main.$i"
    role="${PANES[$i]}"
    
    tmux send-keys -t "$pane_id" "cd $CLAUDE_DIR" C-m
    tmux send-keys -t "$pane_id" "export PS1='($role) \\w\\$ '" C-m
    tmux send-keys -t "$pane_id" "clear" C-m
    tmux send-keys -t "$pane_id" "echo '=== $role ==='" C-m
    
    case $role in
        "PRESIDENT")
            tmux send-keys -t "$pane_id" "echo 'Product Owner / Project Manager'" C-m
            ;;
        "TECH_LEAD")
            tmux send-keys -t "$pane_id" "echo 'Architecture Lead / System Design'" C-m
            ;;
        "ACTIVE_ENGINEER")
            tmux send-keys -t "$pane_id" "echo 'Current Task: Ready for Assignment'" C-m
            ;;
    esac
    
    tmux send-keys -t "$pane_id" "echo ''" C-m
done

log_success "✅ メインセッション作成完了"
echo ""

# エンジニア切り替え用のヘルパー関数作成
log_info "🔧 エンジニア切り替えヘルパー作成中..."
cat > "$CLAUDE_DIR/switch-engineer.sh" << 'EOF'
#!/bin/bash

ENGINEERS=("analysis_engineer" "trading_engineer" "risk_engineer" "data_engineer" "qa_engineer")
CURRENT_FILE="$HOME/.tradeflow_current_engineer"

if [ $# -eq 0 ]; then
    echo "利用可能なエンジニア:"
    for i in "${!ENGINEERS[@]}"; do
        echo "  $((i+1)). ${ENGINEERS[$i]}"
    done
    echo ""
    echo "使用方法: $0 <番号> または $0 <エンジニア名>"
    exit 1
fi

if [[ $1 =~ ^[0-9]+$ ]] && [ $1 -ge 1 ] && [ $1 -le ${#ENGINEERS[@]} ]; then
    ENGINEER="${ENGINEERS[$(($ 1-1))]}"
else
    ENGINEER="$1"
fi

# 現在のエンジニアを記録
echo "$ENGINEER" > "$CURRENT_FILE"

# ペインタイトル更新
tmux select-pane -t tradeflow:main.2 -T "ACTIVE: $ENGINEER"

# プロンプト更新
tmux send-keys -t tradeflow:main.2 "export PS1='($ENGINEER) \\w\\$ '" C-m
tmux send-keys -t tradeflow:main.2 "clear" C-m
tmux send-keys -t tradeflow:main.2 "echo '=== $ENGINEER ==='" C-m

case $ENGINEER in
    "analysis_engineer")
        tmux send-keys -t tradeflow:main.2 "echo '4つの分析エンジン担当'" C-m
        ;;
    "trading_engineer")
        tmux send-keys -t tradeflow:main.2 "echo '17ファイル取引システム担当'" C-m
        ;;
    "risk_engineer")
        tmux send-keys -t tradeflow:main.2 "echo '需給リスク分析・動的目標設定担当'" C-m
        ;;
    "data_engineer")
        tmux send-keys -t tradeflow:main.2 "echo '50並列データ取得・800銘柄管理担当'" C-m
        ;;
    "qa_engineer")
        tmux send-keys -t tradeflow:main.2 "echo '品質保証・テスト・デバッグ担当'" C-m
        ;;
esac

tmux send-keys -t tradeflow:main.2 "echo ''" C-m
echo "✅ エンジニア切り替え完了: $ENGINEER"
EOF

chmod +x "$CLAUDE_DIR/switch-engineer.sh"

# Alacritty起動スクリプト作成
log_info "🖥️ Alacritty起動スクリプト作成中..."
cat > "$CLAUDE_DIR/start-alacritty.sh" << 'EOF'
#!/bin/bash

CLAUDE_DIR="/Users/yono/Build/TradeFlow/scripts/Claude-Code-Communication"

# メインウィンドウ（大きめ）
alacritty --working-directory "$CLAUDE_DIR" \
          --position 100 100 \
          --dimensions 160 50 \
          --command tmux attach-session -t tradeflow \; \
          select-pane -t tradeflow:main.0 &

# 監視ウィンドウ（小さめ、右上）
sleep 1
alacritty --working-directory "$CLAUDE_DIR" \
          --position 1200 100 \
          --dimensions 80 30 \
          --command tmux new-session -s monitor \; \
          send-keys "watch -n 1 'tmux list-sessions && echo && tmux list-panes -t tradeflow:main -F \"#{pane_title}: #{pane_current_command}\"'" C-m &

echo "✅ Alacrittyウィンドウ起動完了"
EOF

chmod +x "$CLAUDE_DIR/start-alacritty.sh"

# Claude起動スクリプト作成
log_info "🤖 Claude起動スクリプト作成中..."
cat > "$CLAUDE_DIR/start-claude.sh" << 'EOF'
#!/bin/bash

CLAUDE_DIR="/Users/yono/Build/TradeFlow/scripts/Claude-Code-Communication"
LOG_DIR="$HOME/ObsidianVault/claude_logs"

mkdir -p "$LOG_DIR"

# 各ペインでClaude起動
PANES=("PRESIDENT" "TECH_LEAD" "ACTIVE_ENGINEER")
for i in {0..2}; do
    pane_id="tradeflow:main.$i"
    role="${PANES[$i]}"
    
    log_file="$LOG_DIR/${role,,}_$(date +%F_%H-%M).md"
    
    tmux send-keys -t "$pane_id" "claude --dangerously-skip-permissions 2>&1 | tee $log_file" C-m
    sleep 1
done

echo "✅ Claude起動完了（全ペイン）"
EOF

chmod +x "$CLAUDE_DIR/start-claude.sh"

# 便利なエイリアス作成
log_info "⚡ エイリアス設定作成中..."
cat >> ~/.zshrc << 'EOF'

# TradeFlow Alacritty最適化エイリアス
alias tf-start="/Users/yono/Build/TradeFlow/scripts/Claude-Code-Communication/start-alacritty.sh"
alias tf-claude="/Users/yono/Build/TradeFlow/scripts/Claude-Code-Communication/start-claude.sh"
alias tf-switch="/Users/yono/Build/TradeFlow/scripts/Claude-Code-Communication/switch-engineer.sh"
alias tf-attach="tmux attach-session -t tradeflow"
alias tf-monitor="tmux attach-session -t monitor"
EOF

log_success "✅ セットアップ完了！"
echo ""
echo "🎯 使用方法:"
echo "  1. tf-start     # Alacrittyウィンドウ起動"
echo "  2. tf-claude    # Claude起動（全ペイン）"
echo "  3. tf-switch 1  # エンジニア切り替え"
echo "  4. tf-attach    # セッション再接続"
echo ""
echo "📋 ペイン構成:"
echo "  左：PRESIDENT（指示・管理）"
echo "  右上：TECH_LEAD（設計・レビュー）"
echo "  右下：ACTIVE_ENGINEER（実装）"
echo ""
echo "🔄 エンジニア切り替え:"
echo "  1. analysis_engineer（分析）"
echo "  2. trading_engineer（取引）"
echo "  3. risk_engineer（リスク）"
echo "  4. data_engineer（データ）"
echo "  5. qa_engineer（品質保証）"
echo ""
echo "💡 利益目標: 日次5,000円以上、勝率65%以上" 