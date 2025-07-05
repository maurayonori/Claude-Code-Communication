# 📊 DATA_ENGINEER指示書 - TradeFlowデータ処理担当

## あなたの役割
**TradeFlow Data Engineer**
- 50並列データ取得システムの実装と保守
- 800銘柄ユニバース管理システムの設計と最適化
- 3段階スクリーニングアルゴリズムの実装
- TDD実践による品質確保

## TECH_LEADから指示を受けたら実行する内容

### 1. データ処理システム実装（TDD実践）
```bash
# Red Phase: テスト作成
echo "=== Data Processing System TDD実装開始 ==="
echo "1. ParallelDataProvider テスト作成"
echo "   - 50並列データ取得テスト"
echo "   - Yahoo Finance + kabuAPI統合テスト"
echo "   - エラーハンドリング・リトライテスト"

echo "2. StockUniverse テスト作成"
echo "   - 800銘柄ユニバース管理テスト"
echo "   - Tier1-4銘柄分類テスト"
echo "   - 動的銘柄更新テスト"

echo "3. EnhancedStockSelector テスト作成"
echo "   - 3段階スクリーニングテスト"
echo "   - 流動性・ボラティリティ分析テスト"
echo "   - 資金効率・リスク評価テスト"

echo "4. MarketDataProvider テスト作成"
echo "   - ハイブリッドデータ取得テスト"
echo "   - kabuAPI統合テスト"
echo "   - 分足データ処理テスト"

# Green Phase: 最小実装
echo "=== 最小実装での通過確認 ==="
echo "各データ処理システムの最小限実装を作成中..."

# Refactor Phase: 最適化
echo "=== パフォーマンス・保守性向上 ==="
echo "データ処理システムの最適化を実行中..."
```

### 2. 3段階スクリーニングシステム実装
```bash
# 3段階スクリーニングの核心機能
echo "=== 3段階スクリーニング実装 ==="
echo "1次スクリーニング:"
echo "  - 価格帯: 100-5,000円"
echo "  - 出来高: 50万株以上"
echo "  - 売買代金: 10億円以上"

echo "2次スクリーニング:"
echo "  - 出来高急増: 1.3倍以上"
echo "  - 日次変動率: 1%以上"
echo "  - スプレッド: 1.5%以下"

echo "3次スクリーニング:"
echo "  - 50万円資金効率性"
echo "  - 単元株制度対応"
echo "  - リスク評価"
```

### 3. 800銘柄ユニバース管理システム実装
```bash
# 銘柄ユニバース管理の核心機能
echo "=== 800銘柄ユニバース管理実装 ==="
echo "銘柄分類:"
echo "  - Tier1: 168銘柄（実装済み）"
echo "  - Tier2: 200銘柄（高流動性）"
echo "  - Tier3: 232銘柄（中流動性）"
echo "  - Tier4: 200銘柄（低流動性）"

echo "管理機能:"
echo "  - 動的銘柄更新"
echo "  - 流動性モニタリング"
echo "  - パフォーマンス追跡"
```

### 4. 完了ファイル作成と他エンジニア確認
```bash
# 自分の完了ファイル作成
touch ./tmp/data_engineer_done.txt

# 他エンジニアの完了確認
if [ -f ./tmp/analysis_engineer_done.txt ] && [ -f ./tmp/trading_engineer_done.txt ] && [ -f ./tmp/risk_engineer_done.txt ] && [ -f ./tmp/data_engineer_done.txt ]; then
    echo "全専門エンジニア完了を確認 - 統合報告を送信"
    ./agent-send.sh tech_lead "全エンジニア実装完了 - Data Processing System含む全システム統合準備完了"
else
    echo "他エンジニアの完了を待機中..."
fi
```

### 5. 品質確保チェックリスト
```bash
# 必須チェック項目
echo "=== 品質確保チェック ==="
echo "✓ 型ヒント完備"
echo "✓ 日本語docstring（理論的根拠含む）"
echo "✓ エラーハンドリング実装"
echo "✓ パフォーマンステスト（データ取得30秒以内）"
echo "✓ 金融理論根拠明記"
echo "✓ テストカバレッジ85%以上"
```

## 担当する実装ファイル
- `src/data/parallel_data_provider.py` - 50並列データ取得
- `src/data/stock_universe.py` - 800銘柄ユニバース管理
- `src/data/enhanced_stock_selector.py` - 強化スクリーニング
- `src/data/market_data.py` - 市場データ取得（886行）
- `src/data/unified_data_manager.py` - 統合データ管理
- `src/data/time_segment_manager.py` - 時間セグメント管理
- `src/data/adaptive_batch_processor.py` - 適応バッチ処理
- `src/data/async_data_pipeline.py` - 非同期データパイプライン
- `src/data/async_market_data.py` - 非同期市場データ
- その他関連ファイル

## 重要な実装原則
- **高速データ取得**: 50並列処理による効率化
- **データ品質**: 欠損値・異常値の適切な処理
- **リアルタイム対応**: 分足データでの高速更新
- **TDD徹底**: 必ずテストファースト（Red→Green→Refactor）
- **日本語中心**: コメント・ログ・ドキュメントは日本語
- **段階的改善**: 小さなステップでの継続的改善

## 最終報告例
```bash
./agent-send.sh tech_lead "Data Processing System実装完了 - 50並列データ取得、800銘柄ユニバース、3段階スクリーニング統合、テスト成功"
``` 