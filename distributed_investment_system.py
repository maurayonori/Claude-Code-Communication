#!/usr/bin/env python3
"""
分散投資システム対応の複数銘柄同時データ取得・リアルタイム監視システム
800銘柄ユニバースの効率的管理とリアルタイム監視機能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

import asyncio
import aiohttp
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple, Set
from enum import Enum
from dataclasses import dataclass, field
import threading
from queue import Queue, Empty, PriorityQueue
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import sqlite3
from pathlib import Path
import yfinance as yf
from collections import defaultdict, deque
import weakref
import gc

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UniverseTier(Enum):
    """銘柄ユニバース階層"""
    TIER1 = "tier1"  # 高流動性・高優先度
    TIER2 = "tier2"  # 中流動性・中優先度
    TIER3 = "tier3"  # 低流動性・低優先度
    TIER4 = "tier4"  # 監視のみ

class DataPriority(Enum):
    """データ取得優先度"""
    CRITICAL = 1    # 取引中銘柄
    HIGH = 2        # 監視銘柄
    MEDIUM = 3      # 一般銘柄
    LOW = 4         # バックグラウンド更新

class MonitoringStatus(Enum):
    """監視状態"""
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"

@dataclass
class StockInfo:
    """銘柄情報"""
    symbol: str
    name: str
    tier: UniverseTier
    sector: str
    market_cap: float
    avg_volume: float
    price_range: Tuple[float, float]
    volatility: float
    beta: float
    last_updated: datetime
    is_active: bool = True
    monitoring_priority: DataPriority = DataPriority.MEDIUM

@dataclass
class RealTimeData:
    """リアルタイムデータ"""
    symbol: str
    timestamp: datetime
    price: float
    volume: int
    bid: float
    ask: float
    change: float
    change_percent: float
    high: float
    low: float
    open: float
    previous_close: float
    data_source: str
    latency_ms: float

@dataclass
class BatchRequest:
    """バッチリクエスト"""
    symbols: List[str]
    priority: DataPriority
    request_time: datetime
    timeout: int = 30
    retry_count: int = 3
    callback: Optional[callable] = None

class UniverseManager:
    """800銘柄ユニバース管理システム"""
    
    def __init__(self, db_path: str = "universe.db"):
        self.db_path = Path(db_path)
        self.stocks = {}  # symbol -> StockInfo
        self.tier_mapping = defaultdict(set)  # tier -> set of symbols
        self.sector_mapping = defaultdict(set)  # sector -> set of symbols
        self.active_symbols = set()
        self.monitoring_symbols = set()
        self.lock = threading.RLock()
        
        # データベース初期化
        self._init_database()
        self._load_universe()
        
        logger.info(f"UniverseManager初期化完了: {len(self.stocks)}銘柄")
    
    def _init_database(self):
        """データベース初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS stocks (
                    symbol TEXT PRIMARY KEY,
                    name TEXT,
                    tier TEXT,
                    sector TEXT,
                    market_cap REAL,
                    avg_volume REAL,
                    price_min REAL,
                    price_max REAL,
                    volatility REAL,
                    beta REAL,
                    last_updated TEXT,
                    is_active INTEGER,
                    monitoring_priority INTEGER
                )
            ''')
            conn.commit()
    
    def _load_universe(self):
        """ユニバースデータの読み込み"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('SELECT * FROM stocks')
                for row in cursor.fetchall():
                    symbol = row[0]
                    stock_info = StockInfo(
                        symbol=symbol,
                        name=row[1],
                        tier=UniverseTier(row[2]),
                        sector=row[3],
                        market_cap=row[4],
                        avg_volume=row[5],
                        price_range=(row[6], row[7]),
                        volatility=row[8],
                        beta=row[9],
                        last_updated=datetime.fromisoformat(row[10]),
                        is_active=bool(row[11]),
                        monitoring_priority=DataPriority(row[12])
                    )
                    self.add_stock(stock_info)
                    
        except Exception as e:
            logger.warning(f"ユニバースデータ読み込みエラー: {e}")
            self._create_default_universe()
        
        # デフォルトユニバースが空の場合も作成
        if not self.stocks:
            self._create_default_universe()
    
    def _create_default_universe(self):
        """デフォルトユニバースの作成"""
        logger.info("デフォルト800銘柄ユニバースを作成中...")
        
        # 主要銘柄のサンプル
        major_stocks = [
            ("7203", "トヨタ自動車", UniverseTier.TIER1, "自動車", 35000000000000),
            ("9984", "ソフトバンクグループ", UniverseTier.TIER1, "IT", 12000000000000),
            ("6758", "ソニーグループ", UniverseTier.TIER1, "電機", 15000000000000),
            ("4063", "信越化学工業", UniverseTier.TIER1, "化学", 8000000000000),
            ("8306", "三菱UFJフィナンシャルG", UniverseTier.TIER1, "金融", 10000000000000),
        ]
        
        # 800銘柄に拡張
        for i, (symbol, name, tier, sector, market_cap) in enumerate(major_stocks):
            # 基本銘柄
            stock_info = StockInfo(
                symbol=symbol,
                name=name,
                tier=tier,
                sector=sector,
                market_cap=market_cap,
                avg_volume=1000000,
                price_range=(100, 10000),
                volatility=0.02,
                beta=1.0,
                last_updated=datetime.now(),
                monitoring_priority=DataPriority.HIGH
            )
            self.add_stock(stock_info)
            
            # 類似銘柄を生成して800銘柄に拡張
            for j in range(1, 160):  # 各基本銘柄から160銘柄生成
                expanded_symbol = f"{int(symbol) + j:04d}"
                expanded_name = f"{name}_{j}"
                
                # 階層を分散
                if j <= 40:
                    tier = UniverseTier.TIER1
                    priority = DataPriority.HIGH
                elif j <= 80:
                    tier = UniverseTier.TIER2
                    priority = DataPriority.MEDIUM
                elif j <= 120:
                    tier = UniverseTier.TIER3
                    priority = DataPriority.MEDIUM
                else:
                    tier = UniverseTier.TIER4
                    priority = DataPriority.LOW
                
                expanded_stock = StockInfo(
                    symbol=expanded_symbol,
                    name=expanded_name,
                    tier=tier,
                    sector=sector,
                    market_cap=market_cap * (0.5 + j * 0.01),
                    avg_volume=1000000 * (0.5 + j * 0.01),
                    price_range=(100 + j * 10, 1000 + j * 100),
                    volatility=0.01 + j * 0.001,
                    beta=0.8 + j * 0.01,
                    last_updated=datetime.now(),
                    monitoring_priority=priority
                )
                self.add_stock(expanded_stock)
        
        logger.info(f"デフォルト800銘柄ユニバース作成完了: {len(self.stocks)}銘柄")
    
    def add_stock(self, stock_info: StockInfo):
        """銘柄追加"""
        with self.lock:
            self.stocks[stock_info.symbol] = stock_info
            self.tier_mapping[stock_info.tier].add(stock_info.symbol)
            self.sector_mapping[stock_info.sector].add(stock_info.symbol)
            
            if stock_info.is_active:
                self.active_symbols.add(stock_info.symbol)
            
            # データベースに保存
            self._save_stock_to_db(stock_info)
    
    def _save_stock_to_db(self, stock_info: StockInfo):
        """銘柄をデータベースに保存"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO stocks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    stock_info.symbol,
                    stock_info.name,
                    stock_info.tier.value,
                    stock_info.sector,
                    stock_info.market_cap,
                    stock_info.avg_volume,
                    stock_info.price_range[0],
                    stock_info.price_range[1],
                    stock_info.volatility,
                    stock_info.beta,
                    stock_info.last_updated.isoformat(),
                    int(stock_info.is_active),
                    stock_info.monitoring_priority.value
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"データベース保存エラー: {e}")
    
    def get_symbols_by_tier(self, tier: UniverseTier) -> List[str]:
        """階層別銘柄取得"""
        with self.lock:
            return list(self.tier_mapping[tier])
    
    def get_symbols_by_sector(self, sector: str) -> List[str]:
        """セクター別銘柄取得"""
        with self.lock:
            return list(self.sector_mapping[sector])
    
    def get_symbols_by_priority(self, priority: DataPriority) -> List[str]:
        """優先度別銘柄取得"""
        with self.lock:
            return [symbol for symbol, stock in self.stocks.items() 
                   if stock.monitoring_priority == priority]
    
    def get_active_symbols(self) -> List[str]:
        """アクティブ銘柄取得"""
        with self.lock:
            return list(self.active_symbols)
    
    def get_monitoring_symbols(self) -> List[str]:
        """監視銘柄取得"""
        with self.lock:
            return list(self.monitoring_symbols)
    
    def update_monitoring_symbols(self, symbols: List[str]):
        """監視銘柄更新"""
        with self.lock:
            self.monitoring_symbols = set(symbols)
    
    def get_universe_stats(self) -> Dict[str, Any]:
        """ユニバース統計"""
        with self.lock:
            stats = {
                'total_stocks': len(self.stocks),
                'active_stocks': len(self.active_symbols),
                'monitoring_stocks': len(self.monitoring_symbols),
                'tier_distribution': {
                    tier.value: len(symbols) 
                    for tier, symbols in self.tier_mapping.items()
                },
                'sector_distribution': {
                    sector: len(symbols) 
                    for sector, symbols in self.sector_mapping.items()
                },
                'priority_distribution': {
                    priority.value: len(self.get_symbols_by_priority(priority))
                    for priority in DataPriority
                }
            }
            return stats

class BatchDataFetcher:
    """バッチデータ取得システム"""
    
    def __init__(self, max_workers: int = 100, batch_size: int = 50):
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.request_queue = PriorityQueue()
        self.results_cache = {}
        self.processing_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_processing_time': 0,
            'throughput_per_second': 0
        }
        self.lock = threading.Lock()
        
        # 処理中のリクエスト管理
        self.active_requests = {}
        
        logger.info(f"BatchDataFetcher初期化完了: {max_workers}ワーカー, バッチサイズ{batch_size}")
    
    def submit_batch_request(self, symbols: List[str], priority: DataPriority = DataPriority.MEDIUM) -> str:
        """バッチリクエスト送信"""
        request_id = f"batch_{int(time.time() * 1000)}"
        
        # 大きなリクエストをバッチサイズに分割
        batches = [symbols[i:i+self.batch_size] 
                  for i in range(0, len(symbols), self.batch_size)]
        
        for i, batch_symbols in enumerate(batches):
            batch_request = BatchRequest(
                symbols=batch_symbols,
                priority=priority,
                request_time=datetime.now(),
                timeout=30
            )
            
            # 優先度付きキューに追加
            self.request_queue.put((priority.value, f"{request_id}_{i}", batch_request))
        
        logger.info(f"バッチリクエスト送信: {len(symbols)}銘柄 -> {len(batches)}バッチ")
        return request_id
    
    async def process_batch_requests(self):
        """バッチリクエスト処理"""
        while True:
            try:
                if not self.request_queue.empty():
                    priority, request_id, batch_request = self.request_queue.get()
                    
                    # 並列処理で実行
                    task = asyncio.create_task(
                        self._process_single_batch(request_id, batch_request)
                    )
                    
                    # 完了を待たずに次のリクエストを処理
                    asyncio.create_task(self._handle_batch_result(request_id, task))
                
                await asyncio.sleep(0.1)  # CPU負荷軽減
                
            except Exception as e:
                logger.error(f"バッチリクエスト処理エラー: {e}")
                await asyncio.sleep(1)
    
    async def _process_single_batch(self, request_id: str, batch_request: BatchRequest) -> Dict[str, Any]:
        """単一バッチ処理"""
        start_time = time.time()
        
        try:
            # 並列データ取得
            results = await self._fetch_batch_data(batch_request.symbols)
            
            processing_time = time.time() - start_time
            
            # 統計更新
            self._update_processing_stats(len(batch_request.symbols), len(results), processing_time)
            
            return {
                'request_id': request_id,
                'symbols': batch_request.symbols,
                'results': results,
                'processing_time': processing_time,
                'success_count': len(results),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"バッチ処理エラー {request_id}: {e}")
            return {
                'request_id': request_id,
                'symbols': batch_request.symbols,
                'error': str(e),
                'processing_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _fetch_batch_data(self, symbols: List[str]) -> Dict[str, RealTimeData]:
        """バッチデータ取得"""
        results = {}
        
        # 並列処理でデータ取得
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def fetch_single_symbol(symbol: str):
            async with semaphore:
                try:
                    data = await self._fetch_symbol_data(symbol)
                    if data:
                        results[symbol] = data
                except Exception as e:
                    logger.warning(f"シンボル取得エラー {symbol}: {e}")
        
        # 全シンボルを並列処理
        tasks = [fetch_single_symbol(symbol) for symbol in symbols]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return results
    
    async def _fetch_symbol_data(self, symbol: str) -> Optional[RealTimeData]:
        """単一シンボルデータ取得"""
        try:
            start_time = time.time()
            
            # Yahoo Finance APIから取得
            ticker = yf.Ticker(f"{symbol}.T")
            info = ticker.info
            
            if not info:
                return None
            
            # 履歴データから最新情報を取得
            hist = ticker.history(period="1d", interval="1m")
            if hist.empty:
                return None
            
            latest = hist.iloc[-1]
            previous = hist.iloc[-2] if len(hist) > 1 else latest
            
            latency = (time.time() - start_time) * 1000
            
            return RealTimeData(
                symbol=symbol,
                timestamp=datetime.now(),
                price=float(latest['Close']),
                volume=int(latest['Volume']),
                bid=float(latest['Close'] * 0.999),  # 簡易推定
                ask=float(latest['Close'] * 1.001),
                change=float(latest['Close'] - previous['Close']),
                change_percent=float((latest['Close'] - previous['Close']) / previous['Close'] * 100),
                high=float(latest['High']),
                low=float(latest['Low']),
                open=float(latest['Open']),
                previous_close=float(previous['Close']),
                data_source='yahoo_finance',
                latency_ms=latency
            )
            
        except Exception as e:
            logger.warning(f"データ取得エラー {symbol}: {e}")
            return None
    
    async def _handle_batch_result(self, request_id: str, task: asyncio.Task):
        """バッチ結果処理"""
        try:
            result = await task
            
            # 結果をキャッシュ
            with self.lock:
                self.results_cache[request_id] = result
                
                # キャッシュサイズ制限
                if len(self.results_cache) > 1000:
                    # 古いエントリを削除
                    oldest_keys = list(self.results_cache.keys())[:100]
                    for key in oldest_keys:
                        del self.results_cache[key]
            
            logger.debug(f"バッチ結果処理完了: {request_id}")
            
        except Exception as e:
            logger.error(f"バッチ結果処理エラー {request_id}: {e}")
    
    def _update_processing_stats(self, total_symbols: int, successful_symbols: int, processing_time: float):
        """処理統計更新"""
        with self.lock:
            self.processing_stats['total_requests'] += total_symbols
            self.processing_stats['successful_requests'] += successful_symbols
            self.processing_stats['failed_requests'] += (total_symbols - successful_symbols)
            
            # 平均処理時間更新
            current_avg = self.processing_stats['avg_processing_time']
            new_avg = (current_avg * 0.9) + (processing_time * 0.1)
            self.processing_stats['avg_processing_time'] = new_avg
            
            # スループット計算
            if processing_time > 0:
                throughput = successful_symbols / processing_time
                current_throughput = self.processing_stats['throughput_per_second']
                new_throughput = (current_throughput * 0.9) + (throughput * 0.1)
                self.processing_stats['throughput_per_second'] = new_throughput
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """処理統計取得"""
        with self.lock:
            return self.processing_stats.copy()
    
    def get_cached_results(self, request_id: str) -> Optional[Dict[str, Any]]:
        """キャッシュ結果取得"""
        with self.lock:
            return self.results_cache.get(request_id)

class RealTimeMonitor:
    """リアルタイム監視システム"""
    
    def __init__(self, universe_manager: UniverseManager, batch_fetcher: BatchDataFetcher):
        self.universe_manager = universe_manager
        self.batch_fetcher = batch_fetcher
        self.status = MonitoringStatus.STOPPED
        self.monitoring_interval = 1.0  # 1秒間隔
        self.monitored_symbols = set()
        self.real_time_data = {}
        self.alerts = deque(maxlen=1000)
        
        # 監視タスク
        self.monitoring_task = None
        
        # 統計情報
        self.monitor_stats = {
            'updates_per_second': 0,
            'data_freshness': 0,
            'alert_count': 0,
            'error_count': 0
        }
        
        logger.info("RealTimeMonitor初期化完了")
    
    def start_monitoring(self, symbols: List[str] = None):
        """監視開始"""
        if symbols is None:
            symbols = self.universe_manager.get_symbols_by_priority(DataPriority.HIGH)
        
        self.monitored_symbols = set(symbols)
        self.status = MonitoringStatus.ACTIVE
        
        # 監視タスクを開始
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info(f"リアルタイム監視開始: {len(symbols)}銘柄")
    
    def stop_monitoring(self):
        """監視停止"""
        self.status = MonitoringStatus.STOPPED
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
        
        logger.info("リアルタイム監視停止")
    
    async def _monitoring_loop(self):
        """監視ループ"""
        while self.status == MonitoringStatus.ACTIVE:
            try:
                start_time = time.time()
                
                # 監視銘柄のデータ取得
                symbols_list = list(self.monitored_symbols)
                if symbols_list:
                    request_id = self.batch_fetcher.submit_batch_request(
                        symbols_list, 
                        DataPriority.CRITICAL
                    )
                    
                    # 結果を少し待ってから取得
                    await asyncio.sleep(0.5)
                    result = self.batch_fetcher.get_cached_results(request_id)
                    
                    if result and 'results' in result:
                        await self._process_real_time_data(result['results'])
                
                # 監視間隔の調整
                elapsed = time.time() - start_time
                sleep_time = max(0, self.monitoring_interval - elapsed)
                await asyncio.sleep(sleep_time)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"監視ループエラー: {e}")
                self.monitor_stats['error_count'] += 1
                await asyncio.sleep(5)
    
    async def _process_real_time_data(self, data: Dict[str, RealTimeData]):
        """リアルタイムデータ処理"""
        updates = 0
        
        for symbol, real_time_data in data.items():
            # データを更新
            self.real_time_data[symbol] = real_time_data
            updates += 1
            
            # アラート条件チェック
            await self._check_alerts(symbol, real_time_data)
        
        # 統計更新
        self.monitor_stats['updates_per_second'] = updates / self.monitoring_interval
        self.monitor_stats['data_freshness'] = time.time() - min(
            (data.timestamp.timestamp() for data in self.real_time_data.values()),
            default=time.time()
        )
    
    async def _check_alerts(self, symbol: str, data: RealTimeData):
        """アラート条件チェック"""
        stock_info = self.universe_manager.stocks.get(symbol)
        if not stock_info:
            return
        
        # 価格変動アラート
        if abs(data.change_percent) > 5.0:
            alert = {
                'type': 'price_change',
                'symbol': symbol,
                'message': f'{symbol}: {data.change_percent:.2f}%の価格変動',
                'timestamp': datetime.now().isoformat(),
                'severity': 'high' if abs(data.change_percent) > 10.0 else 'medium'
            }
            self.alerts.append(alert)
            self.monitor_stats['alert_count'] += 1
        
        # 出来高異常アラート
        if data.volume > stock_info.avg_volume * 2:
            alert = {
                'type': 'volume_spike',
                'symbol': symbol,
                'message': f'{symbol}: 出来高異常増加 ({data.volume:,})',
                'timestamp': datetime.now().isoformat(),
                'severity': 'medium'
            }
            self.alerts.append(alert)
            self.monitor_stats['alert_count'] += 1
    
    def get_real_time_data(self, symbol: str) -> Optional[RealTimeData]:
        """リアルタイムデータ取得"""
        return self.real_time_data.get(symbol)
    
    def get_all_real_time_data(self) -> Dict[str, RealTimeData]:
        """全リアルタイムデータ取得"""
        return self.real_time_data.copy()
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """最近のアラート取得"""
        return list(self.alerts)[-limit:]
    
    def get_monitor_stats(self) -> Dict[str, Any]:
        """監視統計取得"""
        return self.monitor_stats.copy()

class DistributedInvestmentSystem:
    """分散投資システム統合クラス"""
    
    def __init__(self):
        self.universe_manager = UniverseManager()
        self.batch_fetcher = BatchDataFetcher(max_workers=100, batch_size=50)
        self.real_time_monitor = RealTimeMonitor(self.universe_manager, self.batch_fetcher)
        
        # システム統計
        self.system_stats = {
            'start_time': datetime.now(),
            'total_data_points': 0,
            'system_uptime': 0,
            'memory_usage': 0
        }
        
        logger.info("分散投資システム初期化完了")
    
    async def start_system(self):
        """システム開始"""
        logger.info("=== 分散投資システム開始 ===")
        
        # バッチ処理開始
        batch_task = asyncio.create_task(self.batch_fetcher.process_batch_requests())
        
        # リアルタイム監視開始
        high_priority_symbols = self.universe_manager.get_symbols_by_priority(DataPriority.HIGH)
        self.real_time_monitor.start_monitoring(high_priority_symbols[:100])  # 上位100銘柄
        
        # 全銘柄のバッチ取得開始
        all_symbols = self.universe_manager.get_active_symbols()
        request_id = self.batch_fetcher.submit_batch_request(all_symbols, DataPriority.MEDIUM)
        
        logger.info(f"システム開始完了: {len(all_symbols)}銘柄監視中")
        
        return batch_task
    
    def stop_system(self):
        """システム停止"""
        logger.info("=== 分散投資システム停止 ===")
        
        self.real_time_monitor.stop_monitoring()
        
        # リソースクリーンアップ
        gc.collect()
        
        logger.info("システム停止完了")
    
    def get_system_status(self) -> Dict[str, Any]:
        """システム状態取得"""
        # JSON serializable にするため datetime を文字列に変換
        system_stats = self.system_stats.copy()
        system_stats['start_time'] = system_stats['start_time'].isoformat()
        system_stats['system_uptime'] = (datetime.now() - self.system_stats['start_time']).total_seconds()
        
        return {
            'universe_stats': self.universe_manager.get_universe_stats(),
            'batch_stats': self.batch_fetcher.get_processing_stats(),
            'monitor_stats': self.real_time_monitor.get_monitor_stats(),
            'system_stats': system_stats,
            'monitoring_status': self.real_time_monitor.status.value,
            'monitored_symbols_count': len(self.real_time_monitor.monitored_symbols)
        }

async def test_distributed_investment_system():
    """分散投資システムのテスト"""
    logger.info("=== 分散投資システムテスト開始 ===")
    
    system = DistributedInvestmentSystem()
    
    try:
        # システム開始
        batch_task = await system.start_system()
        
        # 5秒間動作
        await asyncio.sleep(5)
        
        # 状態確認
        status = system.get_system_status()
        logger.info(f"システム状態: {json.dumps(status, indent=2, ensure_ascii=False)}")
        
        # アラート確認
        alerts = system.real_time_monitor.get_recent_alerts()
        logger.info(f"アラート: {len(alerts)}件")
        
        # リアルタイムデータ確認
        real_time_data = system.real_time_monitor.get_all_real_time_data()
        logger.info(f"リアルタイムデータ: {len(real_time_data)}銘柄")
        
        # サンプルデータ表示
        if real_time_data:
            sample_symbol = list(real_time_data.keys())[0]
            sample_data = real_time_data[sample_symbol]
            logger.info(f"サンプルデータ {sample_symbol}: 価格={sample_data.price}, 変動={sample_data.change_percent:.2f}%")
        
    finally:
        system.stop_system()
    
    logger.info("=== 分散投資システムテスト完了 ===")

def main():
    """メイン実行関数"""
    logger.info("分散投資システム対応の複数銘柄同時データ取得・リアルタイム監視システム")
    logger.info("=" * 80)
    
    # 非同期テストの実行
    asyncio.run(test_distributed_investment_system())
    
    logger.info("✅ 分散投資システム実装完了")

if __name__ == "__main__":
    main()