"""
Unit tests for Cloud Logger Component

Tests structured logging for AWS operations and ML inferences.
Property-based tests for comprehensive logging.
"""

import pytest
import json
from hypothesis import given, strategies as st, settings

# Import the component
import sys
sys.path.insert(0, 'src/components')
from cloud_logger import CloudLogger


class TestCloudLogger:
    """Test suite for CloudLogger component"""
    
    def test_log_bedrock_call_success(self):
        """Test logging successful Bedrock API call"""
        logger = CloudLogger()
        
        request = {
            "model": "claude-3",
            "prompt": "Test prompt",
            "parameters": {"temperature": 0.7}
        }
        response = {
            "output": "Test response",
            "tokens": 150
        }
        
        logger.log_bedrock_call(request, response)
        
        logs = logger.get_recent_logs(1)
        assert len(logs) == 1
        assert logs[0]["service"] == "bedrock"
        assert logs[0]["operation_type"] == "api_call"
        assert logs[0]["status"] == "success"
        assert logs[0]["details"]["model"] == "claude-3"
        assert logs[0]["details"]["tokens_used"] == 150
    
    def test_log_bedrock_call_error(self):
        """Test logging failed Bedrock API call"""
        logger = CloudLogger()
        
        request = {"model": "claude-3", "prompt": "Test"}
        
        logger.log_bedrock_call(request, error="API timeout")
        
        logs = logger.get_recent_logs(1)
        assert logs[0]["status"] == "error"
        assert logs[0]["details"]["error"] == "API timeout"
    
    def test_log_dynamodb_operation_success(self):
        """Test logging successful DynamoDB operation"""
        logger = CloudLogger()
        
        logger.log_dynamodb_operation(
            operation="put_item",
            table="FarmerProfiles",
            details={"farmer_id": "123", "name": "Ramesh"}
        )
        
        logs = logger.get_recent_logs(1)
        assert logs[0]["service"] == "dynamodb"
        assert logs[0]["operation_type"] == "put_item"
        assert logs[0]["status"] == "success"
        assert logs[0]["details"]["table"] == "FarmerProfiles"
    
    def test_log_dynamodb_operation_error(self):
        """Test logging failed DynamoDB operation"""
        logger = CloudLogger()
        
        logger.log_dynamodb_operation(
            operation="get_item",
            table="FarmerProfiles",
            details={"farmer_id": "123"},
            error="Item not found"
        )
        
        logs = logger.get_recent_logs(1)
        assert logs[0]["status"] == "error"
        assert logs[0]["details"]["error"] == "Item not found"
    
    def test_log_ml_operation_success(self):
        """Test logging successful ML operation"""
        logger = CloudLogger()
        
        logger.log_ml_operation(
            operation="train",
            duration=45.5,
            details={"model": "prophet", "data_points": 365}
        )
        
        logs = logger.get_recent_logs(1)
        assert logs[0]["service"] == "ml_model"
        assert logs[0]["operation_type"] == "train"
        assert logs[0]["status"] == "success"
        assert logs[0]["details"]["duration_seconds"] == 45.5
        assert logs[0]["details"]["model"] == "prophet"
    
    def test_log_ml_operation_error(self):
        """Test logging failed ML operation"""
        logger = CloudLogger()
        
        logger.log_ml_operation(
            operation="predict",
            duration=2.3,
            details={"model": "prophet"},
            error="Insufficient training data"
        )
        
        logs = logger.get_recent_logs(1)
        assert logs[0]["status"] == "error"
        assert logs[0]["details"]["error"] == "Insufficient training data"
    
    def test_log_s3_operation_success(self):
        """Test logging successful S3 operation"""
        logger = CloudLogger()
        
        logger.log_s3_operation(
            operation="upload",
            bucket="agri-models",
            key="prophet_model.pkl",
            details={"size_bytes": 1024}
        )
        
        logs = logger.get_recent_logs(1)
        assert logs[0]["service"] == "s3"
        assert logs[0]["operation_type"] == "upload"
        assert logs[0]["status"] == "success"
        assert logs[0]["details"]["bucket"] == "agri-models"
        assert logs[0]["details"]["key"] == "prophet_model.pkl"
    
    def test_log_s3_operation_error(self):
        """Test logging failed S3 operation"""
        logger = CloudLogger()
        
        logger.log_s3_operation(
            operation="download",
            bucket="agri-models",
            key="model.pkl",
            error="Access denied"
        )
        
        logs = logger.get_recent_logs(1)
        assert logs[0]["status"] == "error"
        assert logs[0]["details"]["error"] == "Access denied"
    
    def test_log_sns_operation_success(self):
        """Test logging successful SNS operation"""
        logger = CloudLogger()
        
        logger.log_sns_operation(
            operation="publish",
            topic_arn="arn:aws:sns:us-east-1:123:alerts",
            message="Storage temperature alert"
        )
        
        logs = logger.get_recent_logs(1)
        assert logs[0]["service"] == "sns"
        assert logs[0]["operation_type"] == "publish"
        assert logs[0]["status"] == "success"
        assert logs[0]["details"]["topic_arn"] == "arn:aws:sns:us-east-1:123:alerts"
    
    def test_log_sns_operation_long_message(self):
        """Test SNS logging truncates long messages"""
        logger = CloudLogger()
        
        long_message = "A" * 200
        
        logger.log_sns_operation(
            operation="publish",
            topic_arn="arn:aws:sns:us-east-1:123:alerts",
            message=long_message
        )
        
        logs = logger.get_recent_logs(1)
        assert len(logs[0]["details"]["message_preview"]) <= 103  # 100 + "..."
    
    def test_circular_buffer_limit(self):
        """Test that logger maintains only max_logs entries"""
        logger = CloudLogger(max_logs=5)
        
        # Add 10 logs
        for i in range(10):
            logger.log_ml_operation(
                operation="predict",
                duration=1.0,
                details={"iteration": i}
            )
        
        # Should only have 5 most recent
        assert logger.get_log_count() == 5
        
        logs = logger.get_recent_logs()
        # Most recent should be iteration 9
        assert logs[0]["details"]["iteration"] == 9
        # Oldest should be iteration 5
        assert logs[-1]["details"]["iteration"] == 5
    
    def test_get_recent_logs_with_count(self):
        """Test retrieving specific number of recent logs"""
        logger = CloudLogger()
        
        for i in range(10):
            logger.log_ml_operation(
                operation="predict",
                duration=1.0,
                details={"iteration": i}
            )
        
        logs = logger.get_recent_logs(3)
        assert len(logs) == 3
        # Should be most recent (9, 8, 7)
        assert logs[0]["details"]["iteration"] == 9
        assert logs[1]["details"]["iteration"] == 8
        assert logs[2]["details"]["iteration"] == 7
    
    def test_get_logs_by_service(self):
        """Test filtering logs by service"""
        logger = CloudLogger()
        
        logger.log_bedrock_call({"model": "claude"}, {"output": "test"})
        logger.log_dynamodb_operation("put_item", "table", {})
        logger.log_bedrock_call({"model": "claude"}, {"output": "test2"})
        
        bedrock_logs = logger.get_logs_by_service("bedrock")
        assert len(bedrock_logs) == 2
        
        dynamodb_logs = logger.get_logs_by_service("dynamodb")
        assert len(dynamodb_logs) == 1
    
    def test_get_logs_by_status(self):
        """Test filtering logs by status"""
        logger = CloudLogger()
        
        logger.log_ml_operation("train", 1.0, {})
        logger.log_ml_operation("predict", 1.0, {}, error="Failed")
        logger.log_ml_operation("train", 1.0, {})
        
        success_logs = logger.get_logs_by_status("success")
        assert len(success_logs) == 2
        
        error_logs = logger.get_logs_by_status("error")
        assert len(error_logs) == 1
    
    def test_get_error_logs(self):
        """Test retrieving only error logs"""
        logger = CloudLogger()
        
        logger.log_ml_operation("train", 1.0, {})
        logger.log_ml_operation("predict", 1.0, {}, error="Error 1")
        logger.log_bedrock_call({}, error="Error 2")
        
        error_logs = logger.get_error_logs()
        assert len(error_logs) == 2
    
    def test_clear_logs(self):
        """Test clearing all logs"""
        logger = CloudLogger()
        
        logger.log_ml_operation("train", 1.0, {})
        logger.log_ml_operation("predict", 1.0, {})
        
        assert logger.get_log_count() == 2
        
        logger.clear_logs()
        
        assert logger.get_log_count() == 0
    
    def test_get_stats(self):
        """Test getting log statistics"""
        logger = CloudLogger()
        
        logger.log_bedrock_call({"model": "claude"}, {"output": "test"})
        logger.log_bedrock_call({"model": "claude"}, error="Failed")
        logger.log_dynamodb_operation("put_item", "table", {})
        logger.log_ml_operation("train", 1.0, {})
        
        stats = logger.get_stats()
        
        assert stats["total_logs"] == 4
        assert stats["by_service"]["bedrock"] == 2
        assert stats["by_service"]["dynamodb"] == 1
        assert stats["by_service"]["ml_model"] == 1
        assert stats["by_status"]["success"] == 3
        assert stats["by_status"]["error"] == 1
        assert stats["error_count"] == 1
    
    def test_get_stats_empty(self):
        """Test stats with no logs"""
        logger = CloudLogger()
        
        stats = logger.get_stats()
        
        assert stats["total_logs"] == 0
        assert stats["by_service"] == {}
        assert stats["by_status"] == {}
        assert stats["error_count"] == 0
    
    def test_export_logs_json(self):
        """Test exporting logs as JSON"""
        logger = CloudLogger()
        
        logger.log_ml_operation("train", 1.0, {"model": "prophet"})
        
        json_str = logger.export_logs_json()
        logs = json.loads(json_str)
        
        assert len(logs) == 1
        assert logs[0]["service"] == "ml_model"
    
    def test_log_structure(self):
        """Test that all logs have required fields"""
        logger = CloudLogger()
        
        logger.log_bedrock_call({"model": "claude"}, {"output": "test"})
        
        logs = logger.get_recent_logs(1)
        log = logs[0]
        
        # Check required fields
        assert "timestamp" in log
        assert "operation_type" in log
        assert "service" in log
        assert "details" in log
        assert "status" in log


# Property-Based Tests
class TestCloudLoggerProperties:
    """Property-based tests for Cloud Logger"""
    
    @settings(deadline=None, max_examples=50)
    @given(
        num_operations=st.integers(min_value=1, max_value=20)
    )
    def test_property_comprehensive_logging(self, num_operations):
        """
        Property 11: Comprehensive AWS Operations Logging
        
        GIVEN multiple AWS operations
        WHEN operations are logged
        THEN all operations are captured with complete details
        
        Validates: Requirements 13.1, 13.2, 13.3
        """
        logger = CloudLogger(max_logs=100)
        
        for i in range(num_operations):
            logger.log_ml_operation(
                operation="predict",
                duration=float(i),
                details={"iteration": i}
            )
        
        logs = logger.get_recent_logs()
        
        # All operations should be logged (up to max_logs)
        assert len(logs) == min(num_operations, 100)
        
        # Each log should have required structure
        for log in logs:
            assert "timestamp" in log
            assert "operation_type" in log
            assert "service" in log
            assert "details" in log
            assert "status" in log
    
    @settings(deadline=None)
    @given(
        operation=st.sampled_from(["train", "predict", "evaluate"]),
        duration=st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False)
    )
    def test_property_structured_log_format(self, operation, duration):
        """
        Property 25: Structured Log Format
        
        GIVEN any operation and duration
        WHEN logged
        THEN log follows structured format with all required fields
        
        Validates: Requirement 13.5
        """
        logger = CloudLogger()
        
        logger.log_ml_operation(
            operation=operation,
            duration=duration,
            details={"test": "data"}
        )
        
        logs = logger.get_recent_logs(1)
        log = logs[0]
        
        # Verify structure
        assert isinstance(log["timestamp"], str)
        assert log["operation_type"] == operation
        assert log["service"] == "ml_model"
        assert isinstance(log["details"], dict)
        assert log["status"] in ["success", "error", "warning"]
        assert log["details"]["duration_seconds"] == round(duration, 2)
