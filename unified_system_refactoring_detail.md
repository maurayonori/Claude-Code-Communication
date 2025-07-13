# unified_system.py 分割実装詳細計画

## 現状分析結果
- **ファイルサイズ**: 2,437行
- **メソッド数**: 58個
- **主要機能**:
  1. システム統合管理
  2. 取引セッション実行
  3. ポジション管理
  4. エントリー判定
  5. マーケットトレンド分析
  6. 決済管理
  7. パフォーマンス集計
  8. CSV記録

## 分割方針

### 1. マーケットトレンド分析の分離（約400行削減）
**対象メソッド**:
- `_analyze_market_trend()` 
- `_determine_trend_direction()`
- `_calculate_trend_strength()`
- `_analyze_volume_signal()`
- `_make_market_decision()`
- `_neutral_trend_signal()`

**移動先**: 既存の `market_analyzer.py` または新規 `market_trend_engine.py`

### 2. スコア計算ロジックの分離（約300行削減）
**対象メソッド**:
- `_calculate_market_score()`
- `_calculate_dynamic_score_threshold()`
- `_calculate_sector_price_bonus()`
- `_calculate_time_based_bonus()`
- `_calculate_time_threshold_adjustment()`

**移動先**: 新規 `score_calculator.py` または既存の scorer モジュールへ統合

### 3. CSV/レポート機能の分離（約200行削減）
**対象メソッド**:
- `_save_trading_session_to_csv()`
- `_update_monthly_summary_csv()`
- `get_performance_summary()`
- `get_trading_discipline_status()`
- `get_trading_violations_summary()`

**移動先**: 新規 `trading_reporter.py`

### 4. 評価・分析機能の分離（約300行削減）
**対象メソッド**:
- `_perform_objective_evaluation()`
- `_should_perform_evaluation()`
- `_get_stock_data_for_evaluation()`
- `_create_stock_data_from_realtime()`
- `_log_objective_evaluation()`
- `_handle_objective_evaluation_results()`

**移動先**: 新規 `position_evaluator.py`

### 5. 重複コードの削除（約300行削減）
- ロング/ショートポジションの開設ロジックの統合
- 動的ターゲット計算の統一化
- エラーハンドリングの共通化

## 実装手順

### Step 1: インターフェース定義
```python
# interfaces/trading_interfaces.py
from abc import ABC, abstractmethod

class MarketAnalyzerInterface(ABC):
    @abstractmethod
    def analyze_trend(self, symbol: str, current_date: str = None) -> TrendSignal:
        pass

class ScoreCalculatorInterface(ABC):
    @abstractmethod
    def calculate_entry_score(self, stock_data, trend_signal, market_decision) -> float:
        pass

class TradingReporterInterface(ABC):
    @abstractmethod
    def save_session_results(self, date: str, results: Dict) -> None:
        pass
```

### Step 2: 機能の抽出と移動
1. 各機能グループを新モジュールへ移動
2. UnifiedTradingSystem内では、これらのモジュールを組み合わせて使用
3. 依存性注入パターンで結合度を下げる

### Step 3: UnifiedTradingSystemのスリム化
```python
class UnifiedTradingSystem:
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.logger = config_manager.get_logger("unified_trading")
        
        # 分離したコンポーネントの初期化
        self.market_analyzer = MarketTrendEngine(config_manager)
        self.score_calculator = ScoreCalculator(config_manager)
        self.trading_reporter = TradingReporter(config_manager)
        self.position_evaluator = PositionEvaluator(config_manager)
        
        # 既存のコンポーネント
        self.position_manager = PositionManager(config_manager)
        self.risk_manager = EnhancedRiskManager(config_manager)
        # ...
```

## 期待される効果
- **コード削減**: 約1,500行（重複削除含む）
- **保守性向上**: 機能ごとに独立したモジュール
- **テスタビリティ向上**: 各機能を個別にテスト可能
- **再利用性向上**: 他のシステムからも利用可能

## リスクと対策
1. **依存関係の複雑化**
   - 明確なインターフェース定義で対処
   - 依存性注入パターンの活用

2. **パフォーマンス低下**
   - プロファイリングで検証
   - 必要に応じてキャッシュ実装

3. **既存機能への影響**
   - 段階的な移行
   - 包括的なテストカバレッジ

## 検証計画
1. 単体テストの作成・更新
2. 統合テストでの動作確認
3. パフォーマンステスト
4. main.pyでのエンドツーエンドテスト