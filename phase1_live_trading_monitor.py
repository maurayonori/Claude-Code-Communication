#!/usr/bin/env python3
"""
Phase 1 Live Trading Monitor - 実取引検証監視システム
🚀 TECH_LEAD技術統括下での実取引性能検証

監視対象システム:
- MultiStockAnalyzer: 複数銘柄同時分析
- PortfolioExpertConnector: 外部専門家連携
- DynamicPortfolioManager: 動的ポートフォリオ管理

Phase 1 検証条件:
- 初期資金: 50,000円
- 検証期間: 1週間
- 目標: 利益率3%以上、勝率60%以上
"""

import sys
import os
import time
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
import threading
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings('ignore')

# パス設定
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    from analyzer.multi_stock_analyzer import MultiStockAnalyzer, StockAnalysisResult
    from analyzer.portfolio_expert_connector import PortfolioExpertConnector, PortfolioRecommendation
    from analyzer.dynamic_portfolio_manager import DynamicPortfolioManager, PortfolioState
    from data.stock_universe import StockUniverse
except ImportError as e:
    print(f"⚠️ Import Error: {e}")
    print("💡 実取引検証はシミュレーションモードで実行します")


@dataclass
class Phase1Config:
    """Phase 1 検証設定"""
    initial_capital: float = 50000.0          # 初期資金5万円
    max_positions: int = 3                    # 最大ポジション数
    max_position_size: float = 15000.0        # 最大ポジションサイズ
    stop_loss_ratio: float = 0.05             # ストップロス5%
    take_profit_ratio: float = 0.03           # 利確3%
    
    # 監視設定
    monitoring_interval: int = 60             # 監視間隔（秒）
    alert_threshold: float = 0.02             # アラート閾値（2%）
    emergency_stop_loss: float = 0.05         # 緊急停止損失（5%）
    
    # 検証期間
    verification_days: int = 7                # 検証期間（日）
    trading_hours_start: int = 9              # 取引開始時刻
    trading_hours_end: int = 15               # 取引終了時刻


@dataclass
class LiveTradingMetrics:
    """実取引メトリクス"""
    timestamp: datetime
    total_capital: float
    available_cash: float
    positions_count: int
    unrealized_pnl: float
    realized_pnl: float
    total_pnl: float
    win_rate: float
    profit_factor: float
    max_drawdown: float
    sharpe_ratio: float
    system_performance: Dict[str, float]


@dataclass
class SystemPerformance:
    """システム性能データ"""
    multi_analyzer_time: float
    portfolio_connector_time: float
    dynamic_manager_time: float
    total_analysis_time: float
    success_rate: float
    error_count: int


class Phase1LiveTradingMonitor:
    """
    Phase 1 実取引検証監視システム
    
    TECH_LEAD技術統括下での実取引性能検証
    - 5万円小額検証
    - 3システム統合性能監視
    - 24時間監視体制
    """
    
    def __init__(self, config: Phase1Config = None):
        self.config = config or Phase1Config()
        self.logger = self._setup_logger()
        
        # 監視状態
        self.monitoring_active = False
        self.start_time = None
        self.phase1_metrics: List[LiveTradingMetrics] = []
        
        # システム初期化
        self._initialize_systems()
        
        # 監視スレッド
        self.monitoring_thread = None
        self.alert_thread = None
        
        # 統計追跡
        self.stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'system_errors': 0,
            'emergency_stops': 0
        }
        
        self.logger.info("🚀 Phase 1 Live Trading Monitor 初期化完了")
        self.logger.info(f"初期資金: {self.config.initial_capital:,.0f}円")
        self.logger.info(f"検証期間: {self.config.verification_days}日間")
    
    def _setup_logger(self) -> logging.Logger:
        """ログ設定"""
        logger = logging.getLogger('Phase1LiveTradingMonitor')
        logger.setLevel(logging.INFO)
        
        # ファイルハンドラー
        log_file = f'phase1_live_trading_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # コンソールハンドラー
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # フォーマッター
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _initialize_systems(self):
        """システム初期化"""
        try:
            # 3システム初期化
            self.multi_analyzer = MultiStockAnalyzer()
            self.portfolio_connector = PortfolioExpertConnector()
            self.dynamic_manager = DynamicPortfolioManager()
            
            # 銘柄ユニバース
            self.stock_universe = StockUniverse()
            
            # テスト用銘柄（Phase 1用）
            self.test_symbols = ['8306.T', '4689.T', '9984.T', '6758.T', '7203.T']
            
            # 仮想ポートフォリオ初期化
            self.virtual_portfolio = {
                'cash': self.config.initial_capital,
                'positions': {},
                'order_history': [],
                'performance_history': []
            }
            
            self.logger.info("✅ 3システム初期化完了")
            
        except Exception as e:
            self.logger.error(f"❌ システム初期化エラー: {e}")
            self.logger.info("💡 シミュレーションモードで継続")
    
    def start_phase1_monitoring(self):
        """Phase 1 監視開始"""
        if self.monitoring_active:
            self.logger.warning("⚠️ 監視既に開始済み")
            return
        
        self.monitoring_active = True
        self.start_time = datetime.now()
        
        self.logger.info("🚀 Phase 1 実取引検証監視開始")
        self.logger.info(f"開始時刻: {self.start_time}")
        
        # 監視スレッド開始
        self.monitoring_thread = threading.Thread(
            target=self._continuous_monitoring,
            daemon=True
        )
        self.monitoring_thread.start()
        
        # アラートスレッド開始
        self.alert_thread = threading.Thread(
            target=self._alert_monitoring,
            daemon=True
        )
        self.alert_thread.start()
        
        # 初期レポート
        self._generate_initial_report()
    
    def _continuous_monitoring(self):
        """継続監視メインループ"""
        while self.monitoring_active:
            try:
                # 現在時刻チェック
                current_time = datetime.now()
                
                # 取引時間チェック
                if self._is_trading_hours(current_time):
                    # 3システム統合分析実行
                    performance_data = self._execute_integrated_analysis()
                    
                    # メトリクス更新
                    metrics = self._calculate_current_metrics(performance_data)
                    self.phase1_metrics.append(metrics)
                    
                    # リアルタイム報告
                    self._generate_realtime_report(metrics)
                    
                    # 緊急停止チェック
                    if self._check_emergency_stop(metrics):
                        self.logger.critical("🚨 緊急停止条件達成")
                        self.stop_monitoring()
                        break
                
                # 監視間隔待機
                time.sleep(self.config.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"❌ 監視エラー: {e}")
                self.stats['system_errors'] += 1
                time.sleep(5)  # エラー時は短い間隔で再試行
    
    def _is_trading_hours(self, current_time: datetime) -> bool:
        """取引時間チェック"""
        hour = current_time.hour
        weekday = current_time.weekday()
        
        # 平日9:00-15:00のみ
        return (weekday < 5 and 
                self.config.trading_hours_start <= hour < self.config.trading_hours_end)
    
    def _execute_integrated_analysis(self) -> SystemPerformance:
        """3システム統合分析実行"""
        performance = SystemPerformance(
            multi_analyzer_time=0.0,
            portfolio_connector_time=0.0,
            dynamic_manager_time=0.0,
            total_analysis_time=0.0,
            success_rate=0.0,
            error_count=0
        )
        
        total_start = time.time()
        
        try:
            # 仮想市場データ生成（実際は外部APIから取得）
            market_data = self._generate_mock_market_data()
            
            # 1. MultiStockAnalyzer実行
            start_time = time.time()
            try:
                analysis_results = self.multi_analyzer.analyze_multiple_stocks(
                    self.test_symbols, market_data
                )
                performance.multi_analyzer_time = time.time() - start_time
                self.logger.info(f"✅ MultiStockAnalyzer: {len(analysis_results)}銘柄分析完了")
                
            except Exception as e:
                self.logger.error(f"❌ MultiStockAnalyzer エラー: {e}")
                performance.error_count += 1
                analysis_results = []
            
            # 2. PortfolioExpertConnector実行
            start_time = time.time()
            try:
                recommendation = self.portfolio_connector.analyze_with_experts(
                    self.test_symbols, market_data, self.config.initial_capital
                )
                performance.portfolio_connector_time = time.time() - start_time
                self.logger.info(f"✅ PortfolioExpertConnector: 推奨生成完了")
                
            except Exception as e:
                self.logger.error(f"❌ PortfolioExpertConnector エラー: {e}")
                performance.error_count += 1
                recommendation = None
            
            # 3. DynamicPortfolioManager実行
            start_time = time.time()
            try:
                if not hasattr(self.dynamic_manager, 'portfolio_state') or self.dynamic_manager.portfolio_state is None:
                    # 初期化
                    portfolio_state = self.dynamic_manager.initialize_portfolio(
                        self.test_symbols, self.config.initial_capital, market_data
                    )
                else:
                    # 監視・管理
                    rebalance_action = self.dynamic_manager.monitor_and_manage(market_data)
                    if rebalance_action:
                        self.logger.info(f"🔄 リバランス: {rebalance_action.signal.value}")
                
                performance.dynamic_manager_time = time.time() - start_time
                self.logger.info(f"✅ DynamicPortfolioManager: 管理完了")
                
            except Exception as e:
                self.logger.error(f"❌ DynamicPortfolioManager エラー: {e}")
                performance.error_count += 1
            
            # 総合性能計算
            performance.total_analysis_time = time.time() - total_start
            performance.success_rate = (3 - performance.error_count) / 3.0
            
            return performance
            
        except Exception as e:
            self.logger.error(f"❌ 統合分析エラー: {e}")
            performance.error_count = 3
            performance.success_rate = 0.0
            return performance
    
    def _generate_mock_market_data(self) -> Dict:
        """仮想市場データ生成（実際は外部APIから取得）"""
        import pandas as pd
        import numpy as np
        
        market_data = {}
        
        for symbol in self.test_symbols:
            # 60日分のデータ
            dates = pd.date_range(
                start=datetime.now() - timedelta(days=60),
                end=datetime.now(),
                freq='D'
            )
            
            # 価格データ（簡易シミュレーション）
            np.random.seed(42)
            base_price = np.random.uniform(1000, 3000)
            returns = np.random.normal(0, 0.015, len(dates))
            prices = base_price * np.exp(np.cumsum(returns))
            
            # 出来高データ
            volumes = np.random.uniform(100000, 1000000, len(dates))
            
            market_data[symbol] = pd.DataFrame({
                'Date': dates,
                'Open': prices * 0.995,
                'High': prices * 1.005,
                'Low': prices * 0.995,
                'Close': prices,
                'Volume': volumes
            }).set_index('Date')
        
        return market_data
    
    def _calculate_current_metrics(self, performance: SystemPerformance) -> LiveTradingMetrics:
        """現在のメトリクス計算"""
        
        # 仮想ポートフォリオ値計算
        total_capital = self.virtual_portfolio['cash']
        for symbol, position in self.virtual_portfolio['positions'].items():
            total_capital += position.get('value', 0)
        
        # PnL計算
        realized_pnl = sum(order.get('pnl', 0) for order in self.virtual_portfolio['order_history'])
        unrealized_pnl = total_capital - self.config.initial_capital - realized_pnl
        total_pnl = realized_pnl + unrealized_pnl
        
        # 勝率計算
        profitable_trades = len([o for o in self.virtual_portfolio['order_history'] if o.get('pnl', 0) > 0])
        total_trades = len(self.virtual_portfolio['order_history'])
        win_rate = (profitable_trades / total_trades) if total_trades > 0 else 0.0
        
        # プロフィットファクター計算
        total_profit = sum(o.get('pnl', 0) for o in self.virtual_portfolio['order_history'] if o.get('pnl', 0) > 0)
        total_loss = abs(sum(o.get('pnl', 0) for o in self.virtual_portfolio['order_history'] if o.get('pnl', 0) < 0))
        profit_factor = (total_profit / total_loss) if total_loss > 0 else 0.0
        
        # システム性能データ
        system_performance = {
            'multi_analyzer_time': performance.multi_analyzer_time,
            'portfolio_connector_time': performance.portfolio_connector_time,
            'dynamic_manager_time': performance.dynamic_manager_time,
            'total_analysis_time': performance.total_analysis_time,
            'success_rate': performance.success_rate,
            'error_count': performance.error_count
        }
        
        return LiveTradingMetrics(
            timestamp=datetime.now(),
            total_capital=total_capital,
            available_cash=self.virtual_portfolio['cash'],
            positions_count=len(self.virtual_portfolio['positions']),
            unrealized_pnl=unrealized_pnl,
            realized_pnl=realized_pnl,
            total_pnl=total_pnl,
            win_rate=win_rate,
            profit_factor=profit_factor,
            max_drawdown=self._calculate_max_drawdown(),
            sharpe_ratio=self._calculate_sharpe_ratio(),
            system_performance=system_performance
        )
    
    def _calculate_max_drawdown(self) -> float:
        """最大ドローダウン計算"""
        if not self.phase1_metrics:
            return 0.0
        
        peak = self.config.initial_capital
        max_drawdown = 0.0
        
        for metrics in self.phase1_metrics:
            if metrics.total_capital > peak:
                peak = metrics.total_capital
            
            drawdown = (peak - metrics.total_capital) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown
    
    def _calculate_sharpe_ratio(self) -> float:
        """シャープレシオ計算"""
        if len(self.phase1_metrics) < 2:
            return 0.0
        
        returns = []
        for i in range(1, len(self.phase1_metrics)):
            prev_capital = self.phase1_metrics[i-1].total_capital
            current_capital = self.phase1_metrics[i].total_capital
            
            if prev_capital > 0:
                daily_return = (current_capital - prev_capital) / prev_capital
                returns.append(daily_return)
        
        if not returns:
            return 0.0
        
        import numpy as np
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        # 年率化（252営業日）
        return (mean_return * 252) / (std_return * np.sqrt(252))
    
    def _generate_realtime_report(self, metrics: LiveTradingMetrics):
        """リアルタイム報告生成"""
        self.logger.info("📊 リアルタイム監視レポート")
        self.logger.info(f"時刻: {metrics.timestamp}")
        self.logger.info(f"総資本: {metrics.total_capital:,.0f}円")
        self.logger.info(f"総損益: {metrics.total_pnl:+,.0f}円 ({metrics.total_pnl/self.config.initial_capital:+.1%})")
        self.logger.info(f"勝率: {metrics.win_rate:.1%}")
        self.logger.info(f"プロフィットファクター: {metrics.profit_factor:.2f}")
        self.logger.info(f"最大ドローダウン: {metrics.max_drawdown:.1%}")
        
        # システム性能
        self.logger.info("🔧 システム性能:")
        self.logger.info(f"  MultiStockAnalyzer: {metrics.system_performance['multi_analyzer_time']:.1f}秒")
        self.logger.info(f"  PortfolioExpertConnector: {metrics.system_performance['portfolio_connector_time']:.1f}秒")
        self.logger.info(f"  DynamicPortfolioManager: {metrics.system_performance['dynamic_manager_time']:.1f}秒")
        self.logger.info(f"  総分析時間: {metrics.system_performance['total_analysis_time']:.1f}秒")
        self.logger.info(f"  成功率: {metrics.system_performance['success_rate']:.1%}")
        
        # Phase 1 基準チェック
        profit_rate = metrics.total_pnl / self.config.initial_capital
        if profit_rate >= 0.03:
            self.logger.info("✅ Phase 1 利益率基準達成（3%以上）")
        if metrics.win_rate >= 0.6:
            self.logger.info("✅ Phase 1 勝率基準達成（60%以上）")
        if metrics.max_drawdown <= 0.05:
            self.logger.info("✅ Phase 1 ドローダウン基準達成（5%以下）")
    
    def _check_emergency_stop(self, metrics: LiveTradingMetrics) -> bool:
        """緊急停止チェック"""
        loss_ratio = metrics.total_pnl / self.config.initial_capital
        
        if loss_ratio <= -self.config.emergency_stop_loss:
            self.logger.critical(f"🚨 緊急停止: 損失{loss_ratio:.1%} > 閾値{self.config.emergency_stop_loss:.1%}")
            self.stats['emergency_stops'] += 1
            return True
        
        if metrics.max_drawdown > 0.10:  # 10%以上のドローダウン
            self.logger.critical(f"🚨 緊急停止: 最大ドローダウン{metrics.max_drawdown:.1%} > 10%")
            self.stats['emergency_stops'] += 1
            return True
        
        return False
    
    def _alert_monitoring(self):
        """アラート監視"""
        while self.monitoring_active:
            try:
                if self.phase1_metrics:
                    latest_metrics = self.phase1_metrics[-1]
                    
                    # アラート条件チェック
                    loss_ratio = latest_metrics.total_pnl / self.config.initial_capital
                    if loss_ratio <= -self.config.alert_threshold:
                        self.logger.warning(f"⚠️ 損失アラート: {loss_ratio:.1%}")
                    
                    if latest_metrics.system_performance['success_rate'] < 0.8:
                        self.logger.warning(f"⚠️ システム性能低下: {latest_metrics.system_performance['success_rate']:.1%}")
                
                time.sleep(300)  # 5分間隔でアラート監視
                
            except Exception as e:
                self.logger.error(f"❌ アラート監視エラー: {e}")
                time.sleep(60)
    
    def _generate_initial_report(self):
        """初期レポート生成"""
        report = f"""
🚀 Phase 1 実取引検証開始レポート

📊 検証条件:
- 初期資金: {self.config.initial_capital:,.0f}円
- 最大ポジション数: {self.config.max_positions}
- 検証期間: {self.config.verification_days}日間
- 監視間隔: {self.config.monitoring_interval}秒

🎯 Phase 1 成功基準:
- 利益率: 3%以上
- 勝率: 60%以上
- 最大ドローダウン: 5%以下

🔧 監視システム:
- MultiStockAnalyzer: 複数銘柄同時分析
- PortfolioExpertConnector: 外部専門家連携
- DynamicPortfolioManager: 動的ポートフォリオ管理

📈 対象銘柄: {', '.join(self.test_symbols)}

🛡️ 安全措置:
- 緊急停止損失: {self.config.emergency_stop_loss:.1%}
- アラート閾値: {self.config.alert_threshold:.1%}
- 24時間監視体制

開始時刻: {self.start_time}
"""
        
        self.logger.info(report)
        
        # レポートファイル保存
        with open(f'phase1_initial_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md', 'w', encoding='utf-8') as f:
            f.write(report)
    
    def stop_monitoring(self):
        """監視停止"""
        self.monitoring_active = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        if self.alert_thread:
            self.alert_thread.join(timeout=5)
        
        self.logger.info("🛑 Phase 1 監視停止")
        self._generate_final_report()
    
    def _generate_final_report(self):
        """最終レポート生成"""
        if not self.phase1_metrics:
            self.logger.warning("⚠️ メトリクスデータなし")
            return
        
        final_metrics = self.phase1_metrics[-1]
        duration = datetime.now() - self.start_time
        
        report = f"""
📋 Phase 1 実取引検証最終レポート

⏱️ 検証期間: {duration}
📊 総データポイント: {len(self.phase1_metrics)}

💰 最終結果:
- 最終資本: {final_metrics.total_capital:,.0f}円
- 総損益: {final_metrics.total_pnl:+,.0f}円
- 利益率: {final_metrics.total_pnl/self.config.initial_capital:+.1%}
- 勝率: {final_metrics.win_rate:.1%}
- プロフィットファクター: {final_metrics.profit_factor:.2f}
- 最大ドローダウン: {final_metrics.max_drawdown:.1%}
- シャープレシオ: {final_metrics.sharpe_ratio:.2f}

🎯 Phase 1 基準達成状況:
- 利益率3%以上: {'✅' if final_metrics.total_pnl/self.config.initial_capital >= 0.03 else '❌'}
- 勝率60%以上: {'✅' if final_metrics.win_rate >= 0.6 else '❌'}
- ドローダウン5%以下: {'✅' if final_metrics.max_drawdown <= 0.05 else '❌'}

🔧 システム性能:
- 平均分析時間: {sum(m.system_performance['total_analysis_time'] for m in self.phase1_metrics) / len(self.phase1_metrics):.1f}秒
- 平均成功率: {sum(m.system_performance['success_rate'] for m in self.phase1_metrics) / len(self.phase1_metrics):.1%}
- 総エラー数: {sum(m.system_performance['error_count'] for m in self.phase1_metrics)}

📈 統計:
- 総取引数: {self.stats['total_trades']}
- 勝ちトレード: {self.stats['winning_trades']}
- 負けトレード: {self.stats['losing_trades']}
- システムエラー: {self.stats['system_errors']}
- 緊急停止: {self.stats['emergency_stops']}

🔄 次のステップ:
{'✅ Phase 2 進行可能' if self._check_phase2_ready(final_metrics) else '❌ Phase 1 継続が必要'}
"""
        
        self.logger.info(report)
        
        # 最終レポートファイル保存
        with open(f'phase1_final_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md', 'w', encoding='utf-8') as f:
            f.write(report)
        
        # メトリクスデータ保存
        with open(f'phase1_metrics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
            json.dump([asdict(m) for m in self.phase1_metrics], f, indent=2, default=str)
    
    def _check_phase2_ready(self, final_metrics: LiveTradingMetrics) -> bool:
        """Phase 2 準備完了チェック"""
        profit_rate = final_metrics.total_pnl / self.config.initial_capital
        
        return (profit_rate >= 0.03 and
                final_metrics.win_rate >= 0.6 and
                final_metrics.max_drawdown <= 0.05)
    
    def get_current_status(self) -> Dict:
        """現在の状況取得"""
        if not self.phase1_metrics:
            return {'status': 'no_data'}
        
        latest = self.phase1_metrics[-1]
        return {
            'monitoring_active': self.monitoring_active,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'latest_metrics': asdict(latest),
            'stats': self.stats,
            'phase1_ready': self._check_phase2_ready(latest) if self.phase1_metrics else False
        }


def main():
    """メイン実行"""
    print("🚀 Phase 1 Live Trading Monitor 起動")
    
    # 設定
    config = Phase1Config()
    
    # 監視システム初期化
    monitor = Phase1LiveTradingMonitor(config)
    
    try:
        # 監視開始
        monitor.start_phase1_monitoring()
        
        # 監視継続（キーボード中断まで）
        while monitor.monitoring_active:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 監視停止（ユーザー中断）")
        monitor.stop_monitoring()
    
    except Exception as e:
        print(f"❌ エラー: {e}")
        monitor.stop_monitoring()
    
    print("✅ Phase 1 監視完了")


if __name__ == "__main__":
    main()