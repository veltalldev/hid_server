#!/bin/bash
# Comprehensive curl Test Suite for HID Server
# Run this to verify all new functionality works correctly

BASE_URL="https://localhost:8444"  # Adjust if using HTTP or different port
CURL_OPTS="-k -s"  # -k for self-signed certs, -s for silent

echo "🧪 HID Server Comprehensive Test Suite"
echo "======================================"
echo "Base URL: $BASE_URL"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test result tracking
PASSED=0
FAILED=0

test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected_status="$5"
    
    echo -e "${BLUE}Testing:${NC} $name"
    echo "  $method $endpoint"
    
    if [ "$method" = "GET" ]; then
        response=$(curl $CURL_OPTS -w "\n%{http_code}" "$BASE_URL$endpoint")
    elif [ "$method" = "POST" ] && [ -n "$data" ]; then
        response=$(curl $CURL_OPTS -X POST -H "Content-Type: application/json" -d "$data" -w "\n%{http_code}" "$BASE_URL$endpoint")
    elif [ "$method" = "POST" ]; then
        response=$(curl $CURL_OPTS -X POST -w "\n%{http_code}" "$BASE_URL$endpoint")
    elif [ "$method" = "DELETE" ]; then
        response=$(curl $CURL_OPTS -X DELETE -w "\n%{http_code}" "$BASE_URL$endpoint")
    fi
    
    # Extract status code (last line) and body (everything else)
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "  ${GREEN}✓ PASS${NC} (Status: $status_code)"
        PASSED=$((PASSED + 1))
    else
        echo -e "  ${RED}✗ FAIL${NC} (Expected: $expected_status, Got: $status_code)"
        FAILED=$((FAILED + 1))
    fi
    
    # Pretty print JSON if it's valid JSON
    if echo "$body" | jq . >/dev/null 2>&1; then
        echo "$body" | jq .
    else
        echo "$body"
    fi
    echo ""
}

echo "🏁 Phase 1: Basic Server Health"
echo "==============================="

test_endpoint "Server Info" "GET" "/" "200"
test_endpoint "Debug Info" "GET" "/debug" "200"
test_endpoint "API Documentation" "GET" "/docs" "200"

echo "📋 Phase 2: Script Management"
echo "============================="

test_endpoint "List Scripts" "GET" "/scripts" "200"
test_endpoint "Get Script Image (should fail - no scripts yet)" "GET" "/image/nonexistent" "404"

echo "🎮 Phase 3: Session State Management"
echo "===================================="

test_endpoint "Get Initial Session State" "GET" "/session_state" "200"

test_endpoint "Update Session - Set Combination" "POST" "/session_state" \
    '{"selected_combination_id": "drk_bottom_deck_passage_3", "step_size": 1.5}' "200"

test_endpoint "Get Updated Session State" "GET" "/session_state" "200"

test_endpoint "Update Session - Invalid Step Size" "POST" "/session_state" \
    '{"step_size": 5.0}' "400"

test_endpoint "Update Session - Only Step Size" "POST" "/session_state" \
    '{"step_size": 2.0}' "200"

test_endpoint "Clear Session State" "DELETE" "/session_state" "200"

test_endpoint "Verify Session Cleared" "GET" "/session_state" "200"

echo "🎯 Phase 4: Context-Dependent Actions (No Context)"
echo "=================================================="

test_endpoint "Class Init - No Context" "POST" "/action/class/init" "" "400"
test_endpoint "Map Navigate - No Context" "POST" "/action/map/navigate" "" "400"
test_endpoint "Map Position - No Context" "POST" "/action/map/position" "" "400"

echo "🎯 Phase 5: Context-Dependent Actions (With Context)"
echo "===================================================="

# Set context first
echo "Setting up context..."
curl $CURL_OPTS -X POST -H "Content-Type: application/json" \
    -d '{"selected_combination_id": "drk_bottom_deck_passage_3", "step_size": 1.0}' \
    "$BASE_URL/session_state" > /dev/null

test_endpoint "Class Init - With DRK Context" "POST" "/action/class/init" "" "200"
test_endpoint "Map Navigate - With BDP3 Context" "POST" "/action/map/navigate" "" "200"
test_endpoint "Map Position - With BDP3 Context" "POST" "/action/map/position" "" "200"

# Test with different context
echo "Switching to Night Walker context..."
curl $CURL_OPTS -X POST -H "Content-Type: application/json" \
    -d '{"selected_combination_id": "nw_laboratory_behind_closed_door_3"}' \
    "$BASE_URL/session_state" > /dev/null

test_endpoint "Class Init - With NW Context" "POST" "/action/class/init" "" "200"
test_endpoint "Map Navigate - With LBLD3 Context" "POST" "/action/map/navigate" "" "200"
test_endpoint "Map Position - With LBLD3 Context" "POST" "/action/map/position" "" "200"

echo "🕹️ Phase 6: Movement Actions (Context-Aware)"
echo "============================================="

# Set step size context
curl $CURL_OPTS -X POST -H "Content-Type: application/json" \
    -d '{"step_size": 0.5}' \
    "$BASE_URL/session_state" > /dev/null

test_endpoint "Move Up - Small Step" "POST" "/action/movement/up" "" "200"
test_endpoint "Move Down - Small Step" "POST" "/action/movement/down" "" "200"
test_endpoint "Move Left - Small Step" "POST" "/action/movement/left" "" "200"
test_endpoint "Move Right - Small Step" "POST" "/action/movement/right" "" "200"

# Change step size
curl $CURL_OPTS -X POST -H "Content-Type: application/json" \
    -d '{"step_size": 2.5}' \
    "$BASE_URL/session_state" > /dev/null

test_endpoint "Move Up - Large Step" "POST" "/action/movement/up" "" "200"

test_endpoint "Invalid Direction" "POST" "/action/movement/invalid" "" "400"

echo "🎮 Phase 7: Context-Agnostic Actions"
echo "==================================="

test_endpoint "Double Jump" "POST" "/action/movement/double_jump" "" "200"
test_endpoint "Jump Down" "POST" "/action/movement/jump_down" "" "200"
test_endpoint "Rope Up" "POST" "/action/movement/rope_up" "" "200"
test_endpoint "Interact" "POST" "/action/movement/interact" "" "200"

echo "🛠️ Phase 8: Utility Actions"
echo "============================"

test_endpoint "Go to Town" "POST" "/action/utility/go_to_town" "" "200"
test_endpoint "Use Consumables" "POST" "/action/utility/use_consumables" "" "200"

echo "📊 Phase 9: Macro Management"
echo "============================"

test_endpoint "Get Macro Status" "GET" "/status" "200"
test_endpoint "Start Macro - No Script" "POST" "/start_macro" '{"script_name": "nonexistent.ahk"}' "400"

# Only test if scripts exist
if curl $CURL_OPTS "$BASE_URL/scripts" | jq -r '.scripts[0].name' 2>/dev/null | grep -q ".ahk"; then
    SCRIPT_NAME=$(curl $CURL_OPTS "$BASE_URL/scripts" | jq -r '.scripts[0].name' 2>/dev/null)
    echo "Found script: $SCRIPT_NAME"
    
    test_endpoint "Start Macro - Valid Script" "POST" "/start_macro" "{\"script_name\": \"$SCRIPT_NAME\"}" "200"
    
    sleep 1
    
    test_endpoint "Pause Macro" "POST" "/pause_macro" "" "200"
    test_endpoint "Resume Macro" "POST" "/resume_macro" "" "200"
    test_endpoint "Stop Macro" "POST" "/stop_macro" "" "200"
else
    echo "⚠️  No scripts found - skipping macro tests"
fi

echo "🔍 Phase 10: Edge Cases"
echo "======================="

test_endpoint "Invalid Session Data" "POST" "/session_state" '{"invalid": "data"}' "200"
test_endpoint "Empty Session Update" "POST" "/session_state" '{}' "200"

# Test invalid combination IDs
curl $CURL_OPTS -X POST -H "Content-Type: application/json" \
    -d '{"selected_combination_id": "invalid_combination"}' \
    "$BASE_URL/session_state" > /dev/null

test_endpoint "Class Init - Invalid Combination" "POST" "/action/class/init" "" "400"

echo ""
echo "📈 Test Results Summary"
echo "======================"
echo -e "Total Tests: $((PASSED + FAILED))"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed! Your implementation is working correctly.${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Some tests failed. Check the output above for details.${NC}"
    exit 1
fi

# Additional manual verification commands
echo ""
echo "🔧 Manual Verification Commands"
echo "==============================="
echo "# Check current session state:"
echo "curl $CURL_OPTS '$BASE_URL/session_state' | jq ."
echo ""
echo "# Set combination and test class init:"
echo "curl $CURL_OPTS -X POST -H 'Content-Type: application/json' \\"
echo "  -d '{\"selected_combination_id\": \"drk_bottom_deck_passage_3\"}' \\"
echo "  '$BASE_URL/session_state'"
echo "curl $CURL_OPTS -X POST '$BASE_URL/action/class/init'"
echo ""
echo "# Test movement with different step sizes:"
echo "curl $CURL_OPTS -X POST -H 'Content-Type: application/json' \\"
echo "  -d '{\"step_size\": 0.5}' '$BASE_URL/session_state'"
echo "curl $CURL_OPTS -X POST '$BASE_URL/action/movement/up'"
echo ""
echo "curl $CURL_OPTS -X POST -H 'Content-Type: application/json' \\"
echo "  -d '{\"step_size\": 3.0}' '$BASE_URL/session_state'"
echo "curl $CURL_OPTS -X POST '$BASE_URL/action/movement/up'"
