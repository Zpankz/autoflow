#!/bin/bash

# AutoFlow Nx Command Scripts
# Enhanced build orchestration and development workflows

echo "🚀 AutoFlow Nx Enhanced Commands"
echo "==============================="

# Build all projects in dependency order
build_all() {
    echo "📦 Building all projects in dependency order..."
    nx run-many --target=build --projects=core,backend,tidb-ai-parent,example-docs --parallel=2
}

# Development setup - build dependencies and start dev servers
dev_setup() {
    echo "🔧 Setting up development environment..."
    nx run-many --target=build --projects=core,backend --parallel=2
    echo "✅ Dependencies built. Starting dev servers..."
    # Start backend and frontend in parallel
    (nx run backend:dev &)
    (nx run tidb-ai-parent:dev &)
    (nx run example-docs:dev &)
    wait
}

# Run tests with proper dependency chain
test_all() {
    echo "🧪 Running all tests with dependency chain..."
    nx run-many --target=test --projects=core,backend,tidb-ai-parent --parallel=2
}

# Affected commands based on changes
affected_build() {
    echo "🎯 Building only affected projects..."
    nx affected:build --base=main
}

affected_test() {
    echo "🎯 Testing only affected projects..."
    nx affected:test --base=main
}

# Graph visualization commands
show_deps() {
    echo "📊 Opening dependency graph..."
    nx graph
}

show_affected() {
    echo "📊 Showing affected projects..."
    nx affected:graph --base=main
}

# Cache management
clear_cache() {
    echo "🗑️  Clearing Nx cache..."
    nx reset
}

cache_stats() {
    echo "📈 Showing cache statistics..."
    nx show projects --affected --base=main
}

# Main menu
case "$1" in
    "build") build_all ;;
    "dev") dev_setup ;;
    "test") test_all ;;
    "affected:build") affected_build ;;
    "affected:test") affected_test ;;
    "graph") show_deps ;;
    "affected:graph") show_affected ;;
    "clear-cache") clear_cache ;;
    "cache-stats") cache_stats ;;
    *)
        echo "Usage: $0 {build|dev|test|affected:build|affected:test|graph|affected:graph|clear-cache|cache-stats}"
        echo ""
        echo "Available commands:"
        echo "  build          - Build all projects in dependency order"
        echo "  dev            - Setup development environment"
        echo "  test           - Run all tests"
        echo "  affected:build - Build only affected projects"
        echo "  affected:test  - Test only affected projects"
        echo "  graph          - Show dependency graph"
        echo "  affected:graph - Show affected projects graph"
        echo "  clear-cache    - Clear Nx cache"
        echo "  cache-stats    - Show cache statistics"
        ;;
esac
