# TradeFlow Agent Communication System

## エージェント構成（TradeFlow専門チーム）
- **PRESIDENT** (別セッション): Product Owner / Project Manager
- **tech_lead** (multiagent:agents): Tech Lead / Architecture Lead  
- **analysis_engineer** (multiagent:agents): 分析エンジン担当
- **trading_engineer** (multiagent:agents): 取引システム担当
- **risk_engineer** (multiagent:agents): リスク管理担当
- **data_engineer** (multiagent:agents): データ処理担当
- **qa_engineer** (multiagent:agents): 品質保証・テスト・デバッグ担当

## 各役割の責任範囲
- **PRESIDENT**: @instructions/president.md (全体戦略、Linear Issue管理、利益目標監視)
- **tech_lead**: @instructions/boss.md (技術統括、TDD指導、品質管理)
- **analysis_engineer**: @instructions/worker.md (4つの分析エンジン、統合スコアリング)
- **trading_engineer**: @instructions/trading_engineer.md (17ファイル取引システム、利益最大化)
- **risk_engineer**: @instructions/risk_engineer.md (需給リスク分析、動的目標設定)
- **data_engineer**: @instructions/data_engineer.md (50並列データ取得、800銘柄管理)
- **qa_engineer**: @instructions/qa_engineer.md (品質保証、テスト戦略、デバッグ、品質ゲート管理)

## メッセージ送信
```bash
./agent-send.sh [相手] "[メッセージ]"
```

## TradeFlow開発フロー
```
PRESIDENT → tech_lead → 5専門エンジニア → qa_engineer → tech_lead → PRESIDENT
```

## 品質保証統合フロー
```
1. 5専門エンジニア実装完了
2. qa_engineer 包括的品質検証実行
3. 品質ゲート通過確認（カバレッジ85%以上）
4. 利益目標達成可能性検証
5. tech_lead 統合報告 → PRESIDENT
```

## 利益目標
- **プロフィットファクター**: 1.5以上
- **日次利益**: 5,000円以上  
- **勝率**: 65%以上
- **TDD実践率**: 100%

## 品質目標（QA Engineer追加）
- **テストカバレッジ**: 85%以上
- **テスト成功率**: 100%
- **品質ゲート通過率**: 100%
- **利益目標達成可能性**: 90%以上
- **静的解析警告**: 高リスク0件
- **メモリリーク**: 0件 