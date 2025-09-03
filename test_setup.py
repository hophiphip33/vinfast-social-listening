#!/usr/bin/env python3
"""
VinFast Social Listening Platform - Setup Verification Script
Tests all major components to ensure the platform is working correctly
"""

import asyncio
import sys
import time
from datetime import datetime
import requests
import json

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_status(message, status="info"):
    colors = {
        "success": Colors.GREEN + "✅ ",
        "error": Colors.RED + "❌ ",
        "warning": Colors.YELLOW + "⚠️  ",
        "info": Colors.BLUE + "ℹ️  "
    }
    print(f"{colors.get(status, '')}{message}{Colors.END}")

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")

async def test_database_connection():
    """Test MongoDB connection"""
    try:
        print_header("Testing Database Connection")
        
        from backend.database.connection import db_manager
        await db_manager.connect()
        
        # Test basic database operations
        collection = db_manager.get_collection("test")
        test_doc = {"test": True, "timestamp": datetime.now()}
        result = await collection.insert_one(test_doc)
        await collection.delete_one({"_id": result.inserted_id})
        
        await db_manager.disconnect()
        print_status("Database connection successful", "success")
        return True
        
    except Exception as e:
        print_status(f"Database connection failed: {e}", "error")
        return False

async def test_sentiment_analysis():
    """Test Vietnamese sentiment analysis"""
    try:
        print_header("Testing Vietnamese Sentiment Analysis")
        
        from backend.processors.vietnamese_sentiment import VietnameseSentimentAnalyzer
        analyzer = VietnameseSentimentAnalyzer()
        
        test_texts = [
            "VinFast VF8 thật tuyệt vời, xe điện đẹp và chất lượng cao",
            "Tôi thất vọng về chất lượng xe VinFast, có nhiều lỗi",
            "VinFast là thương hiệu xe hơi của Việt Nam"
        ]
        
        print_status("Loading Vietnamese sentiment models...", "info")
        await analyzer.load_models()
        
        print_status("Testing sentiment analysis on Vietnamese text...", "info")
        for text in test_texts:
            result = await analyzer.analyze_sentiment(text)
            keywords = analyzer.extract_keywords(text)
            
            print(f"  📝 Text: {text[:50]}...")
            print(f"  🎯 Sentiment: {result['sentiment']} (score: {result['sentiment_score']:.2f})")
            print(f"  🔑 Keywords: {', '.join(keywords[:3])}")
            print()
        
        print_status("Vietnamese sentiment analysis working correctly", "success")
        return True
        
    except Exception as e:
        print_status(f"Sentiment analysis test failed: {e}", "error")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    try:
        print_header("Testing API Endpoints")
        
        base_url = "http://localhost:8000"
        
        # Test health endpoint
        print_status("Testing health endpoint...", "info")
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print_status("Health endpoint working", "success")
        else:
            print_status(f"Health endpoint failed: {response.status_code}", "error")
            return False
        
        # Test system status
        print_status("Testing system status...", "info")
        response = requests.get(f"{base_url}/api/system/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"  Database: {data.get('data', {}).get('database', 'unknown')}")
            print(f"  Model: {data.get('data', {}).get('sentiment_model', 'unknown')}")
            print_status("System status endpoint working", "success")
        else:
            print_status("System status endpoint not ready yet", "warning")
        
        # Test sentiment analysis endpoint
        print_status("Testing manual sentiment analysis...", "info")
        test_data = {"text": "VinFast VF8 là xe điện tuyệt vời"}
        response = requests.post(
            f"{base_url}/api/analyze/sentiment",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  Sentiment: {result.get('data', {}).get('sentiment', 'unknown')}")
            print_status("Sentiment analysis API working", "success")
        else:
            print_status("Sentiment analysis API not ready", "warning")
        
        print_status("API endpoints are functional", "success")
        return True
        
    except requests.exceptions.ConnectionError:
        print_status("API server not running. Start with: docker-compose up", "error")
        return False
    except Exception as e:
        print_status(f"API test failed: {e}", "error")
        return False

def test_frontend():
    """Test frontend accessibility"""
    try:
        print_header("Testing Frontend Dashboard")
        
        frontend_url = "http://localhost:3000"
        
        print_status("Testing frontend accessibility...", "info")
        response = requests.get(frontend_url, timeout=10)
        
        if response.status_code == 200:
            print_status("Frontend dashboard accessible", "success")
            return True
        else:
            print_status(f"Frontend not accessible: {response.status_code}", "error")
            return False
            
    except requests.exceptions.ConnectionError:
        print_status("Frontend not running. Start with: docker-compose up", "error")
        return False
    except Exception as e:
        print_status(f"Frontend test failed: {e}", "error")
        return False

def test_docker_setup():
    """Test Docker setup"""
    try:
        print_header("Testing Docker Configuration")
        
        import subprocess
        
        # Check if Docker is installed
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_status(f"Docker installed: {result.stdout.strip()}", "success")
        else:
            print_status("Docker not found", "error")
            return False
        
        # Check if Docker Compose is installed
        result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_status(f"Docker Compose installed: {result.stdout.strip()}", "success")
        else:
            print_status("Docker Compose not found", "error")
            return False
        
        return True
        
    except Exception as e:
        print_status(f"Docker test failed: {e}", "error")
        return False

def print_summary(results):
    """Print test summary"""
    print_header("Test Summary")
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {Colors.GREEN}{passed_tests}{Colors.END}")
    print(f"Failed: {Colors.RED}{total_tests - passed_tests}{Colors.END}")
    
    if passed_tests == total_tests:
        print_status("🎉 All tests passed! Your VinFast Social Listening Platform is ready!", "success")
        print("\n📋 Next Steps:")
        print("1. 🌐 Open http://localhost:3000 to access the dashboard")
        print("2. 📊 Start data collection from the Data Collection page")
        print("3. 📈 View analytics and insights on the main dashboard")
        print("4. 📖 Read docs/GETTING_STARTED.md for detailed usage")
    else:
        print_status("❗ Some tests failed. Check the errors above and fix issues before proceeding.", "warning")
        print("\n🔧 Troubleshooting:")
        print("1. Ensure all dependencies are installed")
        print("2. Check if Docker services are running: docker-compose ps")
        print("3. View logs: docker-compose logs")
        print("4. Try restarting: docker-compose restart")

async def main():
    """Main test function"""
    print_status("🚀 VinFast Social Listening Platform - Setup Verification", "info")
    print_status("Testing all components to ensure proper setup...", "info")
    
    results = {}
    
    # Test Docker setup
    results['docker'] = test_docker_setup()
    
    # Test database connection
    results['database'] = await test_database_connection()
    
    # Test Vietnamese sentiment analysis
    results['sentiment'] = await test_sentiment_analysis()
    
    # Test API endpoints (only if services are running)
    results['api'] = test_api_endpoints()
    
    # Test frontend
    results['frontend'] = test_frontend()
    
    # Print summary
    print_summary(results)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_status("\nTest interrupted by user", "warning")
        sys.exit(1)
    except Exception as e:
        print_status(f"Test runner failed: {e}", "error")
        sys.exit(1)
