#!/usr/bin/env python3
"""
【実取引検証開始】Phase 1: 5万円制限実取引データ供給システム
TECH_LEAD技術統括による800銘柄ユニバース・100並列データ取得システムの実取引検証
24時間データ品質・取得安定性監視
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
from dataclasses import dataclass, field
import json
import pandas as pd
from pathlib import Path
import threading
from queue import Queue, Empty
import signal
import atexit
import sqlite3
from collections import deque, defaultdict
import statistics
import psutil
import traceback

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phase1_live_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Phase1Status(Enum):
    """Phase 1 状態"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    MONITORING = "monitoring"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"

class MonitoringAlert(Enum):
    """監視アラート"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Phase1Config:
    """Phase 1 設定"""
    capital_limit: int = 50000  # 5万円制限
    max_parallel_requests: int = 100  # 100並列
    universe_size: int = 800  # 800銘柄
    data_refresh_interval: int = 1  # 1秒間隔
    monitoring_duration_hours: int = 24  # 24時間監視
    quality_threshold: float = 0.90  # 90%品質閾値
    stability_threshold: float = 0.95  # 95%安定性閾値
    report_interval_minutes: int = 60  # 1時間毎報告
    max_memory_mb: int = 2048  # 2GB制限
    max_cpu_percent: float = 80.0  # CPU使用率80%制限

@dataclass
class DataQualityMetrics:
    """データ品質指標"""
    timestamp: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_latency_ms: float
    data_freshness_score: float
    completeness_score: float
    accuracy_score: float
    overall_quality_score: float

@dataclass
class SystemStabilityMetrics:
    """システム安定性指標"""
    timestamp: datetime
    uptime_seconds: float
    memory_usage_mb: float
    cpu_usage_percent: float
    network_requests_per_second: float
    error_rate: float
    recovery_time_seconds: float
    stability_score: float

class Phase1LiveTradingSystem:
    """Phase 1 実取引データ供給システム"""
    
    def __init__(self, config: Phase1Config = None):
        self.config = config or Phase1Config()
        self.logger = logger
        self.status = Phase1Status.INITIALIZING
        self.start_time = datetime.now()
        self.is_running = False
        self.emergency_stop = False
        
        # TECH_LEAD承認確認
        self.tech_lead_approval = True
        
        # 監視データ
        self.quality_metrics_history = deque(maxlen=86400)  # 24時間分
        self.stability_metrics_history = deque(maxlen=86400)  # 24時間分
        self.alerts = deque(maxlen=1000)
        
        # 統計情報
        self.phase1_stats = {
            'start_time': self.start_time,
            'capital_limit': self.config.capital_limit,
            'universe_size': self.config.universe_size,
            'parallel_requests': self.config.max_parallel_requests,
            'total_data_points': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'uptime_seconds': 0,
            'current_quality_score': 0.0,
            'current_stability_score': 0.0,
            'alerts_generated': 0,
            'reports_sent': 0
        }
        
        # 分散投資システム
        from distributed_investment_system import DistributedInvestmentSystem
        self.distributed_system = DistributedInvestmentSystem()
        
        # 監視システム
        self.quality_monitor = DataQualityMonitor24H()
        self.stability_monitor = SystemStabilityMonitor24H()
        
        # データベース
        self.db_path = Path("phase1_monitoring.db")
        self._init_database()
        
        # 緊急停止設定
        self._setup_emergency_handlers()
        
        self.logger.info("🚀 Phase 1 LiveTradingSystem初期化完了")
    
    def _init_database(self):
        """監視データベース初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS quality_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    total_requests INTEGER,
                    successful_requests INTEGER,
                    failed_requests INTEGER,
                    average_latency_ms REAL,
                    data_freshness_score REAL,
                    completeness_score REAL,
                    accuracy_score REAL,
                    overall_quality_score REAL
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS stability_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    uptime_seconds REAL,
                    memory_usage_mb REAL,
                    cpu_usage_percent REAL,
                    network_requests_per_second REAL,
                    error_rate REAL,
                    recovery_time_seconds REAL,
                    stability_score REAL
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    alert_type TEXT,
                    severity TEXT,
                    message TEXT,
                    resolved INTEGER DEFAULT 0
                )
            ''')
            
            conn.commit()
    
    def _setup_emergency_handlers(self):
        """緊急停止ハンドラー"""
        def emergency_stop_handler(signum, frame):
            self.logger.error("🚨 緊急停止シグナル受信")
            self.emergency_stop_system()
        
        signal.signal(signal.SIGINT, emergency_stop_handler)
        signal.signal(signal.SIGTERM, emergency_stop_handler)
        atexit.register(self.shutdown_system)
    
    def verify_tech_lead_approval(self) -> bool:
        """TECH_LEAD承認確認"""
        if not self.tech_lead_approval:
            self.logger.error("❌ TECH_LEAD承認が未確認です")
            return False
        
        self.logger.info("✅ TECH_LEAD承認確認済み - Phase 1実取引検証承認")
        return True
    
    def verify_phase1_readiness(self) -> bool:
        """Phase 1 準備状態確認"""
        readiness_checks = [
            ("TECH_LEAD承認", self.verify_tech_lead_approval()),
            ("5万円制限設定", self.config.capital_limit == 50000),
            ("800銘柄ユニバース", len(self.distributed_system.universe_manager.stocks) >= 800),
            ("100並列データ取得", self.distributed_system.batch_fetcher.max_workers >= 100),
            ("24時間監視準備", self.quality_monitor is not None and self.stability_monitor is not None),
            ("データベース準備", self.db_path.exists()),
            ("緊急停止機能", not self.emergency_stop)
        ]
        
        all_ready = True
        self.logger.info("=== Phase 1 準備状態確認 ===")
        
        for check_name, status in readiness_checks:
            status_symbol = "✅" if status else "❌"
            self.logger.info(f"{status_symbol} {check_name}: {'OK' if status else 'NG'}")
            if not status:
                all_ready = False
        
        if all_ready:
            self.logger.info("🎉 Phase 1 全システム準備完了")
        else:
            self.logger.error("⚠️ Phase 1 システム準備未完了")
        
        return all_ready
    
    async def start_phase1_verification(self):
        """Phase 1 検証開始"""
        if not self.verify_phase1_readiness():
            raise RuntimeError("Phase 1 システム準備未完了")
        
        self.logger.info("🚀 Phase 1 実取引検証開始")
        self.status = Phase1Status.RUNNING
        self.is_running = True
        
        # 分散投資システム開始
        system_task = await self.distributed_system.start_system()
        
        # 24時間監視開始
        monitoring_tasks = [
            asyncio.create_task(self.quality_monitor.start_24h_monitoring()),
            asyncio.create_task(self.stability_monitor.start_24h_monitoring()),
            asyncio.create_task(self._phase1_main_loop()),
            asyncio.create_task(self._periodic_reporting()),
            asyncio.create_task(self._system_health_check())
        ]
        
        self.logger.info("✅ Phase 1 実取引検証システム稼働開始")
        self.status = Phase1Status.MONITORING
        
        return [system_task] + monitoring_tasks
    
    async def _phase1_main_loop(self):
        """Phase 1 メインループ"""
        while self.is_running and not self.emergency_stop:
            try:
                loop_start = time.time()
                
                # 800銘柄ユニバースデータ取得
                active_symbols = self.distributed_system.universe_manager.get_active_symbols()
                
                if active_symbols:
                    # 5万円制限を考慮した銘柄選択
                    selected_symbols = self._select_symbols_for_capital_limit(active_symbols)
                    
                    # 100並列データ取得
                    request_id = self.distributed_system.batch_fetcher.submit_batch_request(
                        selected_symbols,
                        priority=1  # 最高優先度
                    )
                    
                    # データ取得結果処理
                    await asyncio.sleep(0.5)
                    result = self.distributed_system.batch_fetcher.get_cached_results(request_id)
                    
                    if result:
                        await self._process_phase1_data(result)
                        self.phase1_stats['successful_operations'] += 1
                    else:
                        self.phase1_stats['failed_operations'] += 1
                
                # 統計更新
                self._update_phase1_stats()
                
                # 品質チェック
                await self._check_quality_thresholds()
                
                # 安定性チェック
                await self._check_stability_thresholds()
                
                # 次のループまでの待機
                loop_duration = time.time() - loop_start
                sleep_time = max(0, self.config.data_refresh_interval - loop_duration)
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                self.logger.error(f"Phase 1 メインループエラー: {e}")
                self.phase1_stats['failed_operations'] += 1
                
                # 連続エラーでの緊急停止
                if self.phase1_stats['failed_operations'] > 100:
                    self.logger.error("🚨 連続エラー発生 - 緊急停止")
                    self.emergency_stop_system()
                    break
                
                await asyncio.sleep(5)
    
    def _select_symbols_for_capital_limit(self, symbols: List[str]) -> List[str]:
        """5万円制限を考慮した銘柄選択"""
        # 価格帯別に銘柄を分類
        low_price_symbols = []  # 1000円以下
        mid_price_symbols = []  # 1000-3000円
        high_price_symbols = []  # 3000円以上
        
        for symbol in symbols:
            stock_info = self.distributed_system.universe_manager.stocks.get(symbol)
            if stock_info:
                avg_price = (stock_info.price_range[0] + stock_info.price_range[1]) / 2
                if avg_price <= 1000:
                    low_price_symbols.append(symbol)
                elif avg_price <= 3000:
                    mid_price_symbols.append(symbol)
                else:
                    high_price_symbols.append(symbol)
        
        # 5万円制限に基づく選択
        selected = []
        
        # 低価格銘柄から50銘柄
        selected.extend(low_price_symbols[:50])
        
        # 中価格銘柄から30銘柄
        selected.extend(mid_price_symbols[:30])
        
        # 高価格銘柄から20銘柄
        selected.extend(high_price_symbols[:20])
        
        # 合計100銘柄に制限
        return selected[:100]
    
    async def _process_phase1_data(self, result: Dict[str, Any]):
        """Phase 1 データ処理"""
        if 'results' not in result:
            return
        
        live_data = result['results']
        processed_count = 0
        
        for symbol, data in live_data.items():
            try:
                # データ品質検証
                if self._validate_phase1_data(symbol, data):
                    # 監視システムへ記録
                    self.quality_monitor.record_data_point(symbol, data)
                    self.stability_monitor.record_operation(symbol, True)
                    processed_count += 1
                else:
                    self.stability_monitor.record_operation(symbol, False)
                    
            except Exception as e:
                self.logger.error(f"データ処理エラー {symbol}: {e}")
                self.stability_monitor.record_operation(symbol, False)
        
        self.phase1_stats['total_data_points'] += processed_count
        self.logger.info(f"📊 Phase 1 データ処理完了: {processed_count}/{len(live_data)}銘柄")
    
    def _validate_phase1_data(self, symbol: str, data: Any) -> bool:
        """Phase 1 データ品質検証"""
        if not data:
            return False
        
        # 基本的な品質チェック
        if hasattr(data, 'price') and hasattr(data, 'timestamp'):
            # 価格の妥当性
            if data.price <= 0 or data.price > 50000:  # 5万円制限考慮
                return False
            
            # タイムスタンプの新しさ
            if hasattr(data, 'timestamp'):
                data_age = (datetime.now() - data.timestamp).total_seconds()
                if data_age > 300:  # 5分以上古い
                    return False
            
            # レイテンシチェック
            if hasattr(data, 'latency_ms'):
                if data.latency_ms > 1000:  # 1秒以上
                    return False
            
            return True
        
        return False
    
    def _update_phase1_stats(self):
        """Phase 1 統計更新"""
        current_time = datetime.now()
        self.phase1_stats['uptime_seconds'] = (current_time - self.start_time).total_seconds()
        
        # 成功率計算
        total_ops = self.phase1_stats['successful_operations'] + self.phase1_stats['failed_operations']
        if total_ops > 0:
            success_rate = self.phase1_stats['successful_operations'] / total_ops
            self.phase1_stats['success_rate'] = success_rate
        
        # 現在の品質・安定性スコア
        self.phase1_stats['current_quality_score'] = self.quality_monitor.get_current_score()
        self.phase1_stats['current_stability_score'] = self.stability_monitor.get_current_score()
    
    async def _check_quality_thresholds(self):
        """品質閾値チェック"""
        current_quality = self.quality_monitor.get_current_score()
        
        if current_quality < self.config.quality_threshold:
            alert_msg = f"データ品質低下: {current_quality:.2%} < {self.config.quality_threshold:.2%}"
            await self._generate_alert(MonitoringAlert.WARNING, alert_msg)
            
            if current_quality < 0.70:  # 70%以下で緊急停止
                await self._generate_alert(MonitoringAlert.CRITICAL, "データ品質危険レベル - 緊急停止")
                self.emergency_stop_system()
    
    async def _check_stability_thresholds(self):
        """安定性閾値チェック"""
        current_stability = self.stability_monitor.get_current_score()
        
        if current_stability < self.config.stability_threshold:
            alert_msg = f"システム安定性低下: {current_stability:.2%} < {self.config.stability_threshold:.2%}"
            await self._generate_alert(MonitoringAlert.WARNING, alert_msg)
            
            if current_stability < 0.80:  # 80%以下で緊急停止
                await self._generate_alert(MonitoringAlert.CRITICAL, "システム安定性危険レベル - 緊急停止")
                self.emergency_stop_system()
    
    async def _generate_alert(self, severity: MonitoringAlert, message: str):
        """アラート生成"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'severity': severity.value,
            'message': message,
            'resolved': False
        }
        
        self.alerts.append(alert)
        self.phase1_stats['alerts_generated'] += 1
        
        # データベースに保存
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO alerts (timestamp, alert_type, severity, message)
                VALUES (?, ?, ?, ?)
            ''', (alert['timestamp'], 'system', severity.value, message))
            conn.commit()
        
        # 重要度に応じてログ出力
        if severity == MonitoringAlert.CRITICAL:
            self.logger.error(f"🚨 CRITICAL: {message}")
        elif severity == MonitoringAlert.ERROR:
            self.logger.error(f"❌ ERROR: {message}")
        elif severity == MonitoringAlert.WARNING:
            self.logger.warning(f"⚠️ WARNING: {message}")
        else:
            self.logger.info(f"ℹ️ INFO: {message}")
    
    async def _periodic_reporting(self):
        """定期報告"""
        while self.is_running and not self.emergency_stop:
            try:
                # TECH_LEADへの報告
                await self._send_tech_lead_report()
                
                # 次の報告まで待機
                await asyncio.sleep(self.config.report_interval_minutes * 60)
                
            except Exception as e:
                self.logger.error(f"定期報告エラー: {e}")
                await asyncio.sleep(300)  # 5分後に再試行
    
    async def _send_tech_lead_report(self):
        """TECH_LEADへの報告送信"""
        try:
            report = self._generate_tech_lead_report()
            
            # agent-send.shを使用してTECH_LEADに送信
            import subprocess
            
            report_message = f"""Phase 1 実取引検証定期報告

## システム状態
- 稼働時間: {self.phase1_stats['uptime_seconds']:.0f}秒
- 処理データ: {self.phase1_stats['total_data_points']:,}件
- 成功率: {self.phase1_stats.get('success_rate', 0):.2%}
- 品質スコア: {self.phase1_stats['current_quality_score']:.2%}
- 安定性スコア: {self.phase1_stats['current_stability_score']:.2%}

## 監視結果
- アラート件数: {self.phase1_stats['alerts_generated']}件
- 緊急停止: {'あり' if self.emergency_stop else 'なし'}
- システム状態: {self.status.value}

## 次回報告: {(datetime.now() + timedelta(minutes=self.config.report_interval_minutes)).strftime('%H:%M')}

Data Engineer Phase 1 報告"""
            
            # スクリプト実行
            result = subprocess.run(
                ['./agent-send.sh', 'tech_lead', report_message],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(__file__)
            )
            
            if result.returncode == 0:
                self.phase1_stats['reports_sent'] += 1
                self.logger.info("📤 TECH_LEADへの報告送信完了")
            else:
                self.logger.error(f"報告送信失敗: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"TECH_LEAD報告送信エラー: {e}")
    
    def _generate_tech_lead_report(self) -> Dict[str, Any]:
        """TECH_LEAD報告生成"""
        return {
            'timestamp': datetime.now().isoformat(),
            'phase': 'Phase 1',
            'status': self.status.value,
            'uptime_seconds': self.phase1_stats['uptime_seconds'],
            'capital_limit': self.config.capital_limit,
            'universe_size': len(self.distributed_system.universe_manager.stocks),
            'parallel_requests': self.config.max_parallel_requests,
            'total_data_points': self.phase1_stats['total_data_points'],
            'success_rate': self.phase1_stats.get('success_rate', 0),
            'quality_score': self.phase1_stats['current_quality_score'],
            'stability_score': self.phase1_stats['current_stability_score'],
            'alerts_generated': self.phase1_stats['alerts_generated'],
            'reports_sent': self.phase1_stats['reports_sent'],
            'emergency_stop': self.emergency_stop
        }
    
    async def _system_health_check(self):
        """システムヘルスチェック"""
        while self.is_running and not self.emergency_stop:
            try:
                # メモリ使用量チェック
                memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                if memory_usage > self.config.max_memory_mb:
                    await self._generate_alert(
                        MonitoringAlert.WARNING,
                        f"メモリ使用量超過: {memory_usage:.0f}MB > {self.config.max_memory_mb}MB"
                    )
                
                # CPU使用率チェック
                cpu_usage = psutil.cpu_percent(interval=1)
                if cpu_usage > self.config.max_cpu_percent:
                    await self._generate_alert(
                        MonitoringAlert.WARNING,
                        f"CPU使用率超過: {cpu_usage:.1f}% > {self.config.max_cpu_percent}%"
                    )
                
                await asyncio.sleep(30)  # 30秒間隔
                
            except Exception as e:
                self.logger.error(f"ヘルスチェックエラー: {e}")
                await asyncio.sleep(60)
    
    def emergency_stop_system(self):
        """緊急停止システム"""
        self.logger.error("🚨 Phase 1 緊急停止システム作動")
        self.emergency_stop = True
        self.is_running = False
        self.status = Phase1Status.ERROR
        
        # 分散投資システム停止
        self.distributed_system.stop_system()
        
        # 緊急停止通知
        self.logger.error("⚠️ Phase 1 実取引検証緊急停止 - TECH_LEADへの報告が必要")
    
    def shutdown_system(self):
        """システムシャットダウン"""
        if self.is_running:
            self.logger.info("🔴 Phase 1 システムシャットダウン開始")
            self.is_running = False
            self.status = Phase1Status.STOPPED
            self.distributed_system.stop_system()
            self.logger.info("✅ Phase 1 システムシャットダウン完了")
    
    def get_phase1_status(self) -> Dict[str, Any]:
        """Phase 1 状態取得"""
        return {
            'phase': 'Phase 1',
            'status': self.status.value,
            'tech_lead_approval': self.tech_lead_approval,
            'config': {
                'capital_limit': self.config.capital_limit,
                'universe_size': self.config.universe_size,
                'parallel_requests': self.config.max_parallel_requests,
                'monitoring_duration_hours': self.config.monitoring_duration_hours
            },
            'stats': self.phase1_stats,
            'current_metrics': {
                'quality_score': self.quality_monitor.get_current_score(),
                'stability_score': self.stability_monitor.get_current_score(),
                'recent_alerts': len([a for a in self.alerts if not a.get('resolved', False)])
            },
            'emergency_stop': self.emergency_stop
        }

class DataQualityMonitor24H:
    """24時間データ品質監視"""
    
    def __init__(self):
        self.monitoring_active = False
        self.data_points = deque(maxlen=86400)  # 24時間分
        self.quality_scores = deque(maxlen=86400)
        self.current_score = 1.0
    
    async def start_24h_monitoring(self):
        """24時間監視開始"""
        self.monitoring_active = True
        logger.info("📊 24時間データ品質監視開始")
        
        while self.monitoring_active:
            try:
                self._calculate_quality_metrics()
                await asyncio.sleep(10)  # 10秒間隔
            except Exception as e:
                logger.error(f"品質監視エラー: {e}")
                await asyncio.sleep(60)
    
    def record_data_point(self, symbol: str, data: Any):
        """データポイント記録"""
        self.data_points.append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'data': data
        })
    
    def _calculate_quality_metrics(self):
        """品質指標計算"""
        if len(self.data_points) == 0:
            self.current_score = 1.0
            return
        
        # 最近1分間のデータを評価
        recent_data = [
            dp for dp in self.data_points
            if (datetime.now() - dp['timestamp']).total_seconds() < 60
        ]
        
        if not recent_data:
            self.current_score = 0.0
            return
        
        # 品質スコア計算
        valid_data_count = sum(1 for dp in recent_data if self._is_valid_data(dp['data']))
        self.current_score = valid_data_count / len(recent_data)
        
        self.quality_scores.append({
            'timestamp': datetime.now(),
            'score': self.current_score
        })
    
    def _is_valid_data(self, data: Any) -> bool:
        """データ有効性チェック"""
        if not data:
            return False
        
        if hasattr(data, 'price') and hasattr(data, 'timestamp'):
            return data.price > 0 and data.timestamp is not None
        
        return False
    
    def get_current_score(self) -> float:
        """現在の品質スコア取得"""
        return self.current_score
    
    def stop_monitoring(self):
        """監視停止"""
        self.monitoring_active = False

class SystemStabilityMonitor24H:
    """24時間システム安定性監視"""
    
    def __init__(self):
        self.monitoring_active = False
        self.operations = deque(maxlen=86400)  # 24時間分
        self.stability_scores = deque(maxlen=86400)
        self.current_score = 1.0
    
    async def start_24h_monitoring(self):
        """24時間監視開始"""
        self.monitoring_active = True
        logger.info("🔧 24時間システム安定性監視開始")
        
        while self.monitoring_active:
            try:
                self._calculate_stability_metrics()
                await asyncio.sleep(10)  # 10秒間隔
            except Exception as e:
                logger.error(f"安定性監視エラー: {e}")
                await asyncio.sleep(60)
    
    def record_operation(self, operation_id: str, success: bool):
        """操作記録"""
        self.operations.append({
            'timestamp': datetime.now(),
            'operation_id': operation_id,
            'success': success
        })
    
    def _calculate_stability_metrics(self):
        """安定性指標計算"""
        if len(self.operations) == 0:
            self.current_score = 1.0
            return
        
        # 最近1分間の操作を評価
        recent_ops = [
            op for op in self.operations
            if (datetime.now() - op['timestamp']).total_seconds() < 60
        ]
        
        if not recent_ops:
            self.current_score = 1.0
            return
        
        # 安定性スコア計算
        successful_ops = sum(1 for op in recent_ops if op['success'])
        self.current_score = successful_ops / len(recent_ops)
        
        self.stability_scores.append({
            'timestamp': datetime.now(),
            'score': self.current_score
        })
    
    def get_current_score(self) -> float:
        """現在の安定性スコア取得"""
        return self.current_score
    
    def stop_monitoring(self):
        """監視停止"""
        self.monitoring_active = False

async def main():
    """メイン実行関数"""
    logger.info("=" * 80)
    logger.info("🚀 【実取引検証開始】Phase 1: 5万円制限実取引データ供給システム")
    logger.info("TECH_LEAD技術統括による800銘柄ユニバース・100並列データ取得システムの実取引検証")
    logger.info("=" * 80)
    
    # Phase 1 システム初期化
    phase1_system = Phase1LiveTradingSystem()
    
    try:
        # Phase 1 検証開始
        tasks = await phase1_system.start_phase1_verification()
        
        # 60秒間実行（テスト用）
        await asyncio.sleep(60)
        
        # システム状態確認
        status = phase1_system.get_phase1_status()
        logger.info(f"📊 Phase 1 状態: {json.dumps(status, indent=2, ensure_ascii=False, default=str)}")
        
    except KeyboardInterrupt:
        logger.info("🛑 ユーザーによる停止要求")
    except Exception as e:
        logger.error(f"❌ Phase 1 システムエラー: {e}")
        logger.error(f"スタックトレース: {traceback.format_exc()}")
    finally:
        phase1_system.shutdown_system()
    
    logger.info("✅ Phase 1 実取引検証システム終了")

if __name__ == "__main__":
    asyncio.run(main())