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
