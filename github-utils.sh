#!/bin/bash
# GitHub CLI ユーティリティスクリプト - TradeFlow用
# すべてのGitHub関連操作を簡単に実行するためのヘルパー

# TradeFlowディレクトリに移動
cd "$(dirname "$0")/../.."

# 色付きメッセージ用の関数
print_success() { echo -e "\033[32m✅ $1\033[0m"; }
print_error() { echo -e "\033[31m❌ $1\033[0m"; }
print_info() { echo -e "\033[34mℹ️  $1\033[0m"; }
print_warning() { echo -e "\033[33m⚠️  $1\033[0m"; }

# ヘルプ表示
show_help() {
    echo "🚀 TradeFlow GitHub CLI ユーティリティ"
    echo ""
    echo "使用方法: ./github-utils.sh [コマンド] [オプション]"
    echo ""
    echo "📋 Issue管理:"
    echo "  issues              - Issue一覧表示"
    echo "  issue <number>      - Issue詳細表示"
    echo "  create-issue        - Issue作成（インタラクティブ）"
    echo "  close-issue <number> - Issue終了"
    echo ""
    echo "🔀 PR管理:"
    echo "  prs                 - PR一覧表示"
    echo "  pr <number>         - PR詳細表示"
    echo "  create-pr           - PR作成（インタラクティブ）"
    echo "  merge-pr <number>   - PRマージ"
    echo ""
    echo "📊 Repository情報:"
    echo "  repo                - リポジトリ情報表示"
    echo "  status              - 全体状況表示"
    echo "  workflows           - ワークフロー一覧"
    echo ""
    echo "🛠️ ユーティリティ:"
    echo "  check               - GitHub CLI動作確認"
    echo "  auth                - 認証状況確認"
    echo "  help                - このヘルプ表示"
    echo ""
    echo "例:"
    echo "  ./github-utils.sh issues"
    echo "  ./github-utils.sh issue 42"
    echo "  ./github-utils.sh create-issue"
}

# GitHub CLI動作確認
check_github_cli() {
    print_info "GitHub CLI動作確認開始..."
    
    if ! command -v gh &> /dev/null; then
        print_error "GitHub CLIがインストールされていません"
        exit 1
    fi
    
    print_success "GitHub CLI インストール確認済み"
    
    if ! gh auth status &> /dev/null; then
        print_error "GitHub CLIの認証が必要です"
        echo "以下のコマンドで認証してください："
        echo "gh auth login"
        exit 1
    fi
    
    print_success "GitHub CLI 認証確認済み"
    
    if ! gh repo view &> /dev/null; then
        print_error "リポジトリ認識エラー"
        echo "現在のディレクトリ: $(pwd)"
        echo "Gitリポジトリを確認してください"
        exit 1
    fi
    
    print_success "リポジトリ認識確認済み"
    print_success "GitHub CLI 正常動作確認完了"
}

# Issue一覧表示
list_issues() {
    print_info "Issue一覧を取得中..."
    gh issue list --limit 10
}

# Issue詳細表示
show_issue() {
    if [ -z "$1" ]; then
        print_error "Issue番号を指定してください"
        echo "使用例: ./github-utils.sh issue 42"
        exit 1
    fi
    
    print_info "Issue #$1 の詳細を取得中..."
    gh issue view "$1"
}

# Issue作成（インタラクティブ）
create_issue() {
    print_info "Issue作成を開始します"
    echo "タイトルを入力してください:"
    read -r title
    
    if [ -z "$title" ]; then
        print_error "タイトルは必須です"
        exit 1
    fi
    
    echo "説明を入力してください（空白で終了）:"
    body=""
    while IFS= read -r line; do
        [ -z "$line" ] && break
        body+="$line"$'\n'
    done
    
    echo "ラベルを選択してください（複数可、カンマ区切り）:"
    echo "  - bug: バグ報告"
    echo "  - enhancement: 機能強化"
    echo "  - documentation: ドキュメント"
    echo "  - question: 質問"
    echo "  - high-priority: 高優先度"
    read -r labels
    
    if [ -n "$labels" ]; then
        gh issue create --title "$title" --body "$body" --label "$labels"
    else
        gh issue create --title "$title" --body "$body"
    fi
    
    print_success "Issue作成完了"
}

# Issue終了
close_issue() {
    if [ -z "$1" ]; then
        print_error "Issue番号を指定してください"
        echo "使用例: ./github-utils.sh close-issue 42"
        exit 1
    fi
    
    print_info "Issue #$1 を終了中..."
    gh issue close "$1"
    print_success "Issue #$1 を終了しました"
}

# PR一覧表示
list_prs() {
    print_info "PR一覧を取得中..."
    gh pr list --limit 10
}

# PR詳細表示
show_pr() {
    if [ -z "$1" ]; then
        print_error "PR番号を指定してください"
        echo "使用例: ./github-utils.sh pr 42"
        exit 1
    fi
    
    print_info "PR #$1 の詳細を取得中..."
    gh pr view "$1"
}

# PR作成（インタラクティブ）
create_pr() {
    print_info "PR作成を開始します"
    
    # 現在のブランチ確認
    current_branch=$(git branch --show-current)
    print_info "現在のブランチ: $current_branch"
    
    if [ "$current_branch" = "main" ] || [ "$current_branch" = "master" ]; then
        print_warning "メインブランチからのPR作成は推奨されません"
        echo "続行しますか？ (y/N)"
        read -r confirm
        if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
            print_info "PR作成をキャンセルしました"
            exit 0
        fi
    fi
    
    echo "PRタイトルを入力してください:"
    read -r title
    
    if [ -z "$title" ]; then
        print_error "タイトルは必須です"
        exit 1
    fi
    
    echo "PR説明を入力してください（空白で終了）:"
    body=""
    while IFS= read -r line; do
        [ -z "$line" ] && break
        body+="$line"$'\n'
    done
    
    gh pr create --title "$title" --body "$body"
    print_success "PR作成完了"
}

# PRマージ
merge_pr() {
    if [ -z "$1" ]; then
        print_error "PR番号を指定してください"
        echo "使用例: ./github-utils.sh merge-pr 42"
        exit 1
    fi
    
    print_info "PR #$1 をマージ中..."
    gh pr merge "$1" --merge
    print_success "PR #$1 をマージしました"
}

# リポジトリ情報表示
show_repo() {
    print_info "リポジトリ情報を取得中..."
    gh repo view
}

# 全体状況表示
show_status() {
    print_info "TradeFlow GitHubプロジェクト状況"
    echo "=================================="
    
    print_info "認証状況:"
    gh auth status
    
    echo ""
    print_info "オープンなIssue (上位5件):"
    gh issue list --state open --limit 5
    
    echo ""
    print_info "オープンなPR:"
    gh pr list --state open --limit 5
    
    echo ""
    print_info "最近のコミット:"
    git log --oneline -5
    
    echo ""
    print_info "現在のブランチ:"
    git branch --show-current
    
    echo ""
    print_info "変更されたファイル:"
    git status --porcelain | head -10
}

# ワークフロー一覧
show_workflows() {
    print_info "GitHub Actions ワークフロー一覧:"
    gh workflow list
}

# 認証状況確認
check_auth() {
    print_info "GitHub CLI認証状況:"
    gh auth status
}

# メイン処理
case "${1:-help}" in
    "issues")
        check_github_cli
        list_issues
        ;;
    "issue")
        check_github_cli
        show_issue "$2"
        ;;
    "create-issue")
        check_github_cli
        create_issue
        ;;
    "close-issue")
        check_github_cli
        close_issue "$2"
        ;;
    "prs")
        check_github_cli
        list_prs
        ;;
    "pr")
        check_github_cli
        show_pr "$2"
        ;;
    "create-pr")
        check_github_cli
        create_pr
        ;;
    "merge-pr")
        check_github_cli
        merge_pr "$2"
        ;;
    "repo")
        check_github_cli
        show_repo
        ;;
    "status")
        check_github_cli
        show_status
        ;;
    "workflows")
        check_github_cli
        show_workflows
        ;;
    "check")
        check_github_cli
        ;;
    "auth")
        check_auth
        ;;
    "help"|*)
        show_help
        ;;
esac