#!/usr/bin/env python3
"""
並列データ取得システムのTDDテストスイート
50並列データ取得システムの包括的テスト
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from datetime import datetime, timedelta

# テスト対象のインポート
from data.parallel_data_provider import (
    ParallelDataProvider, 
    DataRequest, 
    DataResponse, 
    DataSource,
    ConnectionPool,
    RateLimitManager,
    quick_bulk_fetch
)

class TestDataRequest(unittest.TestCase):
    """DataRequestクラスのテスト"""
    
    def test_data_request_creation(self):
        """DataRequestオブジェクトの作成テスト"""
        request = DataRequest(
            symbol="7203",
            data_type="info",
            period="1d",
            priority=1
        )
        
        self.assertEqual(request.symbol, "7203")
        self.assertEqual(request.data_type, "info")
        self.assertEqual(request.period, "1d")
        self.assertEqual(request.priority, 1)
        self.assertEqual(request.source, DataSource.YAHOO_FINANCE)
    
    def test_data_request_default_values(self):
        """DataRequestデフォルト値テスト"""
        request = DataRequest(symbol="7203", data_type="info")
        
        self.assertEqual(request.period, "5d")
        self.assertEqual(request.interval, "1d")
        self.assertEqual(request.timeout, 30)
        self.assertEqual(request.retry_count, 3)
        self.assertIsNotNone(request.request_id)
        self.assertIsInstance(request.timestamp, datetime)

class TestDataResponse(unittest.TestCase):
    """DataResponseクラスのテスト"""
    
    def test_data_response_creation(self):
        """DataResponseオブジェクトの作成テスト"""
        request = DataRequest(symbol="7203", data_type="info")
        response = DataResponse(
            request=request,
            success=True,
            data={"test": "data"},
            processing_time=0.5
        )
        
        self.assertEqual(response.request, request)
        self.assertTrue(response.success)
        self.assertEqual(response.data, {"test": "data"})
        self.assertEqual(response.processing_time, 0.5)
    
    def test_data_response_to_dict(self):
        """DataResponse辞書変換テスト"""
        request = DataRequest(symbol="7203", data_type="info")
        response = DataResponse(
            request=request,
            success=True,
            data={"price": 2500},
            processing_time=0.3
        )
        
        result_dict = response.to_dict()
        
        self.assertEqual(result_dict['symbol'], "7203")
        self.assertTrue(result_dict['success'])
        self.assertEqual(result_dict['data'], {"price": 2500})
        self.assertEqual(result_dict['processing_time'], 0.3)
        self.assertIn('request_id', result_dict)
        self.assertIn('timestamp', result_dict)

class TestConnectionPool(unittest.TestCase):
    """ConnectionPoolクラスのテスト"""
    
    def test_connection_pool_initialization(self):
        """接続プール初期化テスト"""
        pool = ConnectionPool(max_connections=10)
        
        self.assertEqual(pool.max_connections, 10)
        self.assertEqual(pool.active_connections, 0)
        self.assertEqual(pool.connection_queue.qsize(), 10)
    
    def test_connection_acquire_and_release(self):
        """接続取得・解放テスト"""
        pool = ConnectionPool(max_connections=2)
        
        # 接続取得
        self.assertTrue(pool.acquire())
        self.assertEqual(pool.active_connections, 1)
        
        self.assertTrue(pool.acquire())
        self.assertEqual(pool.active_connections, 2)
        
        # 接続プール満杯の場合
        self.assertFalse(pool.acquire())
        
        # 接続解放
        pool.release()
        self.assertEqual(pool.active_connections, 1)
        
        # 再度取得可能
        self.assertTrue(pool.acquire())
        self.assertEqual(pool.active_connections, 2)
    
    def test_connection_pool_status(self):
        """接続プール状態取得テスト"""
        pool = ConnectionPool(max_connections=5)
        pool.acquire()
        pool.acquire()
        
        status = pool.get_status()
        
        self.assertEqual(status['max_connections'], 5)
        self.assertEqual(status['active_connections'], 2)
        self.assertEqual(status['available_connections'], 3)

class TestRateLimitManager(unittest.TestCase):
    """RateLimitManagerクラスのテスト"""
    
    def test_rate_limit_manager_initialization(self):
        """レート制限マネージャー初期化テスト"""
        manager = RateLimitManager()
        
        self.assertEqual(manager.requests_per_second[DataSource.YAHOO_FINANCE], 10)
        self.assertEqual(manager.requests_per_second[DataSource.KABU_STATION], 5)
        self.assertEqual(manager.requests_per_second[DataSource.CUSTOM_API], 20)
    
    def test_rate_limit_check(self):
        """レート制限チェックテスト"""
        manager = RateLimitManager()
        
        # 最初はリクエスト可能
        self.assertTrue(manager.can_make_request(DataSource.YAHOO_FINANCE))
        
        # リクエスト記録
        for _ in range(10):
            manager.record_request(DataSource.YAHOO_FINANCE)
        
        # 制限に達した場合
        self.assertFalse(manager.can_make_request(DataSource.YAHOO_FINANCE))
    
    def test_rate_limit_history_cleanup(self):
        """レート制限履歴クリーンアップテスト"""
        manager = RateLimitManager()
        
        # 大量のリクエストを記録
        for _ in range(150):
            manager.record_request(DataSource.YAHOO_FINANCE)
        
        # 履歴が制限される
        self.assertLessEqual(len(manager.request_history[DataSource.YAHOO_FINANCE]), 100)

class TestParallelDataProvider(unittest.TestCase):
    """ParallelDataProviderクラスのテスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.provider = ParallelDataProvider(max_workers=5, max_connections=10)
    
    def tearDown(self):
        """テストクリーンアップ"""
        self.provider.stop_workers()
    
    def test_provider_initialization(self):
        """プロバイダー初期化テスト"""
        self.assertEqual(self.provider.max_workers, 5)
        self.assertEqual(self.provider.connection_pool.max_connections, 10)
        self.assertIsInstance(self.provider.rate_limit_manager, RateLimitManager)
        self.assertIsInstance(self.provider.stats, dict)
    
    @patch('data.parallel_data_provider.yf.Ticker')
    def test_fetch_yahoo_finance_data(self, mock_ticker):
        """Yahoo Finance データ取得テスト"""
        # モックの設定
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {"shortName": "トヨタ自動車", "currentPrice": 2500}
        mock_ticker.return_value = mock_ticker_instance
        
        # テスト実行
        request = DataRequest(symbol="7203", data_type="info")
        result = self.provider._fetch_yahoo_finance_data(request)
        
        # 検証
        self.assertIn('info', result)
        self.assertEqual(result['info']['shortName'], "トヨタ自動車")
        self.assertEqual(result['info']['currentPrice'], 2500)
    
    @patch('data.parallel_data_provider.yf.Ticker')
    def test_fetch_yahoo_finance_history_data(self, mock_ticker):
        """Yahoo Finance 履歴データ取得テスト"""
        # モックの設定
        mock_ticker_instance = Mock()
        mock_history = Mock()
        mock_history.empty = False
        mock_history.to_dict.return_value = {"Close": {0: 2500, 1: 2600}}
        mock_history.__getitem__.side_effect = lambda key: {
            'Close': type('MockSeries', (), {'iloc': [-1: 2600]})(),
            'Volume': type('MockSeries', (), {'iloc': [-1: 1000000]})(),
            'High': type('MockSeries', (), {'iloc': [-1: 2650]})(),
            'Low': type('MockSeries', (), {'iloc': [-1: 2480]})()
        }[key]
        
        mock_ticker_instance.history.return_value = mock_history
        mock_ticker.return_value = mock_ticker_instance
        
        # テスト実行
        request = DataRequest(symbol="7203", data_type="history")
        result = self.provider._fetch_yahoo_finance_data(request)
        
        # 検証
        self.assertIn('history', result)
        self.assertIn('prices', result['history'])
        self.assertIn('latest_price', result['history'])
    
    def test_single_request_execution(self):
        """単一リクエスト実行テスト"""
        with patch.object(self.provider, '_fetch_data_by_source') as mock_fetch:
            mock_fetch.return_value = {"test": "data"}
            
            request = DataRequest(symbol="7203", data_type="info", timeout=5)
            response = self.provider._execute_single_request(request)
            
            self.assertTrue(response.success)
            self.assertEqual(response.data, {"test": "data"})
            self.assertIsNone(response.error)
            self.assertGreater(response.processing_time, 0)
    
    def test_single_request_execution_with_error(self):
        """単一リクエスト実行エラーテスト"""
        with patch.object(self.provider, '_fetch_data_by_source') as mock_fetch:
            mock_fetch.side_effect = Exception("API Error")
            
            request = DataRequest(symbol="7203", data_type="info", timeout=5)
            response = self.provider._execute_single_request(request)
            
            self.assertFalse(response.success)
            self.assertIsNone(response.data)
            self.assertIn("API Error", response.error)
    
    def test_cache_functionality(self):
        """キャッシュ機能テスト"""
        # データをキャッシュ
        test_data = {"price": 2500}
        cache_key = "7203_info_5d"
        self.provider._cache_data(cache_key, test_data)
        
        # キャッシュから取得
        cached_data = self.provider._get_cached_data(cache_key)
        self.assertEqual(cached_data, test_data)
        
        # キャッシュクリア
        self.provider.clear_cache()
        cached_data = self.provider._get_cached_data(cache_key)
        self.assertIsNone(cached_data)
    
    def test_cache_expiration(self):
        """キャッシュ有効期限テスト"""
        # 短い有効期限を設定
        self.provider.cache_timeout = 0.1
        
        test_data = {"price": 2500}
        cache_key = "7203_info_5d"
        self.provider._cache_data(cache_key, test_data)
        
        # 有効期限内
        cached_data = self.provider._get_cached_data(cache_key)
        self.assertEqual(cached_data, test_data)
        
        # 有効期限切れ
        time.sleep(0.2)
        cached_data = self.provider._get_cached_data(cache_key)
        self.assertIsNone(cached_data)
    
    def test_bulk_fetch_data(self):
        """一括データ取得テスト"""
        symbols = ["7203", "4063", "6758"]
        
        with patch.object(self.provider, '_execute_single_request') as mock_execute:
            # モックレスポンス
            def mock_response(request):
                return DataResponse(
                    request=request,
                    success=True,
                    data={"symbol": request.symbol, "price": 2500},
                    processing_time=0.1
                )
            
            mock_execute.side_effect = mock_response
            
            # テスト実行
            responses = self.provider.bulk_fetch_data(symbols, "info", timeout=30)
            
            # 検証
            self.assertEqual(len(responses), 3)
            for symbol in symbols:
                self.assertIn(symbol, responses)
                self.assertTrue(responses[symbol].success)
                self.assertEqual(responses[symbol].data["symbol"], symbol)
    
    def test_parallel_execution(self):
        """並列実行テスト"""
        requests = [
            DataRequest(symbol="7203", data_type="info"),
            DataRequest(symbol="4063", data_type="info"),
            DataRequest(symbol="6758", data_type="info")
        ]
        
        with patch.object(self.provider, '_execute_single_request') as mock_execute:
            # 処理時間を測定するためのモック
            def mock_response(request):
                time.sleep(0.1)  # 処理時間をシミュレート
                return DataResponse(
                    request=request,
                    success=True,
                    data={"symbol": request.symbol},
                    processing_time=0.1
                )
            
            mock_execute.side_effect = mock_response
            
            # 並列実行
            start_time = time.time()
            responses = self.provider.parallel_execute(requests, timeout=30)
            execution_time = time.time() - start_time
            
            # 検証
            self.assertEqual(len(responses), 3)
            # 並列実行により実行時間が短縮されることを確認
            self.assertLess(execution_time, 0.25)  # 0.3秒（0.1*3）より短い
    
    def test_performance_stats(self):
        """パフォーマンス統計テスト"""
        # 初期統計
        stats = self.provider.get_performance_stats()
        self.assertEqual(stats['total_requests'], 0)
        self.assertEqual(stats['successful_requests'], 0)
        self.assertEqual(stats['failed_requests'], 0)
        
        # 統計更新
        mock_responses = {
            "7203": DataResponse(
                request=DataRequest(symbol="7203", data_type="info"),
                success=True,
                processing_time=0.1
            ),
            "4063": DataResponse(
                request=DataRequest(symbol="4063", data_type="info"),
                success=False,
                processing_time=0.2
            )
        }
        
        self.provider._update_stats(2, mock_responses, 0.5)
        
        # 統計確認
        stats = self.provider.get_performance_stats()
        self.assertEqual(stats['total_requests'], 2)
        self.assertEqual(stats['successful_requests'], 1)
        self.assertEqual(stats['failed_requests'], 1)
        self.assertEqual(stats['success_rate'], 50.0)
    
    def test_request_priority_handling(self):
        """リクエスト優先度処理テスト"""
        # 優先度の異なるリクエストを作成
        requests = [
            DataRequest(symbol="7203", data_type="info", priority=3),  # 低優先度
            DataRequest(symbol="4063", data_type="info", priority=1),  # 高優先度
            DataRequest(symbol="6758", data_type="info", priority=2)   # 中優先度
        ]
        
        with patch.object(self.provider, '_execute_single_request') as mock_execute:
            mock_execute.side_effect = lambda req: DataResponse(
                request=req,
                success=True,
                data={"symbol": req.symbol, "priority": req.priority}
            )
            
            # 並列実行
            responses = self.provider.parallel_execute(requests, timeout=30)
            
            # 検証（全リクエストが処理されることを確認）
            self.assertEqual(len(responses), 3)
            for symbol in ["7203", "4063", "6758"]:
                self.assertIn(symbol, responses)
                self.assertTrue(responses[symbol].success)

class TestModuleFunctions(unittest.TestCase):
    """モジュール関数のテスト"""
    
    def test_create_data_provider(self):
        """データプロバイダー作成テスト"""
        provider = create_data_provider(max_workers=20)
        
        self.assertIsInstance(provider, ParallelDataProvider)
        self.assertEqual(provider.max_workers, 20)
        
        provider.stop_workers()
    
    @patch('data.parallel_data_provider.create_data_provider')
    def test_quick_bulk_fetch(self, mock_create):
        """簡易一括データ取得テスト"""
        # モックプロバイダー
        mock_provider = Mock()
        mock_provider.bulk_fetch_data.return_value = {
            "7203": DataResponse(
                request=DataRequest(symbol="7203", data_type="info"),
                success=True,
                data={"price": 2500}
            ),
            "4063": DataResponse(
                request=DataRequest(symbol="4063", data_type="info"),
                success=False,
                error="API Error"
            )
        }
        mock_create.return_value = mock_provider
        
        # テスト実行
        result = quick_bulk_fetch(["7203", "4063"], "info")
        
        # 検証
        self.assertEqual(len(result), 1)  # 成功したもののみ
        self.assertIn("7203", result)
        self.assertEqual(result["7203"]["price"], 2500)
        self.assertNotIn("4063", result)  # 失敗したものは除外
        
        # プロバイダーが適切に停止されることを確認
        mock_provider.stop_workers.assert_called_once()

class TestErrorHandling(unittest.TestCase):
    """エラーハンドリングのテスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.provider = ParallelDataProvider(max_workers=2, max_connections=5)
    
    def tearDown(self):
        """テストクリーンアップ"""
        self.provider.stop_workers()
    
    def test_connection_pool_exhaustion(self):
        """接続プール枯渇テスト"""
        pool = ConnectionPool(max_connections=1)
        
        # 1つの接続を取得
        self.assertTrue(pool.acquire())
        
        # 2つ目の接続取得は失敗
        self.assertFalse(pool.acquire())
        
        # 接続解放後は再度取得可能
        pool.release()
        self.assertTrue(pool.acquire())
    
    def test_invalid_data_source(self):
        """無効なデータソーステスト"""
        request = DataRequest(symbol="7203", data_type="info")
        request.source = "invalid_source"
        
        with self.assertRaises(Exception):
            self.provider._fetch_data_by_source(request)
    
    def test_timeout_handling(self):
        """タイムアウト処理テスト"""
        def slow_execute(request):
            time.sleep(0.5)  # 遅い処理をシミュレート
            return DataResponse(request=request, success=True, data={})
        
        with patch.object(self.provider, '_execute_single_request', side_effect=slow_execute):
            requests = [DataRequest(symbol="7203", data_type="info", timeout=1)]
            
            # 短いタイムアウトで実行
            start_time = time.time()
            responses = self.provider.parallel_execute(requests, timeout=0.1)
            execution_time = time.time() - start_time
            
            # タイムアウトが発生することを確認
            self.assertLess(execution_time, 0.2)

def run_tdd_tests():
    """TDDテストスイート実行"""
    print("=" * 60)
    print("TradeFlow 並列データ取得システム TDDテストスイート")
    print("=" * 60)
    
    # テストスイートの組み立て
    test_classes = [
        TestDataRequest,
        TestDataResponse,
        TestConnectionPool,
        TestRateLimitManager,
        TestParallelDataProvider,
        TestModuleFunctions,
        TestErrorHandling
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー:")
    print(f"実行テスト数: {result.testsRun}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")
    print(f"成功率: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\n失敗したテスト:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print("\nエラーが発生したテスト:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception: ')[-1].split('\\n')[0]}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print("\n✓ 全テスト合格 - 50並列データ取得システムTDD実装完了")
    else:
        print("\n✗ 一部テスト失敗 - 修正が必要")
    
    return success

if __name__ == "__main__":
    success = run_tdd_tests()
    sys.exit(0 if success else 1)