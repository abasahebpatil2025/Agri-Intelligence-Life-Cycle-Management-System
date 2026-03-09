"""
Cloud Logger Component

Structured logging for AWS operations and ML inferences.
Uses circular buffer (deque) for in-memory log storage.

Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6
"""

from collections import deque
from datetime import datetime
from typing import Dict, List, Any, Optional
import json


class CloudLogger:
    """
    Logs AWS cloud operations and ML inferences with structured format.
    
    Maintains a circular buffer of the most recent 100 log entries.
    All logs include timestamp, operation_type, service, details, and status.
    """
    
    def __init__(self, max_logs: int = 100):
        """
        Initialize CloudLogger.
        
        Args:
            max_logs: Maximum number of logs to retain (default: 100)
        """
        self._logs = deque(maxlen=max_logs)
        self.max_logs = max_logs
    
    def _create_log_entry(
        self,
        operation_type: str,
        service: str,
        details: Dict[str, Any],
        status: str = "success"
    ) -> Dict[str, Any]:
        """
        Create a structured log entry.
        
        Args:
            operation_type: Type of operation (e.g., "api_call", "write", "read")
            service: AWS service name (e.g., "bedrock", "dynamodb")
            details: Operation-specific details
            status: Operation status (success, error, warning)
            
        Returns:
            Structured log entry dictionary
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "operation_type": operation_type,
            "service": service,
            "details": details,
            "status": status
        }
    
    def log_bedrock_call(
        self,
        request: Dict[str, Any],
        response: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Log AWS Bedrock API call.
        
        Args:
            request: Request details (model, prompt, parameters)
            response: Response details (output, tokens, etc.)
            error: Error message if call failed
        """
        status = "error" if error else "success"
        
        details = {
            "model": request.get("model", "unknown"),
            "prompt_length": len(str(request.get("prompt", ""))),
            "request_params": request.get("parameters", {}),
        }
        
        if response:
            details["response_length"] = len(str(response.get("output", "")))
            details["tokens_used"] = response.get("tokens", 0)
        
        if error:
            details["error"] = error
        
        log_entry = self._create_log_entry(
            operation_type="api_call",
            service="bedrock",
            details=details,
            status=status
        )
        
        self._logs.append(log_entry)
    
    def log_dynamodb_operation(
        self,
        operation: str,
        table: str,
        details: Dict[str, Any],
        error: Optional[str] = None
    ) -> None:
        """
        Log DynamoDB operation.
        
        Args:
            operation: Operation type (put_item, get_item, query, scan, etc.)
            table: Table name
            details: Operation-specific details (keys, attributes, etc.)
            error: Error message if operation failed
        """
        status = "error" if error else "success"
        
        log_details = {
            "operation": operation,
            "table": table,
            **details
        }
        
        if error:
            log_details["error"] = error
        
        log_entry = self._create_log_entry(
            operation_type=operation,
            service="dynamodb",
            details=log_details,
            status=status
        )
        
        self._logs.append(log_entry)
    
    def log_ml_operation(
        self,
        operation: str,
        duration: float,
        details: Dict[str, Any],
        error: Optional[str] = None
    ) -> None:
        """
        Log ML model training or inference operation.
        
        Args:
            operation: Operation type (train, predict, evaluate)
            duration: Operation duration in seconds
            details: Operation-specific details (model, data size, metrics)
            error: Error message if operation failed
        """
        status = "error" if error else "success"
        
        log_details = {
            "operation": operation,
            "duration_seconds": round(duration, 2),
            **details
        }
        
        if error:
            log_details["error"] = error
        
        log_entry = self._create_log_entry(
            operation_type=operation,
            service="ml_model",
            details=log_details,
            status=status
        )
        
        self._logs.append(log_entry)
    
    def log_s3_operation(
        self,
        operation: str,
        bucket: str,
        key: str,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Log AWS S3 operation.
        
        Args:
            operation: Operation type (upload, download, delete, list)
            bucket: S3 bucket name
            key: S3 object key
            details: Additional operation details
            error: Error message if operation failed
        """
        status = "error" if error else "success"
        
        log_details = {
            "operation": operation,
            "bucket": bucket,
            "key": key
        }
        
        if details:
            log_details.update(details)
        
        if error:
            log_details["error"] = error
        
        log_entry = self._create_log_entry(
            operation_type=operation,
            service="s3",
            details=log_details,
            status=status
        )
        
        self._logs.append(log_entry)
    
    def log_sns_operation(
        self,
        operation: str,
        topic_arn: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Log AWS SNS operation.
        
        Args:
            operation: Operation type (publish, subscribe, unsubscribe)
            topic_arn: SNS topic ARN
            message: Message content (truncated for logging)
            details: Additional operation details
            error: Error message if operation failed
        """
        status = "error" if error else "success"
        
        log_details = {
            "operation": operation,
            "topic_arn": topic_arn,
            "message_preview": message[:100] + "..." if len(message) > 100 else message
        }
        
        if details:
            log_details.update(details)
        
        if error:
            log_details["error"] = error
        
        log_entry = self._create_log_entry(
            operation_type=operation,
            service="sns",
            details=log_details,
            status=status
        )
        
        self._logs.append(log_entry)
    def log_sns_operation(
        self,
        operation: str,
        topic_arn: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Log AWS SNS operation.

        Args:
            operation: Operation type (publish, subscribe, unsubscribe)
            topic_arn: SNS topic ARN
            message: Message content (truncated for logging)
            details: Additional operation details
            error: Error message if operation failed
        """
        status = "error" if error else "success"

        log_details = {
            "operation": operation,
            "topic_arn": topic_arn,
            "message_preview": message[:100] + "..." if len(message) > 100 else message
        }

        if details:
            log_details.update(details)

        if error:
            log_details["error"] = error

        log_entry = self._create_log_entry(
            operation_type=operation,
            service="sns",
            details=log_details,
            status=status
        )

        self._logs.append(log_entry)

    def log_operation(
        self,
        operation_type: str,
        service: str,
        details: Dict[str, Any],
        error: Optional[str] = None
    ) -> None:
        """
        Log a generic operation.

        Args:
            operation_type: Type of operation (e.g., "simulation", "data_generation")
            service: Service or component name (e.g., "iot_simulator", "price_forecaster")
            details: Operation-specific details
            error: Error message if operation failed
        """
        status = "error" if error else "success"

        log_entry = self._create_log_entry(
            operation_type=operation_type,
            service=service,
            details=details,
            status=status
        )

        self._logs.append(log_entry)
    
    def log_operation(
        self,
        operation_type: str,
        service: str,
        details: Dict[str, Any],
        error: Optional[str] = None
    ) -> None:
        """
        Log a generic operation.
        
        Args:
            operation_type: Type of operation (e.g., "simulation", "data_generation")
            service: Service or component name (e.g., "iot_simulator", "price_forecaster")
            details: Operation-specific details
            error: Error message if operation failed
        """
        status = "error" if error else "success"
        
        log_entry = self._create_log_entry(
            operation_type=operation_type,
            service=service,
            details=details,
            status=status
        )
        
        self._logs.append(log_entry)
    
    def get_recent_logs(self, count: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve recent log entries.
        
        Args:
            count: Number of logs to retrieve (default: all logs)
            
        Returns:
            List of log entries (most recent first)
        """
        if count is None:
            count = len(self._logs)
        
        # Return most recent logs (reverse order)
        return list(reversed(list(self._logs)))[:count]
    
    def get_logs_by_service(self, service: str) -> List[Dict[str, Any]]:
        """
        Get logs filtered by service.
        
        Args:
            service: Service name (bedrock, dynamodb, s3, sns, ml_model)
            
        Returns:
            List of log entries for the specified service
        """
        return [
            log for log in self._logs
            if log["service"] == service
        ]
    
    def get_logs_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Get logs filtered by status.
        
        Args:
            status: Status (success, error, warning)
            
        Returns:
            List of log entries with the specified status
        """
        return [
            log for log in self._logs
            if log["status"] == status
        ]
    
    def get_error_logs(self) -> List[Dict[str, Any]]:
        """
        Get all error logs.
        
        Returns:
            List of log entries with error status
        """
        return self.get_logs_by_status("error")
    
    def clear_logs(self) -> None:
        """Clear all log entries."""
        self._logs.clear()
    
    def get_log_count(self) -> int:
        """
        Get total number of logs.
        
        Returns:
            Number of log entries
        """
        return len(self._logs)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get logging statistics.
        
        Returns:
            Dictionary with log statistics
        """
        total = len(self._logs)
        
        if total == 0:
            return {
                "total_logs": 0,
                "by_service": {},
                "by_status": {},
                "error_count": 0
            }
        
        # Count by service
        by_service = {}
        for log in self._logs:
            service = log["service"]
            by_service[service] = by_service.get(service, 0) + 1
        
        # Count by status
        by_status = {}
        for log in self._logs:
            status = log["status"]
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            "total_logs": total,
            "by_service": by_service,
            "by_status": by_status,
            "error_count": by_status.get("error", 0)
        }
    
    def export_logs_json(self) -> str:
        """
        Export all logs as JSON string.
        
        Returns:
            JSON string of all logs
        """
        return json.dumps(list(self._logs), indent=2)
