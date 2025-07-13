# ログシステム統合分析

## 現状分析
- **ログ使用ファイル数**: 134ファイル以上
- **複数のログシステム**:
  1. `logging.getLogger()` - 標準Python logging
  2. `CommonLogger.get_logger()` - カスタムラッパー
  3. `config.get_logger()` - ConfigManager経由
  4. `structured_logger.get_logger()` - 構造化ログ

## ログシステムの重複パターン

### 1. ログ初期化の重複
```python
# パターン1: 直接logging使用
self.logger = logging.getLogger(__name__)

# パターン2: CommonLogger使用
self.logger = CommonLogger.get_logger("module_name")

# パターン3: ConfigManager経由
self.logger = config.get_logger("module_name")

# パターン4: クラス内で独自設定
self._setup_logging()
```

### 2. ログ設定の重複
- 各モジュールで独自のフォーマッタ設定
- ハンドラの重複設定
- ログレベルの個別設定

### 3. ログ出力の重複
- 同じイベントを複数箇所でログ出力
- デバッグログの過剰出力
- エラーログの重複記録

## 統合方針

### 1. 統一ログマネージャーの設計
```python
# core/unified_logger.py
class UnifiedLogger:
    """全システム共通のログマネージャー"""
    
    _instance = None
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: str, component: str = None) -> logging.Logger:
        """統一されたロガー取得インターフェース"""
        key = f"{component}.{name}" if component else name
        if key not in cls._loggers:
            cls._loggers[key] = cls._create_logger(key)
        return cls._loggers[key]
    
    @classmethod
    def _create_logger(cls, name: str) -> logging.Logger:
        """統一された設定でロガーを作成"""
        logger = logging.getLogger(name)
        # 統一フォーマット、ハンドラ設定
        return logger
```

### 2. 使用方法の統一
```python
# 全てのモジュールで統一
from core.unified_logger import UnifiedLogger

class AnyModule:
    def __init__(self):
        self.logger = UnifiedLogger.get_logger(
            self.__class__.__name__,
            component="trading"  # コンポーネント別分類
        )
```

### 3. ログレベルの標準化
```python
# ログレベルポリシー
- CRITICAL: システム停止レベルのエラー
- ERROR: 処理失敗、例外発生
- WARNING: 注意が必要な状況
- INFO: 重要な処理の開始・終了
- DEBUG: 開発時のみ必要な詳細情報
```

## 削減効果予測

### 1. コード削減（約2,500行）
- ログ初期化コード: 800行
- 重複する設定コード: 600行
- 過剰なログ出力: 1,100行

### 2. パフォーマンス改善
- ログ出力のオーバーヘッド削減
- メモリ使用量の削減
- I/O処理の最適化

### 3. 保守性向上
- ログフォーマットの統一
- ログレベルの一元管理
- ログ出力先の柔軟な変更

## 実装手順

### Phase 1: 統一ログマネージャーの作成
1. `UnifiedLogger`クラスの実装
2. 設定ファイルからの読み込み機能
3. 環境別ログレベル制御

### Phase 2: 段階的移行
1. coreモジュールから移行開始
2. 各コンポーネントごとに順次移行
3. テストコードの更新

### Phase 3: 最適化
1. 不要なログ出力の削除
2. ログレベルの見直し
3. パフォーマンステスト

## リスクと対策
1. **既存ログの欠落**
   - 移行前後でログ出力を比較検証
   
2. **デバッグ情報の不足**
   - 開発環境でのログレベル自動調整
   
3. **パフォーマンス劣化**
   - 非同期ログ出力の検討