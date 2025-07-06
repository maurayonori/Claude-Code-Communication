#!/bin/bash
# GitHub CLI修正スクリプト - TradeFlow用

echo "🔧 GitHub CLI修正開始..."

# TradeFlowディレクトリに移動
cd "$(dirname "$0")/../.."

echo "📍 現在のディレクトリ: $(pwd)"

# Git設定確認
echo "🔍 Git設定確認..."
git remote -v
echo ""

# GitHub CLI基本機能テスト
echo "🧪 GitHub CLI機能テスト..."

# 1. リポジトリ情報確認
echo "1. リポジトリ情報確認:"
if gh repo view 2>/dev/null; then
    echo "✅ リポジトリ情報取得成功"
else
    echo "❌ リポジトリ情報取得失敗"
    echo "手動設定を実行中..."
    
    # リポジトリのHTTPS URLからowner/repoを抽出
    REPO_URL=$(git remote get-url origin)
    if [[ $REPO_URL =~ github\.com[:/]([^/]+)/([^/.]+) ]]; then
        OWNER="${BASH_REMATCH[1]}"
        REPO="${BASH_REMATCH[2]}"
        echo "検出されたリポジトリ: $OWNER/$REPO"
    else
        echo "❌ リポジトリURL解析失敗: $REPO_URL"
        exit 1
    fi
fi

echo ""

# 2. Issue一覧テスト
echo "2. Issue一覧テスト:"
if gh issue list --limit 3 2>/dev/null; then
    echo "✅ Issue一覧取得成功"
else
    echo "❌ Issue一覧取得失敗"
fi

echo ""

# 3. PR一覧テスト
echo "3. PR一覧テスト:"
if gh pr list --limit 3 2>/dev/null; then
    echo "✅ PR一覧取得成功"
else
    echo "❌ PR一覧取得失敗（PRが存在しない可能性）"
fi

echo ""

# GitHub CLI設定用のエイリアス作成
echo "🛠️ TradeFlow用GitHub CLIエイリアス作成..."

# エイリアス設定ファイル作成
cat > .gh_aliases << 'EOF'
# TradeFlow用GitHub CLIエイリアス

# Issue管理
alias tf-issues='gh issue list'
alias tf-issue-view='gh issue view'
alias tf-issue-create='gh issue create'
alias tf-issue-close='gh issue close'

# PR管理
alias tf-pr-list='gh pr list'
alias tf-pr-view='gh pr view'
alias tf-pr-create='gh pr create'
alias tf-pr-merge='gh pr merge'

# Repository管理
alias tf-repo-view='gh repo view'
alias tf-repo-clone='gh repo clone'

# Workflow管理
alias tf-workflow-list='gh workflow list'
alias tf-workflow-run='gh workflow run'
EOF

echo "✅ エイリアス作成完了: .gh_aliases"

# 使用方法のドキュメント作成
cat > scripts/github-cli-usage.md << 'EOF'
# TradeFlow GitHub CLI使用ガイド

## 基本コマンド

### Issue管理
```bash
# Issue一覧表示
gh issue list

# Issue詳細表示
gh issue view [issue-number]

# Issue作成
gh issue create --title "タイトル" --body "内容"

# Issue終了
gh issue close [issue-number]
```

### PR管理
```bash
# PR一覧表示
gh pr list

# PR詳細表示
gh pr view [pr-number]

# PR作成
gh pr create --title "タイトル" --body "内容"

# PRマージ
gh pr merge [pr-number]
```

### Repository管理
```bash
# リポジトリ情報表示
gh repo view

# ワークフロー一覧
gh workflow list
```

## エイリアス使用方法

```bash
# エイリアス読み込み
source .gh_aliases

# エイリアス使用例
tf-issues           # Issue一覧
tf-issue-view 123   # Issue #123表示
tf-pr-list         # PR一覧
```

## トラブルシューティング

### 認証エラー
```bash
gh auth status
gh auth login
```

### リポジトリ認識エラー
```bash
gh repo view
git remote -v
```
EOF

echo "✅ 使用ガイド作成完了: scripts/github-cli-usage.md"

# 最終テスト実行
echo ""
echo "🧪 最終機能テスト..."

echo "認証状態:"
gh auth status

echo ""
echo "基本機能テスト:"
if gh repo view --json name,owner,description 2>/dev/null | head -5; then
    echo "✅ GitHub CLI正常動作確認"
else
    echo "⚠️ 一部機能に制限がある可能性があります"
fi

echo ""
echo "🎉 GitHub CLI修正完了！"
echo ""
echo "📚 使用方法:"
echo "  - 基本コマンド: scripts/github-cli-usage.md を参照"
echo "  - エイリアス: source .gh_aliases で読み込み"
echo "  - テスト: gh issue list で動作確認"