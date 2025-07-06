#!/bin/bash
# GitHub CLI動作テストスクリプト

echo "🧪 GitHub CLI機能テスト開始"
echo "================================"

cd "$(dirname "$0")/../.."

# テスト結果を記録
test_results=()

# テスト実行関数
run_test() {
    local test_name="$1"
    local command="$2"
    
    echo -n "Testing $test_name... "
    
    if eval "$command" &>/dev/null; then
        echo "✅ 成功"
        test_results+=("✅ $test_name")
    else
        echo "❌ 失敗"
        test_results+=("❌ $test_name")
    fi
}

# 基本機能テスト
echo "📋 基本機能テスト"
run_test "認証確認" "gh auth status"
run_test "リポジトリ情報" "gh repo view --json name,owner"
run_test "Issue一覧" "gh issue list --limit 1"
run_test "PR一覧" "gh pr list --limit 1"

echo ""
echo "📊 Advanced機能テスト"
run_test "ワークフロー一覧" "gh workflow list"
run_test "リリース一覧" "gh release list --limit 1"
run_test "リポジトリ統計" "gh repo view --json stargazerCount,forkCount"

echo ""
echo "🔍 検索機能テスト"
run_test "Issue検索" "gh issue list --search 'in:title Phase' --limit 1"
run_test "レーベル一覧" "gh label list --limit 5"

echo ""
echo "📋 テスト結果サマリー"
echo "==================="
for result in "${test_results[@]}"; do
    echo "$result"
done

# 成功率計算
total_tests=${#test_results[@]}
successful_tests=$(echo "${test_results[@]}" | grep -o "✅" | wc -l | tr -d ' ')
success_rate=$((successful_tests * 100 / total_tests))

echo ""
echo "📊 成功率: $successful_tests/$total_tests ($success_rate%)"

if [ "$success_rate" -ge 80 ]; then
    echo "🎉 GitHub CLI正常動作確認 - 利用可能"
elif [ "$success_rate" -ge 60 ]; then
    echo "⚠️ GitHub CLI部分的動作 - 基本機能は利用可能"
else
    echo "❌ GitHub CLI問題あり - 設定確認が必要"
fi

echo ""
echo "💡 よく使用するコマンド例:"
echo "  ./github-utils.sh status     # プロジェクト全体状況"
echo "  ./github-utils.sh issues     # Issue一覧"
echo "  ./github-utils.sh create-issue # Issue作成"
echo "  gh issue list               # 直接コマンド"
echo "  gh issue view 42            # Issue詳細"