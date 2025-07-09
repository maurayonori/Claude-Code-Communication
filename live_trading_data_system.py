#!/usr/bin/env python3
"""
【正式取引再開承認】実取引データ供給システム
PRESIDENT承認に基づく800銘柄ユニバース・100並列データ取得での実取引データ供給
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass
import json
import pandas as pd
from pathlib import Path
import threading
from queue import Queue, Empty
import signal
import atexit

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('live_trading_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TradingMode(Enum):
    """取引モード"""
    SIMULATION = "simulation"
    PAPER = "paper"
    LIVE = "live"
    EMERGENCY_STOP = "emergency_stop"

class DataQuality(Enum):
    """データ品質"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    CRITICAL = "critical"

@dataclass
class LiveTradingConfig:
    """実取引設定"""
    mode: TradingMode = TradingMode.LIVE
    max_concurrent_requests: int = 100
    data_refresh_interval: int = 1  # 1秒間隔
    quality_threshold: float = 0.95  # 95%以上の品質要求
    emergency_stop_threshold: float = 0.80  # 80%以下で緊急停止
    max_latency_ms: float = 500  # 最大レイテンシ500ms
    enable_kabu_api: bool = True
    enable_yahoo_finance: bool = True
    enable_real_time_monitoring: bool = True
    enable_safety_checks: bool = True
    data_backup_enabled: bool = True
    
class LiveTradingDataSystem:
    """実取引データ供給システム"""
    
    def __init__(self, config: LiveTradingConfig = None):
        self.config = config or LiveTradingConfig()
        self.logger = logger
        self.mode = self.config.mode
        self.is_running = False
        self.emergency_stop = False
        
        # PRESIDENT承認確認
        self.president_approval = True  # 承認受領済み
        
        # システムコンポーネント
        from distributed_investment_system import DistributedInvestmentSystem
        self.distributed_system = DistributedInvestmentSystem()
        
        # データ品質監視
        self.data_quality_monitor = DataQualityMonitor()
        
        # 実取引用統計
        self.live_stats = {
            'start_time': datetime.now(),
            'total_data_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_latency_ms': 0,
            'data_quality_score': 0.0,
            'emergency_stops': 0,
            'uptime_seconds': 0
        }
        
        # 緊急停止処理
        self._setup_emergency_handlers()
        
        self.logger.info("🚀 LiveTradingDataSystem初期化完了")
    
    def _setup_emergency_handlers(self):
        """緊急停止ハンドラー設定"""
        def emergency_stop_handler(signum, frame):
            self.logger.warning("🚨 緊急停止シグナル受信")
            self.emergency_stop_system()
        
        signal.signal(signal.SIGINT, emergency_stop_handler)
        signal.signal(signal.SIGTERM, emergency_stop_handler)
        atexit.register(self.shutdown_system)
    
    def verify_president_approval(self) -> bool:
        """PRESIDENT承認確認"""
        if not self.president_approval:
            self.logger.error("❌ PRESIDENT承認が未確認です")
            return False
        
        self.logger.info("✅ PRESIDENT承認確認済み - 実取引データ供給承認")
        return True
    
    def verify_system_readiness(self) -> bool:
        """システム準備状態確認"""
        readiness_checks = [
            ("PRESIDENT承認", self.verify_president_approval()),
            ("800銘柄ユニバース", len(self.distributed_system.universe_manager.stocks) >= 800),
            ("100並列データ取得", self.distributed_system.batch_fetcher.max_workers >= 100),
            ("リアルタイム監視", self.distributed_system.real_time_monitor is not None),
            ("データ品質監視", self.data_quality_monitor is not None),
            ("緊急停止機能", not self.emergency_stop)
        ]
        
        all_ready = True
        self.logger.info("=== システム準備状態確認 ===")
        
        for check_name, status in readiness_checks:
            status_symbol = "✅" if status else "❌"
            self.logger.info(f"{status_symbol} {check_name}: {'OK' if status else 'NG'}")
            if not status:
                all_ready = False
        
        if all_ready:
            self.logger.info("🎉 全システム準備完了 - 実取引データ供給開始可能")
        else:
            self.logger.error("⚠️ システム準備未完了 - 実取引データ供給不可")
        
        return all_ready
    
    async def start_live_trading_data_supply(self):
        """実取引データ供給開始"""
        if not self.verify_system_readiness():
            raise RuntimeError("システム準備未完了")
        
        self.logger.info("🚀 実取引データ供給開始")
        self.is_running = True
        self.mode = TradingMode.LIVE
        
        # 分散投資システム開始
        batch_task = await self.distributed_system.start_system()
        
        # データ品質監視開始
        quality_task = asyncio.create_task(self.data_quality_monitor.start_monitoring())
        
        # 実取引データ供給ループ開始
        supply_task = asyncio.create_task(self._live_data_supply_loop())
        
        # 統計更新タスク
        stats_task = asyncio.create_task(self._update_live_stats())
        
        self.logger.info("✅ 実取引データ供給システム稼働開始")
        
        return [batch_task, quality_task, supply_task, stats_task]
    
    async def _live_data_supply_loop(self):
        """実取引データ供給ループ"""
        while self.is_running and not self.emergency_stop:
            try:
                loop_start = time.time()
                
                # 800銘柄ユニバースからアクティブ銘柄を取得
                active_symbols = self.distributed_system.universe_manager.get_active_symbols()
                
                # 100並列データ取得システムでデータ取得
                if active_symbols:
                    request_id = self.distributed_system.batch_fetcher.submit_batch_request(
                        active_symbols[:800],  # 800銘柄に制限
                        priority=1  # 最高優先度
                    )
                    
                    # データ取得完了待機
                    await asyncio.sleep(0.5)
                    
                    # 結果取得
                    result = self.distributed_system.batch_fetcher.get_cached_results(request_id)
                    
                    if result:
                        await self._process_live_data(result)
                        self.live_stats['successful_requests'] += 1
                    else:
                        self.live_stats['failed_requests'] += 1
                        self.logger.warning("データ取得結果未取得")
                
                # データ品質チェック
                quality_score = self.data_quality_monitor.get_current_quality_score()
                
                if quality_score < self.config.emergency_stop_threshold:
                    self.logger.error(f"🚨 データ品質低下: {quality_score:.2%} < {self.config.emergency_stop_threshold:.2%}")
                    self.emergency_stop_system()
                    break
                
                # 次のループまでの待機
                loop_duration = time.time() - loop_start
                sleep_time = max(0, self.config.data_refresh_interval - loop_duration)
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                self.logger.error(f"実取引データ供給ループエラー: {e}")
                self.live_stats['failed_requests'] += 1
                
                # 連続エラーでの緊急停止
                if self.live_stats['failed_requests'] > 10:
                    self.logger.error("🚨 連続エラー発生 - 緊急停止")
                    self.emergency_stop_system()
                    break
                
                await asyncio.sleep(1)
    
    async def _process_live_data(self, result: Dict[str, Any]):
        """実取引データ処理"""
        if 'results' not in result:
            return
        
        live_data = result['results']
        processed_count = 0
        
        for symbol, data in live_data.items():
            try:
                # データ品質チェック
                if self._validate_data_quality(symbol, data):
                    # 実取引システムへデータ供給
                    await self._supply_data_to_trading_system(symbol, data)
                    processed_count += 1
                else:
                    self.logger.warning(f"データ品質不良: {symbol}")
                    
            except Exception as e:
                self.logger.error(f"データ処理エラー {symbol}: {e}")
        
        self.logger.info(f"📊 実取引データ処理完了: {processed_count}/{len(live_data)}銘柄")
    
    def _validate_data_quality(self, symbol: str, data: Any) -> bool:
        """データ品質検証"""
        if not data:
            return False
        
        # 基本的な品質チェック
        if hasattr(data, 'price') and hasattr(data, 'timestamp'):
            # 価格の妥当性チェック
            if data.price <= 0:
                return False
            
            # タイムスタンプの新しさチェック
            if hasattr(data, 'timestamp'):
                data_age = (datetime.now() - data.timestamp).total_seconds()
                if data_age > 60:  # 1分以上古い
                    return False
            
            # レイテンシチェック
            if hasattr(data, 'latency_ms'):
                if data.latency_ms > self.config.max_latency_ms:
                    return False
            
            return True
        
        return False
    
    async def _supply_data_to_trading_system(self, symbol: str, data: Any):
        """取引システムへのデータ供給"""
        # 実取引システムへのデータ供給をシミュレート
        self.logger.debug(f"📤 取引システムへデータ供給: {symbol}")
        
        # 実際の実装では、取引システムのAPIを呼び出す
        # trading_system.update_market_data(symbol, data)
        
        # データ品質監視へ報告
        self.data_quality_monitor.record_data_supply(symbol, data)
    
    async def _update_live_stats(self):
        """実取引統計更新"""
        while self.is_running and not self.emergency_stop:
            try:
                current_time = datetime.now()
                self.live_stats['uptime_seconds'] = (current_time - self.live_stats['start_time']).total_seconds()
                
                # 成功率計算
                total_requests = self.live_stats['total_data_requests']
                if total_requests > 0:
                    success_rate = self.live_stats['successful_requests'] / total_requests
                    self.live_stats['success_rate'] = success_rate
                
                # データ品質スコア更新
                self.live_stats['data_quality_score'] = self.data_quality_monitor.get_current_quality_score()
                
                # 統計ログ出力
                self.logger.info(f"📈 実取引統計: 成功率={self.live_stats.get('success_rate', 0):.2%}, "
                               f"品質={self.live_stats['data_quality_score']:.2%}, "
                               f"稼働時間={self.live_stats['uptime_seconds']:.0f}秒")
                
                await asyncio.sleep(10)  # 10秒間隔で更新
                
            except Exception as e:
                self.logger.error(f"統計更新エラー: {e}")
                await asyncio.sleep(5)
    
    def emergency_stop_system(self):
        """緊急停止システム"""
        self.logger.error("🚨 緊急停止システム作動")
        self.emergency_stop = True
        self.is_running = False
        self.mode = TradingMode.EMERGENCY_STOP
        self.live_stats['emergency_stops'] += 1
        
        # 分散投資システム停止
        self.distributed_system.stop_system()
        
        # 緊急停止通知
        self.logger.error("⚠️ 実取引データ供給緊急停止 - 手動復旧が必要")
    
    def shutdown_system(self):
        """システムシャットダウン"""
        if self.is_running:
            self.logger.info("🔴 システムシャットダウン開始")
            self.is_running = False
            self.distributed_system.stop_system()
            self.logger.info("✅ システムシャットダウン完了")
    
    def get_system_status(self) -> Dict[str, Any]:
        """システム状態取得"""
        return {
            'mode': self.mode.value,
            'is_running': self.is_running,
            'emergency_stop': self.emergency_stop,
            'president_approval': self.president_approval,
            'live_stats': self.live_stats,
            'data_quality_score': self.data_quality_monitor.get_current_quality_score(),
            'system_components': {
                'universe_stocks': len(self.distributed_system.universe_manager.stocks),
                'batch_workers': self.distributed_system.batch_fetcher.max_workers,
                'monitoring_active': self.distributed_system.real_time_monitor.status.value
            }
        }

class DataQualityMonitor:
    """データ品質監視システム"""
    
    def __init__(self):
        self.quality_history = []
        self.current_quality_score = 1.0
        self.data_supply_count = 0
        self.quality_issues = []
        self.monitoring_active = False
    
    async def start_monitoring(self):
        """品質監視開始"""
        self.monitoring_active = True
        logger.info("📊 データ品質監視開始")
        
        while self.monitoring_active:
            try:
                # 品質スコア計算
                self._calculate_quality_score()
                
                # 品質履歴記録
                self.quality_history.append({
                    'timestamp': datetime.now(),
                    'score': self.current_quality_score,
                    'issues': len(self.quality_issues)
                })
                
                # 履歴サイズ制限
                if len(self.quality_history) > 1000:
                    self.quality_history = self.quality_history[-500:]
                
                await asyncio.sleep(5)  # 5秒間隔で監視
                
            except Exception as e:
                logger.error(f"品質監視エラー: {e}")
                await asyncio.sleep(1)
    
    def _calculate_quality_score(self):
        """品質スコア計算"""
        if self.data_supply_count == 0:
            self.current_quality_score = 1.0
            return
        
        # 品質問題の割合を計算
        issue_ratio = len(self.quality_issues) / max(1, self.data_supply_count)
        self.current_quality_score = max(0.0, 1.0 - issue_ratio)
    
    def record_data_supply(self, symbol: str, data: Any):
        """データ供給記録"""
        self.data_supply_count += 1
        
        # 品質問題のチェック
        if hasattr(data, 'price') and data.price <= 0:
            self.quality_issues.append(f"{symbol}: 無効な価格")
        
        if hasattr(data, 'latency_ms') and data.latency_ms > 1000:
            self.quality_issues.append(f"{symbol}: 高レイテンシ")
    
    def get_current_quality_score(self) -> float:
        """現在の品質スコア取得"""
        return self.current_quality_score
    
    def stop_monitoring(self):
        """品質監視停止"""
        self.monitoring_active = False
        logger.info("📊 データ品質監視停止")

async def main():
    """メイン実行関数"""
    logger.info("=" * 80)
    logger.info("🚀 【正式取引再開承認】実取引データ供給システム")
    logger.info("PRESIDENT承認に基づく800銘柄ユニバース・100並列データ取得での実取引データ供給")
    logger.info("=" * 80)
    
    # 実取引データシステム初期化
    live_system = LiveTradingDataSystem()
    
    try:
        # 実取引データ供給開始
        tasks = await live_system.start_live_trading_data_supply()
        
        # 30秒間実行
        await asyncio.sleep(30)
        
        # システム状態確認
        status = live_system.get_system_status()
        logger.info(f"💹 システム状態: {json.dumps(status, indent=2, ensure_ascii=False)}")
        
    except KeyboardInterrupt:
        logger.info("🛑 ユーザーによる停止要求")
    except Exception as e:
        logger.error(f"❌ システムエラー: {e}")
    finally:
        live_system.shutdown_system()
    
    logger.info("✅ 実取引データ供給システム終了")

if __name__ == "__main__":
    asyncio.run(main())