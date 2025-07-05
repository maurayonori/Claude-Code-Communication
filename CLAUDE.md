# TradeFlow Agent Communication System

## エージェント構成（TradeFlow専門チーム）
- **PRESIDENT** (別セッション): Product Owner / Project Manager
- **tech_lead** (multiagent:agents): Tech Lead / Architecture Lead  
- **analysis_engineer** (multiagent:agents): 分析エンジン担当
- **trading_engineer** (multiagent:agents): 取引システム担当
- **risk_engineer** (multiagent:agents): リスク管理担当
- **data_engineer** (multiagent:agents): データ処理担当

## 各役割の責任範囲
- **PRESIDENT**: @instructions/president.md (全体戦略、Linear Issue管理、利益目標監視)
- **tech_lead**: @instructions/boss.md (技術統括、TDD指導、品質管理)
- **analysis_engineer**: @instructions/worker.md (4つの分析エンジン、統合スコアリング)
- **trading_engineer**: @instructions/trading_engineer.md (17ファイル取引システム、利益最大化)
- **risk_engineer**: @instructions/risk_engineer.md (需給リスク分析、動的目標設定)
- **data_engineer**: @instructions/data_engineer.md (50並列データ取得、800銘柄管理)

## メッセージ送信
```bash
./agent-send.sh [相手] "[メッセージ]"
```

## TradeFlow開発フロー
```
PRESIDENT → tech_lead → 4専門エンジニア → tech_lead → PRESIDENT
```

## 利益目標
- **プロフィットファクター**: 1.5以上
- **日次利益**: 5,000円以上  
- **勝率**: 65%以上
- **TDD実践率**: 100% 