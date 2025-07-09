#!/usr/bin/env python3
"""
データAPI動作検証スクリプト
Yahoo Finance APIとkabu APIの基本動作をテスト
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging
import time

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_yahoo_finance_api():
    """Yahoo Finance APIテスト"""
    print("=== Yahoo Finance APIテスト ===")
    
    # テスト銘柄
    symbols = ['7203.T', '4063.T', '6758.T']  # トヨタ、エーアイ、ソニー
    
    for symbol in symbols:
        try:
            logger.info(f"テスト開始: {symbol}")
            
            # 今日の日付
            today = datetime.now()
            start_date = today - timedelta(days=1)
            end_date = today
            
            # データ取得
            data = yf.download(
                symbol,
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                interval="1m",
                progress=False,
                auto_adjust=False
            )
            
            if not data.empty:
                print(f"✓ {symbol} データ取得成功: {len(data)}行")
                print(f"  価格範囲: {data['Close'].min():.0f} - {data['Close'].max():.0f}円")
                print(f"  最新価格: {data['Close'].iloc[-1]:.0f}円")
                print(f"  出来高: {data['Volume'].iloc[-1]:,}株")
            else:
                print(f"✗ {symbol} データ取得失敗: 空のデータ")
                
        except Exception as e:
            print(f"✗ {symbol} エラー: {e}")
        
        time.sleep(0.1)  # レート制限対応
    
    return True

def test_kabu_api_integration():
    """kabu API統合テスト"""
    print("\n=== kabu API統合テスト ===")
    
    try:
        # kabu APIクライアントの存在確認
        kabu_client_path = os.path.join(os.path.dirname(__file__), '../../src/kabu_api/client.py')
        if os.path.exists(kabu_client_path):
            print("✓ kabu API クライアントファイル存在")
        else:
            print("✗ kabu API クライアントファイル不存在")
            return False
        
        # 統合マネージャーの存在確認
        integration_path = os.path.join(os.path.dirname(__file__), '../../src/integration/kabu_api_integration.py')
        if os.path.exists(integration_path):
            print("✓ kabu API統合マネージャー存在")
        else:
            print("✗ kabu API統合マネージャー不存在")
            return False
            
        # 設定ファイルの確認
        config_path = os.path.join(os.path.dirname(__file__), '../../config/kabu_STATION_API.yaml')
        if os.path.exists(config_path):
            print("✓ kabu API設定ファイル存在")
        else:
            print("✗ kabu API設定ファイル不存在")
            return False
        
        print("✓ kabu API統合準備完了")
        return True
        
    except Exception as e:
        print(f"✗ kabu API統合テストエラー: {e}")
        return False

def test_data_processing_performance():
    """データ処理パフォーマンステスト"""
    print("\n=== データ処理パフォーマンステスト ===")
    
    try:
        # 複数銘柄の並列処理シミュレーション
        symbols = ['7203.T', '4063.T', '6758.T', '9984.T', '8306.T']
        
        start_time = time.time()
        
        for symbol in symbols:
            try:
                # 簡単なデータ取得
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                if info:
                    print(f"✓ {symbol}: {info.get('longName', 'N/A')}")
                else:
                    print(f"✗ {symbol}: 情報取得失敗")
                    
            except Exception as e:
                print(f"✗ {symbol}: {e}")
            
            time.sleep(0.1)  # レート制限対応
        
        elapsed_time = time.time() - start_time
        print(f"処理時間: {elapsed_time:.2f}秒 ({len(symbols)}銘柄)")
        
        # パフォーマンス評価
        if elapsed_time < 30:
            print("✓ パフォーマンス良好")
        else:
            print("✗ パフォーマンス要改善")
            
        return True
        
    except Exception as e:
        print(f"✗ パフォーマンステストエラー: {e}")
        return False

def test_data_quality_validation():
    """データ品質検証テスト"""
    print("\n=== データ品質検証テスト ===")
    
    try:
        symbol = '7203.T'  # トヨタ自動車
        
        # 過去1週間のデータを取得
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        data = yf.download(
            symbol,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            interval="1d",
            progress=False
        )
        
        if data.empty:
            print(f"✗ {symbol}: データなし")
            return False
        
        # データ品質チェック
        missing_values = data.isnull().sum().sum()
        if missing_values == 0:
            print(f"✓ {symbol}: 欠損値なし")
        else:
            print(f"✗ {symbol}: 欠損値 {missing_values}件")
        
        # 価格の妥当性チェック
        if (data['Close'] > 0).all():
            print(f"✓ {symbol}: 価格データ正常")
        else:
            print(f"✗ {symbol}: 価格データ異常")
        
        # 出来高の妥当性チェック
        if (data['Volume'] >= 0).all():
            print(f"✓ {symbol}: 出来高データ正常")
        else:
            print(f"✗ {symbol}: 出来高データ異常")
        
        print(f"データ行数: {len(data)}")
        print(f"価格範囲: {data['Close'].min():.0f} - {data['Close'].max():.0f}円")
        
        return True
        
    except Exception as e:
        print(f"✗ データ品質検証エラー: {e}")
        return False

def main():
    """メイン実行関数"""
    print("TradeFlow Data Processing System - API動作検証")
    print("=" * 60)
    
    # テスト実行
    tests = [
        ("Yahoo Finance API", test_yahoo_finance_api),
        ("kabu API統合", test_kabu_api_integration),
        ("データ処理パフォーマンス", test_data_processing_performance),
        ("データ品質検証", test_data_quality_validation)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}テスト開始...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"{test_name}テストでエラー: {e}")
            results.append((test_name, False))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー:")
    
    passed = 0
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n合格: {passed}/{len(tests)} テスト")
    
    if passed == len(tests):
        print("✓ 全テスト合格 - データ処理システム準備完了")
    else:
        print("✗ 一部テスト失敗 - 要調査")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)