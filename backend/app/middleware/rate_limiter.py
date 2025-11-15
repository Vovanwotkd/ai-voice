"""
Rate limiting middleware for WebSocket connections
Protects against DoS attacks and excessive usage
"""

import time
import logging
from typing import Dict, Tuple
from collections import defaultdict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RateLimitBucket:
    """Token bucket for rate limiting"""
    capacity: int
    tokens: float
    last_update: float = field(default_factory=time.time)
    refill_rate: float = 1.0  # tokens per second

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket
        Returns True if successful, False if rate limited
        """
        # Refill tokens based on time passed
        now = time.time()
        time_passed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + time_passed * self.refill_rate)
        self.last_update = now

        # Try to consume
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


class WebSocketRateLimiter:
    """
    Rate limiter for WebSocket connections
    Uses token bucket algorithm per IP/connection
    """

    def __init__(
        self,
        max_connections_per_ip: int = 5,
        max_messages_per_second: float = 10.0,
        max_bytes_per_second: int = 100_000,  # 100KB/s
        bucket_capacity: int = 20,
    ):
        self.max_connections_per_ip = max_connections_per_ip
        self.max_messages_per_second = max_messages_per_second
        self.max_bytes_per_second = max_bytes_per_second
        self.bucket_capacity = bucket_capacity

        # Track connections per IP
        self.connections: Dict[str, int] = defaultdict(int)

        # Token buckets for message rate limiting
        self.message_buckets: Dict[str, RateLimitBucket] = {}

        # Token buckets for bandwidth limiting
        self.bandwidth_buckets: Dict[str, RateLimitBucket] = {}

        # Cleanup old buckets periodically
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes

    def check_connection_limit(self, client_id: str) -> Tuple[bool, str]:
        """
        Check if client can establish new connection
        Returns (allowed, error_message)
        """
        ip = self._extract_ip(client_id)

        if self.connections[ip] >= self.max_connections_per_ip:
            logger.warning(f"Connection limit exceeded for IP: {ip}")
            return False, f"Too many connections from {ip}"

        self.connections[ip] += 1
        return True, ""

    def release_connection(self, client_id: str):
        """Release connection slot for client"""
        ip = self._extract_ip(client_id)
        if self.connections[ip] > 0:
            self.connections[ip] -= 1
            if self.connections[ip] == 0:
                del self.connections[ip]

    def check_message_rate(self, client_id: str) -> Tuple[bool, str]:
        """
        Check if client can send message (rate limit)
        Returns (allowed, error_message)
        """
        # Get or create bucket
        if client_id not in self.message_buckets:
            self.message_buckets[client_id] = RateLimitBucket(
                capacity=self.bucket_capacity,
                tokens=self.bucket_capacity,
                refill_rate=self.max_messages_per_second,
            )

        bucket = self.message_buckets[client_id]

        if bucket.consume(1):
            return True, ""
        else:
            logger.warning(f"Message rate limit exceeded for {client_id}")
            return False, "Message rate limit exceeded. Please slow down."

    def check_bandwidth(self, client_id: str, data_size: int) -> Tuple[bool, str]:
        """
        Check if client can send data (bandwidth limit)
        Returns (allowed, error_message)
        """
        # Get or create bucket
        if client_id not in self.bandwidth_buckets:
            self.bandwidth_buckets[client_id] = RateLimitBucket(
                capacity=self.max_bytes_per_second * 2,  # 2 second burst
                tokens=self.max_bytes_per_second * 2,
                refill_rate=self.max_bytes_per_second,
            )

        bucket = self.bandwidth_buckets[client_id]

        # Convert bytes to tokens (1 token = 1 byte)
        tokens_needed = data_size

        if bucket.consume(tokens_needed):
            return True, ""
        else:
            logger.warning(
                f"Bandwidth limit exceeded for {client_id}: {data_size} bytes"
            )
            return False, f"Bandwidth limit exceeded ({data_size} bytes)"

    def cleanup_old_buckets(self):
        """Remove inactive buckets to prevent memory leak"""
        now = time.time()

        if now - self.last_cleanup < self.cleanup_interval:
            return

        # Remove buckets inactive for > 10 minutes
        timeout = 600
        inactive_message = []
        inactive_bandwidth = []

        for client_id, bucket in self.message_buckets.items():
            if now - bucket.last_update > timeout:
                inactive_message.append(client_id)

        for client_id, bucket in self.bandwidth_buckets.items():
            if now - bucket.last_update > timeout:
                inactive_bandwidth.append(client_id)

        for client_id in inactive_message:
            del self.message_buckets[client_id]

        for client_id in inactive_bandwidth:
            del self.bandwidth_buckets[client_id]

        if inactive_message or inactive_bandwidth:
            logger.info(
                f"Cleaned up {len(inactive_message)} message buckets, "
                f"{len(inactive_bandwidth)} bandwidth buckets"
            )

        self.last_cleanup = now

    def _extract_ip(self, client_id: str) -> str:
        """Extract IP from client_id (format: ip:port or just id)"""
        if ":" in client_id:
            return client_id.split(":")[0]
        return client_id

    def get_stats(self) -> dict:
        """Get rate limiter statistics"""
        return {
            "active_connections": sum(self.connections.values()),
            "unique_ips": len(self.connections),
            "message_buckets": len(self.message_buckets),
            "bandwidth_buckets": len(self.bandwidth_buckets),
        }


# Global rate limiter instance
rate_limiter = WebSocketRateLimiter(
    max_connections_per_ip=5,
    max_messages_per_second=10.0,
    max_bytes_per_second=200_000,  # 200KB/s
    bucket_capacity=20,
)
