import pytest
from cloud_storage_tier import (
    process_storage_tenants,
    monitor_replication_latency
)


# 1. Invalid input
def test_invalid_inputs():
    with pytest.raises(ValueError):
        process_storage_tenants("invalid", 10)

    with pytest.raises(ValueError):
        process_storage_tenants([], -1)


# 2. Single active hot tenant
def test_single_active_hot_tenant():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "has_backup_vault": False,
        "buckets": [
            {"size_gb": 100, "corrupted": False, "egress_gb": 50}
        ]
    }]
    result = process_storage_tenants(tenants, 10)
    assert result["total_billed"] == 2.5
    assert result["status"] == "BILLED"


# 3. Inactive tenant
def test_inactive_tenant():
    result = process_storage_tenants(
        [{"account_active": False}], 10
    )
    assert result["status"] == "ZERO_USAGE"


# 4. Different storage tiers
def test_storage_tiers():
    tenants = [
        {"account_active": True, "tier": "hot",
         "buckets": [{"size_gb": 100}]},
        {"account_active": True, "tier": "cool",
         "buckets": [{"size_gb": 100}]},
        {"account_active": True, "tier": "archive",
         "buckets": [{"size_gb": 100}]}
    ]
    result = process_storage_tenants(tenants, 10)
    assert result["total_billed"] == 4.5
    assert result["status"] == "BILLED"


# 5. Default hot tier
def test_default_tier():
    tenants = [{
        "account_active": True,
        "buckets": [{"size_gb": 100}]
    }]
    result = process_storage_tenants(tenants, 10)
    assert result["total_billed"] == 2.5


# 6. Unknown tier
def test_unknown_tier():
    tenants = [
        {"account_active": True, "tier": "unknown"}
    ]
    result = process_storage_tenants(tenants, 10)
    assert result["status"] == "ZERO_USAGE"


# 7. Invalid bucket size
def test_invalid_bucket_size():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "buckets": [
            {"size_gb": 0},
            {"size_gb": -10}
        ]
    }]
    result = process_storage_tenants(tenants, 10)
    assert result["status"] == "ZERO_USAGE"


# 8. Large and normal bucket
def test_bucket_size_conditions():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "buckets": [
            {"size_gb": 600},
            {"size_gb": 100}
        ]
    }]
    result = process_storage_tenants(tenants, 10)
    assert result["total_billed"] == 16.0


# 9. Boundary bucket size
def test_boundary_bucket_size():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "buckets": [{"size_gb": 500}]
    }]
    result = process_storage_tenants(tenants, 10)
    assert result["total_billed"] == 12.5


# 10. Corrupted hot bucket
def test_corrupted_bucket():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "buckets": [
            {"size_gb": 100, "corrupted": True,
             "egress_gb": 120}
        ]
    }]
    result = process_storage_tenants(tenants, 10)
    assert result["total_billed"] == 1.6


# 11. Corrupted archive bucket
def test_archive_corrupted_bucket():
    tenants = [{
        "account_active": True,
        "tier": "archive",
        "has_backup_vault": True,
        "buckets": [
            {"size_gb": 100, "corrupted": True},
            {"size_gb": 200}
        ]
    }]
    result = process_storage_tenants(tenants, 10)
    assert result["total_billed"] == 10


# 12. Egress conditions
def test_egress_conditions():
    tenants = [{
        "account_active": True,
        "tier": "cool",
        "buckets": [
            {"size_gb": 100, "egress_gb": 150},
            {"size_gb": 100, "egress_gb": 50}
        ]
    }]
    result = process_storage_tenants(tenants, 10)
    assert result["total_billed"] == 7.0


# 13. Egress boundary
def test_egress_boundary():
    tenants = [{
        "account_active": True,
        "tier": "cool",
        "buckets": [
            {"size_gb": 100, "egress_gb": 100}
        ]
    }]
    result = process_storage_tenants(tenants, 10)
    assert result["total_billed"] == 1.5


# 14. Backup vault
def test_backup_vault():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "has_backup_vault": True,
        "buckets": [{"size_gb": 100}]
    }]
    result = process_storage_tenants(tenants, 10)
    assert result["total_billed"] == 12.5


# 15. Audit flagged
def test_audit_flagged():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "buckets": [
            {"size_gb": 0},
            {"size_gb": -1},
            {"size_gb": 0},
            {"size_gb": -2},
            {"size_gb": 0}
        ]
    }]
    result = process_storage_tenants(tenants, 10)
    assert result["status"] == "AUDIT_FLAGGED"


# 16. Zero usage
def test_zero_usage():
    result = process_storage_tenants([], 10)
    assert result["status"] == "ZERO_USAGE"


# 17. Missing buckets
def test_missing_buckets():
    tenants = [{
        "account_active": True,
        "tier": "hot"
    }]
    result = process_storage_tenants(tenants, 10)
    assert result["status"] == "ZERO_USAGE"


# 18. No replication data
def test_no_replication_data():
    assert monitor_replication_latency([]) == "NO_DATA"


# 19. Replication synchronized
def test_replication_synced():
    assert monitor_replication_latency(
        [[100, 150, 180], [50, 100]]
    ) == "SYNCED"


# 20. Single high latency
def test_single_high_latency():
    assert monitor_replication_latency(
        [[250, 100, 150]]
    ) == "SYNCED"


# 21. Replication alert
def test_replication_alert():
    assert monitor_replication_latency(
        [[250, 300]]
    ) == "SYNC_LAG_ALERT"


# 22. Latency reset
def test_latency_reset():
    assert monitor_replication_latency(
        [[250, 100, 250, 300]]
    ) == "SYNC_LAG_ALERT"


# 23. Empty node logs
def test_empty_node_logs():
    assert monitor_replication_latency(
        [[], [100, 150]]
    ) == "SYNCED"