"""
API Key management utilities and CLI commands.

Provides administrative functions for managing API keys.
"""

import click
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from ..database.session import get_db_session
from .api_key_auth import (
    APIKeyAuth,
    APIKeyPermission,
    APIKeyTable,
    APIKeyUsageLog,
    create_api_key,
)


class APIKeyManager:
    """Service class for API key management operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.auth_service = APIKeyAuth(db)
    
    def create_api_key(
        self,
        name: str,
        permission_level: APIKeyPermission,
        description: str = None,
        expires_in_days: int = None,
        rate_limit_per_hour: int = 1000,
        rate_limit_per_day: int = 10000,
        created_by: str = None,
    ) -> dict:
        """
        Create a new API key with specified parameters.
        
        Args:
            name: Name for the API key
            permission_level: Permission level
            description: Optional description
            expires_in_days: Number of days until expiration (None for no expiration)
            rate_limit_per_hour: Hourly rate limit
            rate_limit_per_day: Daily rate limit
            created_by: Who created the key
            
        Returns:
            Dictionary with key info including the full key
        """
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        response = create_api_key(
            name=name,
            permission_level=permission_level,
            db=self.db,
            description=description,
            expires_at=expires_at,
            rate_limit_per_hour=rate_limit_per_hour,
            rate_limit_per_day=rate_limit_per_day,
            created_by=created_by,
        )
        
        return {
            "id": str(response.id),
            "name": response.name,
            "key": response.key,
            "permission_level": response.permission_level,
            "expires_at": response.expires_at,
            "rate_limits": {
                "per_hour": response.rate_limit_per_hour,
                "per_day": response.rate_limit_per_day,
            },
        }
    
    def list_api_keys(self, include_revoked: bool = False) -> List[dict]:
        """
        List all API keys with their status and usage info.
        
        Args:
            include_revoked: Whether to include revoked keys
            
        Returns:
            List of API key information
        """
        query = self.db.query(APIKeyTable)
        
        if not include_revoked:
            query = query.filter(APIKeyTable.status != "revoked")
        
        api_keys = query.all()
        
        result = []
        for key in api_keys:
            result.append({
                "id": str(key.id),
                "name": key.name,
                "description": key.description,
                "permission_level": key.permission_level,
                "status": key.status,
                "created_at": key.created_at,
                "expires_at": key.expires_at,
                "last_used_at": key.last_used_at,
                "usage_count": key.usage_count,
                "total_requests": key.total_requests,
                "failed_requests": key.failed_requests,
                "rate_limits": {
                    "per_hour": key.rate_limit_per_hour,
                    "per_day": key.rate_limit_per_day,
                },
                "key_prefix": key.key_prefix,
            })
        
        return result
    
    def get_api_key_details(self, api_key_id: str) -> Optional[dict]:
        """
        Get detailed information about a specific API key.
        
        Args:
            api_key_id: ID of the API key
            
        Returns:
            Detailed API key information or None if not found
        """
        try:
            key_uuid = UUID(api_key_id)
        except ValueError:
            return None
        
        api_key = self.db.query(APIKeyTable).filter(
            APIKeyTable.id == key_uuid
        ).first()
        
        if not api_key:
            return None
        
        # Get recent usage logs
        recent_logs = self.db.query(APIKeyUsageLog).filter(
            APIKeyUsageLog.api_key_id == key_uuid
        ).order_by(
            APIKeyUsageLog.timestamp.desc()
        ).limit(10).all()
        
        return {
            "id": str(api_key.id),
            "name": api_key.name,
            "description": api_key.description,
            "permission_level": api_key.permission_level,
            "scopes": api_key.scopes,
            "status": api_key.status,
            "created_at": api_key.created_at,
            "expires_at": api_key.expires_at,
            "last_used_at": api_key.last_used_at,
            "revoked_at": api_key.revoked_at,
            "revoked_reason": api_key.revoked_reason,
            "usage_stats": {
                "total_requests": api_key.total_requests,
                "failed_requests": api_key.failed_requests,
                "success_rate": (api_key.total_requests - api_key.failed_requests) / max(api_key.total_requests, 1),
            },
            "rate_limits": {
                "per_hour": api_key.rate_limit_per_hour,
                "per_day": api_key.rate_limit_per_day,
            },
            "security": {
                "allowed_ips": api_key.allowed_ips,
                "user_agent_patterns": api_key.user_agent_patterns,
                "last_request_ip": api_key.last_request_ip,
            },
            "recent_usage": [
                {
                    "timestamp": log.timestamp,
                    "endpoint": log.endpoint,
                    "method": log.method,
                    "status_code": log.status_code,
                    "response_time_ms": log.response_time_ms,
                    "ip_address": log.ip_address,
                }
                for log in recent_logs
            ],
        }
    
    def revoke_api_key(self, api_key_id: str, reason: str = None) -> bool:
        """
        Revoke an API key.
        
        Args:
            api_key_id: ID of the API key to revoke
            reason: Optional reason for revocation
            
        Returns:
            True if successfully revoked, False if not found
        """
        try:
            key_uuid = UUID(api_key_id)
        except ValueError:
            return False
        
        return self.auth_service.revoke_api_key(key_uuid, reason)
    
    def update_rate_limits(
        self,
        api_key_id: str,
        rate_limit_per_hour: int = None,
        rate_limit_per_day: int = None,
    ) -> bool:
        """
        Update rate limits for an API key.
        
        Args:
            api_key_id: ID of the API key
            rate_limit_per_hour: New hourly rate limit
            rate_limit_per_day: New daily rate limit
            
        Returns:
            True if updated successfully, False if not found
        """
        try:
            key_uuid = UUID(api_key_id)
        except ValueError:
            return False
        
        api_key = self.db.query(APIKeyTable).filter(
            APIKeyTable.id == key_uuid
        ).first()
        
        if not api_key:
            return False
        
        if rate_limit_per_hour is not None:
            api_key.rate_limit_per_hour = rate_limit_per_hour
        
        if rate_limit_per_day is not None:
            api_key.rate_limit_per_day = rate_limit_per_day
        
        self.db.commit()
        return True
    
    def get_usage_statistics(self, days: int = 30) -> dict:
        """
        Get usage statistics across all API keys.
        
        Args:
            days: Number of days to include in statistics
            
        Returns:
            Usage statistics dictionary
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Total requests in period
        total_requests = self.db.query(APIKeyUsageLog).filter(
            APIKeyUsageLog.timestamp >= since_date
        ).count()
        
        # Failed requests in period
        failed_requests = self.db.query(APIKeyUsageLog).filter(
            APIKeyUsageLog.timestamp >= since_date,
            APIKeyUsageLog.status_code >= 400
        ).count()
        
        # Active API keys
        active_keys = self.db.query(APIKeyTable).filter(
            APIKeyTable.status == "active"
        ).count()
        
        # Most used endpoints
        from sqlalchemy import func
        popular_endpoints = self.db.query(
            APIKeyUsageLog.endpoint,
            func.count(APIKeyUsageLog.id).label('count')
        ).filter(
            APIKeyUsageLog.timestamp >= since_date
        ).group_by(APIKeyUsageLog.endpoint).order_by(
            func.count(APIKeyUsageLog.id).desc()
        ).limit(10).all()
        
        return {
            "period_days": days,
            "total_requests": total_requests,
            "failed_requests": failed_requests,
            "success_rate": (total_requests - failed_requests) / max(total_requests, 1),
            "active_api_keys": active_keys,
            "popular_endpoints": [
                {"endpoint": ep.endpoint, "requests": ep.count}
                for ep in popular_endpoints
            ],
        }


# CLI commands for API key management
@click.group()
def api_key_cli():
    """API Key management commands."""
    pass


@api_key_cli.command()
@click.option("--name", required=True, help="Name for the API key")
@click.option("--permission", type=click.Choice(['read_only', 'content_creator', 'power_user', 'admin']), 
              default='read_only', help="Permission level")
@click.option("--description", help="Description for the API key")
@click.option("--expires-in-days", type=int, help="Number of days until expiration")
@click.option("--rate-limit-hour", type=int, default=1000, help="Hourly rate limit")
@click.option("--rate-limit-day", type=int, default=10000, help="Daily rate limit")
@click.option("--created-by", help="Who is creating this key")
def create(name, permission, description, expires_in_days, rate_limit_hour, rate_limit_day, created_by):
    """Create a new API key."""
    with get_db_session() as db:
        manager = APIKeyManager(db)
        
        permission_level = APIKeyPermission(permission)
        result = manager.create_api_key(
            name=name,
            permission_level=permission_level,
            description=description,
            expires_in_days=expires_in_days,
            rate_limit_per_hour=rate_limit_hour,
            rate_limit_per_day=rate_limit_day,
            created_by=created_by,
        )
        
        click.echo(f"✅ API Key created successfully!")
        click.echo(f"ID: {result['id']}")
        click.echo(f"Name: {result['name']}")
        click.echo(f"Key: {click.style(result['key'], fg='green', bold=True)}")
        click.echo(f"Permission Level: {result['permission_level']}")
        if result['expires_at']:
            click.echo(f"Expires: {result['expires_at']}")
        click.echo(f"Rate Limits: {result['rate_limits']['per_hour']}/hour, {result['rate_limits']['per_day']}/day")
        click.echo("\n⚠️  Save this key now - it won't be shown again!")


@api_key_cli.command()
@click.option("--include-revoked", is_flag=True, help="Include revoked keys")
def list(include_revoked):
    """List all API keys."""
    with get_db_session() as db:
        manager = APIKeyManager(db)
        keys = manager.list_api_keys(include_revoked=include_revoked)
        
        if not keys:
            click.echo("No API keys found.")
            return
        
        click.echo(f"Found {len(keys)} API key(s):\n")
        
        for key in keys:
            status_color = "green" if key["status"] == "active" else "red"
            click.echo(f"🔑 {click.style(key['name'], bold=True)}")
            click.echo(f"   ID: {key['id']}")
            click.echo(f"   Status: {click.style(key['status'], fg=status_color)}")
            click.echo(f"   Permission: {key['permission_level']}")
            click.echo(f"   Usage: {key['total_requests']} requests")
            if key['last_used_at']:
                click.echo(f"   Last used: {key['last_used_at']}")
            click.echo()


@api_key_cli.command()
@click.argument("api_key_id")
def details(api_key_id):
    """Get detailed information about an API key."""
    with get_db_session() as db:
        manager = APIKeyManager(db)
        details = manager.get_api_key_details(api_key_id)
        
        if not details:
            click.echo("❌ API key not found.")
            return
        
        click.echo(f"🔑 {click.style(details['name'], bold=True)}")
        click.echo(f"ID: {details['id']}")
        click.echo(f"Status: {click.style(details['status'], fg='green' if details['status'] == 'active' else 'red')}")
        click.echo(f"Permission Level: {details['permission_level']}")
        click.echo(f"Created: {details['created_at']}")
        
        if details['expires_at']:
            click.echo(f"Expires: {details['expires_at']}")
        
        if details['revoked_at']:
            click.echo(f"Revoked: {details['revoked_at']}")
            if details['revoked_reason']:
                click.echo(f"Reason: {details['revoked_reason']}")
        
        stats = details['usage_stats']
        click.echo(f"\n📊 Usage Statistics:")
        click.echo(f"   Total Requests: {stats['total_requests']}")
        click.echo(f"   Failed Requests: {stats['failed_requests']}")
        click.echo(f"   Success Rate: {stats['success_rate']:.1%}")
        
        if details['recent_usage']:
            click.echo(f"\n📈 Recent Usage (last 10 requests):")
            for usage in details['recent_usage']:
                status_color = "green" if usage['status_code'] < 400 else "red"
                click.echo(f"   {usage['timestamp']} - {usage['method']} {usage['endpoint']} - "
                          f"{click.style(str(usage['status_code']), fg=status_color)}")


@api_key_cli.command()
@click.argument("api_key_id")
@click.option("--reason", help="Reason for revocation")
def revoke(api_key_id, reason):
    """Revoke an API key."""
    with get_db_session() as db:
        manager = APIKeyManager(db)
        
        if manager.revoke_api_key(api_key_id, reason):
            click.echo("✅ API key revoked successfully.")
        else:
            click.echo("❌ API key not found.")


@api_key_cli.command()
@click.option("--days", type=int, default=30, help="Number of days for statistics")
def stats(days):
    """Show usage statistics."""
    with get_db_session() as db:
        manager = APIKeyManager(db)
        statistics = manager.get_usage_statistics(days=days)
        
        click.echo(f"📊 API Usage Statistics (last {statistics['period_days']} days)\n")
        click.echo(f"Total Requests: {statistics['total_requests']:,}")
        click.echo(f"Failed Requests: {statistics['failed_requests']:,}")
        click.echo(f"Success Rate: {statistics['success_rate']:.1%}")
        click.echo(f"Active API Keys: {statistics['active_api_keys']}")
        
        if statistics['popular_endpoints']:
            click.echo(f"\n🔥 Most Popular Endpoints:")
            for i, endpoint in enumerate(statistics['popular_endpoints'], 1):
                click.echo(f"   {i}. {endpoint['endpoint']} - {endpoint['requests']:,} requests")


if __name__ == "__main__":
    api_key_cli()