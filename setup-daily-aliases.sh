#!/bin/bash

# TradeFlow 日常運用エイリアス設定

CLAUDE_DIR="/Users/yono/Build/TradeFlow/scripts/Claude-Code-Communication"

echo "🔧 TradeFlow 日常運用エイリアス設定"
echo "================================="

# .zshrcにエイリアスを追加
cat >> ~/.zshrc << EOF

# ===== TradeFlow 日常運用エイリアス =====
alias tf-daily="$CLAUDE_DIR/optimized-daily-workflow.sh"
alias tf-status="cat $CLAUDE_DIR/.task_state.json | jq ."
alias tf-progress="$CLAUDE_DIR/lightweight-update-progress.sh"
alias tf-restart="$CLAUDE_DIR/auto-restart-cycle.sh"
alias tf-load="top -l 1 -n 0 | grep 'CPU usage'"
alias tf-logs="ls -la ~/ObsidianVault/claude_logs/ | tail -10"
alias tf-attach-president="tmux attach-session -t president"
alias tf-attach-multiagent="tmux attach-session -t multiagent"
alias tf-kill-all="tmux kill-session -t president 2>/dev/null || true; tmux kill-session -t multiagent 2>/dev/null || true"

EOF

echo "✅ エイリアス設定完了"
echo ""
echo "🎯 使用可能なコマンド:"
echo "  tf-daily           # 日常運用開始"
echo "  tf-status          # タスク状態確認"
echo "  tf-progress <数値> # 進捗更新"
echo "  tf-restart         # 手動再起動"
echo "  tf-load            # システム負荷確認"
echo "  tf-logs            # 最新ログ確認"
echo "  tf-attach-president    # President画面に接続"
echo "  tf-attach-multiagent   # MultiAgent画面に接続"
echo "  tf-kill-all        # 全セッション終了"
echo ""
echo "💡 設定を有効化するには:"
echo "  source ~/.zshrc"
echo ""
echo "🚀 日常運用を開始するには:"
echo "  tf-daily" 