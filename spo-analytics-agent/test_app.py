"""
Quick test script for SPO Analytics Agent
Tests the mock agent and basic API functionality
"""

import sys
import json

def test_config():
    """Test configuration loading"""
    print("🧪 Testing Configuration...")
    from config import Config

    assert Config.MOCK_MODE == True, "Should be in mock mode"
    assert Config.PORT == 5001, "Port should be 5001"
    print(f"   ✅ Config loaded (Mock Mode: {Config.MOCK_MODE}, Port: {Config.PORT})")
    return True

def test_mock_agent():
    """Test mock SPO agent"""
    print("\n🧪 Testing Mock SPO Agent...")
    from spo_agent import MockSPOAnalyticsAgent

    agent = MockSPOAnalyticsAgent()

    # Test different query types
    test_queries = [
        "What is my fill rate for the last 7 days?",
        "What's the average markup across all DSPs?",
        "Why is traffic being blocked?"
    ]

    for query in test_queries:
        result = agent.answer_query(query)
        assert result['success'] == True, f"Query failed: {query}"
        assert result['narrative'], "Should have narrative response"
        assert len(result['data']) > 0, "Should have data"
        print(f"   ✅ Query: '{query[:50]}...' - Success")

    return True

def test_flask_app():
    """Test Flask app initialization"""
    print("\n🧪 Testing Flask App...")
    from app import app, agent

    # Test health endpoint
    with app.test_client() as client:
        response = client.get('/health')
        assert response.status_code == 200, "Health check should return 200"
        data = json.loads(response.data)
        assert data['status'] == 'healthy', "Should be healthy"
        print(f"   ✅ Health check passed")

        # Test config endpoint
        response = client.get('/api/config')
        assert response.status_code == 200
        print(f"   ✅ Config endpoint passed")

        # Test query endpoint
        response = client.post(
            '/api/query',
            json={'query': 'What is my fill rate?'},
            content_type='application/json'
        )
        assert response.status_code == 200, f"Query should return 200, got {response.status_code}"
        data = json.loads(response.data)
        assert data['success'] == True, "Query should succeed"
        print(f"   ✅ Query endpoint passed")

        # Test examples endpoint
        response = client.get('/api/examples')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'examples' in data, "Should have examples"
        print(f"   ✅ Examples endpoint passed")

    return True

def main():
    """Run all tests"""
    print("="*60)
    print("SPO Analytics Agent - Quick Test Suite")
    print("="*60)

    tests = [
        ('Configuration', test_config),
        ('Mock Agent', test_mock_agent),
        ('Flask App', test_flask_app),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"   ❌ {test_name} failed: {e}")
            failed += 1
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"✅ Passed: {passed}/{len(tests)}")
    if failed > 0:
        print(f"❌ Failed: {failed}/{len(tests)}")
    print("="*60)

    if failed == 0:
        print("\n🎉 All tests passed! The SPO Analytics Agent is ready to use.")
        print(f"\nTo start the app, run:")
        print(f"  python app.py")
        print(f"\nThen open: http://localhost:5001")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
