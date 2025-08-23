#!/usr/bin/env python3
"""
ML Platform Backend Setup Verification Script
Comprehensive testing of all backend components
"""

import requests
import psycopg2
import redis
import json
import time
import sys
from typing import Dict, Any

class BackendVerifier:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results = []
        
    def log(self, test_name: str, success: bool, message: str = ""):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"    {message}")
        self.results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
        
    def test_api_health(self):
        """Test API health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            success = response.status_code == 200
            self.log("API Health Check", success, 
                    f"Status: {response.status_code}, Response: {response.json()}")
        except Exception as e:
            self.log("API Health Check", False, str(e))
            
    def test_database_connection(self):
        """Test PostgreSQL database connection"""
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                user="postgres",
                password="password",
                database="mlplatform"
            )
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            conn.close()
            self.log("Database Connection", True, f"PostgreSQL version: {version[:50]}...")
        except Exception as e:
            self.log("Database Connection", False, str(e))
            
    def test_redis_connection(self):
        """Test Redis connection"""
        try:
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            r.ping()
            info = r.info()
            self.log("Redis Connection", True, f"Redis version: {info['redis_version']}")
        except Exception as e:
            self.log("Redis Connection", False, str(e))
            
    def test_minio_connection(self):
        """Test MinIO storage connection"""
        try:
            response = requests.get("http://localhost:9000/minio/health/live", timeout=10)
            success = response.status_code == 200
            self.log("MinIO Storage", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log("MinIO Storage", False, str(e))
            
    def test_user_registration(self):
        """Test user registration endpoint"""
        try:
            user_data = {
                "email": "test@example.com",
                "username": "testuser",
                "password": "testpassword123",
                "full_name": "Test User"
            }
            response = requests.post(f"{self.base_url}/api/auth/register", 
                                   json=user_data, timeout=10)
            success = response.status_code in [200, 400]  # 400 if user already exists
            message = response.json().get('detail', 'User registered successfully')
            self.log("User Registration", success, message)
            return response.status_code == 200
        except Exception as e:
            self.log("User Registration", False, str(e))
            return False
            
    def test_user_login(self):
        """Test user login endpoint"""
        try:
            login_data = {
                "username": "testuser",
                "password": "testpassword123"
            }
            response = requests.post(f"{self.base_url}/api/auth/login", 
                                   json=login_data, timeout=10)
            success = response.status_code == 200
            if success:
                token = response.json().get('access_token')
                self.auth_token = token
                self.log("User Login", True, "Login successful, token received")
                return token
            else:
                self.log("User Login", False, response.json().get('detail', 'Login failed'))
                return None
        except Exception as e:
            self.log("User Login", False, str(e))
            return None
            
    def test_protected_endpoint(self, token: str):
        """Test protected endpoint with authentication"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{self.base_url}/api/auth/me", 
                                  headers=headers, timeout=10)
            success = response.status_code == 200
            if success:
                user_data = response.json()
                self.log("Protected Endpoint", True, f"User: {user_data.get('username')}")
            else:
                self.log("Protected Endpoint", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log("Protected Endpoint", False, str(e))
            
    def test_notebook_creation(self, token: str):
        """Test notebook creation"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            notebook_data = {
                "name": "Test Notebook",
                "description": "Test notebook for verification",
                "gpu_type": "cpu",
                "cpu_cores": 2,
                "memory_gb": 4
            }
            response = requests.post(f"{self.base_url}/api/notebooks/", 
                                   json=notebook_data, headers=headers, timeout=10)
            success = response.status_code == 200
            if success:
                notebook = response.json()
                self.log("Notebook Creation", True, f"Notebook ID: {notebook.get('id')}")
                return notebook.get('id')
            else:
                self.log("Notebook Creation", False, f"Status: {response.status_code}")
                return None
        except Exception as e:
            self.log("Notebook Creation", False, str(e))
            return None
            
    def test_api_documentation(self):
        """Test API documentation availability"""
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=10)
            success = response.status_code == 200
            self.log("API Documentation", success, "Swagger UI accessible")
        except Exception as e:
            self.log("API Documentation", False, str(e))
            
    def run_all_tests(self):
        """Run all verification tests"""
        print("🧪 ML Platform Backend Verification")
        print("=" * 40)
        
        # Basic connectivity tests
        self.test_api_health()
        self.test_database_connection()
        self.test_redis_connection()
        self.test_minio_connection()
        
        # API functionality tests
        self.test_api_documentation()
        user_created = self.test_user_registration()
        token = self.test_user_login()
        
        if token:
            self.test_protected_endpoint(token)
            notebook_id = self.test_notebook_creation(token)
            
        # Summary
        print("\n📊 Test Summary")
        print("=" * 40)
        passed = sum(1 for r in self.results if r['success'])
        total = len(self.results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 All tests passed! Backend is ready for use.")
            return True
        else:
            print("⚠️  Some tests failed. Check the issues above.")
            failed_tests = [r['test'] for r in self.results if not r['success']]
            print(f"Failed tests: {', '.join(failed_tests)}")
            return False

if __name__ == "__main__":
    verifier = BackendVerifier()
    success = verifier.run_all_tests()
    sys.exit(0 if success else 1)