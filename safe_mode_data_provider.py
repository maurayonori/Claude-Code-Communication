#!/usr/bin/env python3
"""
データ取得機能の安全モード移行システム
緊急事態時のシステム安定性確保のための安全モード実装
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
import json
from dataclasses import dataclass, field
import threading
from queue import Queue, Empty
import pandas as pd

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SafetyMode(Enum):
    """安全モード定義"""
    NORMAL = "normal"          # 通常動作
    SAFE = "safe"              # 安全モード
    EMERGENCY = "emergency"    # 緊急モード
    MAINTENANCE = "maintenance" # メンテナンスモード

class DataSourceStatus(Enum):
    """データソース状態"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"

@dataclass
class SafeModeConfig:
    """安全モード設定"""
    max_concurrent_requests: int = 5  # 通常50→5に制限
    request_timeout: int = 10         # タイムアウト短縮
    retry_attempts: int = 2           # リトライ回数削減
    cache_duration: int = 300         # キャッシュ期間延長
    enable_fallback: bool = True      # フォールバック有効
    health_check_interval: int = 60   # ヘルスチェック間隔
    circuit_breaker_enabled: bool = True  # サーキットブレーカー有効
    error_threshold: int = 5          # エラー閾値
    recovery_timeout: int = 300       # 回復タイムアウト

@dataclass
class DataSourceHealth:
    """データソース健全性"""
    source_name: str
    status: DataSourceStatus
    last_success: Optional[datetime] = None
    error_count: int = 0
    total_requests: int = 0
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    last_error: Optional[str] = None
    
    def calculate_success_rate(self):
        """成功率計算"""
        if self.total_requests == 0:
            return 0.0
        return (self.total_requests - self.error_count) / self.total_requests * 100

class SafeModeDataProvider:
    """安全モード対応データプロバイダー"""
    
    def __init__(self, config: SafeModeConfig = None):
        self.config = config or SafeModeConfig()
        self.logger = logger
        self.current_mode = SafetyMode.NORMAL
        
        # 健全性監視
        self.source_health = {
            'yahoo_finance': DataSourceHealth('yahoo_finance', DataSourceStatus.HEALTHY),
            'kabu_api': DataSourceHealth('kabu_api', DataSourceStatus.HEALTHY),
            'fallback': DataSourceHealth('fallback', DataSourceStatus.HEALTHY)
        }
        
        # サーキットブレーカー状態
        self.circuit_breaker = {
            'yahoo_finance': {'open': False, 'failure_count': 0, 'last_failure': None},
            'kabu_api': {'open': False, 'failure_count': 0, 'last_failure': None}
        }
        
        # 統計情報
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'fallback_used': 0,
            'mode_changes': 0
        }
        
        # キャッシュ
        self.cache = {}
        self.cache_lock = threading.Lock()
        
        # リクエスト制限
        self.request_semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        
        # ヘルスチェック
        self.health_check_running = False
        self.health_check_task = None
        
        self.logger.info(f"SafeModeDataProvider初期化完了: モード={self.current_mode.value}")
    
    def activate_safe_mode(self):
        """安全モードの有効化"""
        self.logger.warning("🔒 安全モード有効化")
        self.current_mode = SafetyMode.SAFE
        self.stats['mode_changes'] += 1
        
        # 設定の更新
        self.config.max_concurrent_requests = 3
        self.config.request_timeout = 5
        self.config.retry_attempts = 1
        self.config.cache_duration = 600  # 10分
        
        # セマフォの再設定
        self.request_semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
    
    def activate_emergency_mode(self):
        """緊急モードの有効化"""
        self.logger.error("🚨 緊急モード有効化")
        self.current_mode = SafetyMode.EMERGENCY
        self.stats['mode_changes'] += 1
        
        # 最小限の設定
        self.config.max_concurrent_requests = 1
        self.config.request_timeout = 3
        self.config.retry_attempts = 0
        self.config.cache_duration = 1800  # 30分
        
        # セマフォの再設定
        self.request_semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
    
    def deactivate_safe_mode(self):
        """安全モードの無効化"""
        self.logger.info("🔓 通常モードに復帰")
        self.current_mode = SafetyMode.NORMAL
        self.stats['mode_changes'] += 1
        
        # 通常設定に復帰
        self.config.max_concurrent_requests = 50
        self.config.request_timeout = 30
        self.config.retry_attempts = 3
        self.config.cache_duration = 300
        
        # セマフォの再設定
        self.request_semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
    
    def check_circuit_breaker(self, source: str) -> bool:
        """サーキットブレーカーチェック"""
        if not self.config.circuit_breaker_enabled:
            return False
            
        breaker = self.circuit_breaker.get(source, {})
        
        if breaker.get('open', False):
            # 回復時間チェック
            if breaker.get('last_failure'):
                time_since_failure = (datetime.now() - breaker['last_failure']).total_seconds()
                if time_since_failure > self.config.recovery_timeout:
                    # 回復試行
                    breaker['open'] = False
                    breaker['failure_count'] = 0
                    self.logger.info(f"サーキットブレーカー回復: {source}")
                    return False
            return True
        
        return False
    
    def record_failure(self, source: str, error: str):
        """失敗記録"""
        if source in self.circuit_breaker:
            breaker = self.circuit_breaker[source]
            breaker['failure_count'] += 1
            breaker['last_failure'] = datetime.now()
            
            # 閾値チェック
            if breaker['failure_count'] >= self.config.error_threshold:
                breaker['open'] = True
                self.logger.warning(f"サーキットブレーカー開放: {source}")
                
                # 安全モード自動有効化
                if self.current_mode == SafetyMode.NORMAL:
                    self.activate_safe_mode()
        
        # 健全性更新
        if source in self.source_health:
            health = self.source_health[source]
            health.error_count += 1
            health.last_error = error
            health.success_rate = health.calculate_success_rate()
            
            # 状態更新
            if health.success_rate < 50:
                health.status = DataSourceStatus.UNHEALTHY
            elif health.success_rate < 80:
                health.status = DataSourceStatus.DEGRADED
    
    def record_success(self, source: str, response_time: float):
        """成功記録"""
        if source in self.source_health:
            health = self.source_health[source]
            health.total_requests += 1
            health.last_success = datetime.now()
            health.success_rate = health.calculate_success_rate()
            
            # 平均応答時間更新
            if health.avg_response_time == 0:
                health.avg_response_time = response_time
            else:
                health.avg_response_time = (health.avg_response_time * 0.9) + (response_time * 0.1)
            
            # 状態更新
            if health.success_rate >= 95:
                health.status = DataSourceStatus.HEALTHY
            elif health.success_rate >= 80:
                health.status = DataSourceStatus.DEGRADED
    
    def get_cached_data(self, cache_key: str) -> Optional[Dict]:
        """キャッシュデータ取得"""
        with self.cache_lock:
            if cache_key in self.cache:
                entry = self.cache[cache_key]
                if time.time() - entry['timestamp'] < self.config.cache_duration:
                    self.stats['cache_hits'] += 1
                    return entry['data']
                else:
                    del self.cache[cache_key]
        return None
    
    def cache_data(self, cache_key: str, data: Dict):
        """データキャッシュ"""
        with self.cache_lock:
            self.cache[cache_key] = {
                'data': data,
                'timestamp': time.time()
            }
            
            # キャッシュサイズ制限
            if len(self.cache) > 1000:
                # 古いエントリを削除
                oldest_keys = sorted(self.cache.keys(), 
                                   key=lambda k: self.cache[k]['timestamp'])[:100]
                for key in oldest_keys:
                    del self.cache[key]
    
    async def safe_fetch_data(self, symbol: str, source: str = 'yahoo_finance') -> Optional[Dict]:
        """安全なデータ取得"""
        self.stats['total_requests'] += 1
        
        # キャッシュチェック
        cache_key = f"{symbol}_{source}_{self.current_mode.value}"
        cached_data = self.get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        # サーキットブレーカーチェック
        if self.check_circuit_breaker(source):
            if self.config.enable_fallback:
                return await self._fetch_fallback_data(symbol)
            else:
                self.stats['failed_requests'] += 1
                return None
        
        # セマフォによる同時実行制限
        async with self.request_semaphore:
            try:
                start_time = time.time()
                
                # タイムアウト付きデータ取得
                data = await asyncio.wait_for(
                    self._fetch_from_source(symbol, source),
                    timeout=self.config.request_timeout
                )
                
                response_time = time.time() - start_time
                
                if data:
                    self.record_success(source, response_time)
                    self.cache_data(cache_key, data)
                    self.stats['successful_requests'] += 1
                    return data
                else:
                    self.record_failure(source, "Empty response")
                    self.stats['failed_requests'] += 1
                    
                    if self.config.enable_fallback:
                        return await self._fetch_fallback_data(symbol)
                    
            except asyncio.TimeoutError:
                self.record_failure(source, "Timeout")
                self.stats['failed_requests'] += 1
                self.logger.warning(f"データ取得タイムアウト: {symbol} from {source}")
                
                if self.config.enable_fallback:
                    return await self._fetch_fallback_data(symbol)
                    
            except Exception as e:
                self.record_failure(source, str(e))
                self.stats['failed_requests'] += 1
                self.logger.error(f"データ取得エラー: {symbol} from {source} - {e}")
                
                if self.config.enable_fallback:
                    return await self._fetch_fallback_data(symbol)
        
        return None
    
    async def _fetch_from_source(self, symbol: str, source: str) -> Optional[Dict]:
        """ソースからのデータ取得"""
        if source == 'yahoo_finance':
            return await self._fetch_yahoo_data(symbol)
        elif source == 'kabu_api':
            return await self._fetch_kabu_data(symbol)
        else:
            return None
    
    async def _fetch_yahoo_data(self, symbol: str) -> Optional[Dict]:
        """Yahoo Financeからのデータ取得"""
        try:
            # 簡素化されたデータ取得
            import yfinance as yf
            
            ticker = yf.Ticker(f"{symbol}.T")
            info = ticker.info
            
            if info:
                return {
                    'symbol': symbol,
                    'price': info.get('currentPrice', 0),
                    'volume': info.get('volume', 0),
                    'source': 'yahoo_finance',
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            self.logger.error(f"Yahoo Financeエラー: {e}")
        
        return None
    
    async def _fetch_kabu_data(self, symbol: str) -> Optional[Dict]:
        """kabu APIからのデータ取得"""
        try:
            # kabu APIの簡素化実装
            return {
                'symbol': symbol,
                'price': 2500,  # ダミーデータ
                'volume': 1000000,
                'source': 'kabu_api',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"kabu APIエラー: {e}")
        
        return None
    
    async def _fetch_fallback_data(self, symbol: str) -> Optional[Dict]:
        """フォールバックデータ取得"""
        self.stats['fallback_used'] += 1
        
        # 最小限のフォールバックデータ
        return {
            'symbol': symbol,
            'price': 1000,  # デフォルト価格
            'volume': 100000,
            'source': 'fallback',
            'timestamp': datetime.now().isoformat(),
            'is_fallback': True
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """システム状態取得"""
        return {
            'current_mode': self.current_mode.value,
            'config': {
                'max_concurrent_requests': self.config.max_concurrent_requests,
                'request_timeout': self.config.request_timeout,
                'retry_attempts': self.config.retry_attempts,
                'cache_duration': self.config.cache_duration
            },
            'source_health': {
                name: {
                    'status': health.status.value,
                    'success_rate': health.success_rate,
                    'error_count': health.error_count,
                    'total_requests': health.total_requests,
                    'avg_response_time': health.avg_response_time,
                    'last_success': health.last_success.isoformat() if health.last_success else None
                }
                for name, health in self.source_health.items()
            },
            'circuit_breaker': {
                name: {
                    'open': breaker.get('open', False),
                    'failure_count': breaker.get('failure_count', 0)
                }
                for name, breaker in self.circuit_breaker.items()
            },
            'stats': self.stats,
            'cache_size': len(self.cache)
        }
    
    def start_health_monitoring(self):
        """ヘルスモニタリング開始"""
        if not self.health_check_running:
            self.health_check_running = True
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            self.logger.info("ヘルスモニタリング開始")
    
    def stop_health_monitoring(self):
        """ヘルスモニタリング停止"""
        if self.health_check_running:
            self.health_check_running = False
            if self.health_check_task:
                self.health_check_task.cancel()
            self.logger.info("ヘルスモニタリング停止")
    
    async def _health_check_loop(self):
        """ヘルスチェックループ"""
        while self.health_check_running:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"ヘルスチェックエラー: {e}")
                await asyncio.sleep(60)  # エラー時は1分待機
    
    async def _perform_health_check(self):
        """ヘルスチェック実行"""
        # 全体的な健全性評価
        healthy_sources = sum(1 for health in self.source_health.values() 
                            if health.status == DataSourceStatus.HEALTHY)
        
        total_sources = len(self.source_health)
        health_ratio = healthy_sources / total_sources
        
        # モード自動切り替え
        if health_ratio < 0.5 and self.current_mode == SafetyMode.NORMAL:
            self.activate_safe_mode()
        elif health_ratio < 0.3 and self.current_mode == SafetyMode.SAFE:
            self.activate_emergency_mode()
        elif health_ratio > 0.8 and self.current_mode != SafetyMode.NORMAL:
            self.deactivate_safe_mode()
        
        self.logger.debug(f"ヘルスチェック完了: {healthy_sources}/{total_sources} ソース正常")

async def test_safe_mode_system():
    """安全モードシステムのテスト"""
    logger.info("=== 安全モードシステムテスト開始 ===")
    
    # 安全モードプロバイダーの初期化
    provider = SafeModeDataProvider()
    
    # ヘルスモニタリング開始
    provider.start_health_monitoring()
    
    try:
        # 通常モードでのテスト
        logger.info("通常モードでのデータ取得テスト")
        data = await provider.safe_fetch_data("7203", "yahoo_finance")
        logger.info(f"取得データ: {data}")
        
        # 安全モードの手動有効化
        provider.activate_safe_mode()
        
        # 安全モードでのテスト
        logger.info("安全モードでのデータ取得テスト")
        data = await provider.safe_fetch_data("4063", "yahoo_finance")
        logger.info(f"取得データ: {data}")
        
        # 緊急モードの手動有効化
        provider.activate_emergency_mode()
        
        # 緊急モードでのテスト
        logger.info("緊急モードでのデータ取得テスト")
        data = await provider.safe_fetch_data("6758", "yahoo_finance")
        logger.info(f"取得データ: {data}")
        
        # システム状態の確認
        status = provider.get_system_status()
        logger.info(f"システム状態: {json.dumps(status, indent=2, ensure_ascii=False)}")
        
    finally:
        # ヘルスモニタリング停止
        provider.stop_health_monitoring()
    
    logger.info("=== 安全モードシステムテスト完了 ===")

def main():
    """メイン実行関数"""
    logger.info("データ取得機能の安全モード移行システム")
    logger.info("=" * 60)
    
    # 非同期テストの実行
    asyncio.run(test_safe_mode_system())
    
    logger.info("✅ 安全モード移行完了")

if __name__ == "__main__":
    main()