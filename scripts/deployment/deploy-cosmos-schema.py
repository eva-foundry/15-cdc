#!/usr/bin/env python3
"""Deploy Cosmos DB Schema for CDC

Purpose: Create 12 Cosmos DB containers for CDC system
Version: 1.0.0
Date: 2026-02-07
Status: Production-ready deployment script

Containers:
1. corpus_registry - Multi-corpus management with SLO tiers
2. case_registry - Stable case identities across external key changes
3. case_source_key - External identifiers (URLs, case IDs)
4. case_version - Versioned case states
5. case_text - Extracted text with language tracking
6. artifact - Content-addressable artifact storage
7. poll_run - CDC execution records
8. change_event - Detected changes with classifications
9. scope_definition - Corpus boundaries and polling frequencies
10. policy_version - Change classification policies
11. downstream_action - Action execution tracking
12. freshness_metric - SLO monitoring data

Usage:
    # Deploy all containers
    python deploy-cosmos-schema.py
    
    # Deploy specific containers only
    python deploy-cosmos-schema.py --containers corpus_registry,case_registry
    
    # Preview schema without deploying
    python deploy-cosmos-schema.py --dry-run
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Set UTF-8 encoding for Windows
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')


class CosmosSchemaDeployer:
    """Deploy CDC Cosmos DB schema"""
    
    # Schema definitions from minimal-schema-ddl.md
    CONTAINERS = {
        "corpus_registry": {
            "partition_key": "/corpus_id",
            "description": "Multi-corpus management with SLO tiers",
            "throughput": 400  # Serverless mode in production
        },
        "case_registry": {
            "partition_key": "/tribunal_id", 
            "description": "Stable case identities across external key changes",
            "throughput": 1000
        },
        "case_source_key": {
            "partition_key": "/external_key_type",
            "description": "External identifiers (URLs, case IDs)",
            "throughput": 400
        },
        "case_version": {
            "partition_key": "/case_id",
            "description": "Versioned case states",
            "throughput": 1000
        },
        "case_text": {
            "partition_key": "/case_version_id",
            "description": "Extracted text with language tracking",
            "throughput": 800
        },
        "artifact": {
            "partition_key": "/content_hash",
            "description": "Content-addressable artifact storage",
            "throughput": 800
        },
        "poll_run": {
            "partition_key": "/scope_id",
            "description": "CDC execution records",
            "throughput": 400
        },
        "change_event": {
            "partition_key": "/poll_run_id",
            "description": "Detected changes with classifications",
            "throughput": 1000
        },
        "scope_definition": {
            "partition_key": "/scope_id",
            "description": "Corpus boundaries and polling frequencies",
            "throughput": 400
        },
        "policy_version": {
            "partition_key": "/policy_id",
            "description": "Change classification policies",
            "throughput": 400
        },
        "downstream_action": {
            "partition_key": "/change_event_id",
            "description": "Action execution tracking",
            "throughput": 800
        },
        "freshness_metric": {
            "partition_key": "/corpus_id",
            "description": "SLO monitoring data",
            "throughput": 400
        }
    }
    
    def __init__(self, database_name: str = "cdc-jurisprudence", dry_run: bool = False):
        self.database_name = database_name
        self.dry_run = dry_run
        self.deployment_log = []
    
    def deploy_schema(self, container_filter: List[str] = None):
        """Deploy Cosmos DB containers"""
        try:
            from azure.cosmos import CosmosClient, PartitionKey
            from azure.identity import DefaultAzureCredential
            
            endpoint = os.getenv("AZURE_COSMOSDB_ENDPOINT")
            if not endpoint:
                raise ValueError("AZURE_COSMOSDB_ENDPOINT not set")
            
            credential = DefaultAzureCredential()
            client = CosmosClient(endpoint, credential)
            
            print("=" * 70)
            print("CDC Cosmos DB Schema Deployment")
            print("=" * 70)
            print(f"Database: {self.database_name}")
            print(f"Endpoint: {endpoint}")
            if self.dry_run:
                print("[INFO] DRY RUN MODE - No actual deployment")
            print()
            
            # Create database
            if not self.dry_run:
                database = client.create_database_if_not_exists(self.database_name)
                self.deployment_log.append(f"[PASS] Database '{self.database_name}' ready")
                print(f"[PASS] Database '{self.database_name}' ready")
            else:
                print(f"[INFO] Would create database: {self.database_name}")
            
            # Filter containers if specified
            containers_to_deploy = self.CONTAINERS
            if container_filter:
                containers_to_deploy = {k: v for k, v in self.CONTAINERS.items() if k in container_filter}
            
            # Create containers
            for container_name, config in containers_to_deploy.items():
                if self.dry_run:
                    print(f"[INFO] Would create container: {container_name}")
                    print(f"       Partition key: {config['partition_key']}")
                    print(f"       Throughput: {config['throughput']} RU/s")
                    print(f"       Description: {config['description']}")
                    self.deployment_log.append(f"[DRY-RUN] Container '{container_name}' planned")
                else:
                    try:
                        container = database.create_container_if_not_exists(
                            id=container_name,
                            partition_key=PartitionKey(path=config['partition_key']),
                            offer_throughput=config['throughput']
                        )
                        self.deployment_log.append(f"[PASS] Container '{container_name}' created")
                        print(f"[PASS] Container '{container_name}' created")
                        print(f"       Partition key: {config['partition_key']}")
                        print(f"       Throughput: {config['throughput']} RU/s")
                    except Exception as e:
                        self.deployment_log.append(f"[FAIL] Container '{container_name}': {str(e)}")
                        print(f"[FAIL] Container '{container_name}': {str(e)}")
                        raise
            
            print("\n" + "=" * 70)
            print(f"Deployment Summary: {len(containers_to_deploy)} containers processed")
            print("=" * 70)
            
            # Save deployment log
            self._save_deployment_log()
            
            if not self.dry_run:
                print("\n[PASS] Schema deployment complete!")
                print("\nNext Steps:")
                print("1. Create Azure Storage queues (run: python scripts/deployment/create-storage-queues.py)")
                print("2. Deploy CDC functions (run: python scripts/deployment/deploy-cdc-functions.py)")
                print("3. Configure monitoring (Application Insights)")
            
            return True
            
        except Exception as e:
            print(f"\n[FAIL] Schema deployment failed: {str(e)}")
            self.deployment_log.append(f"[FAIL] Deployment failed: {str(e)}")
            self._save_deployment_log()
            return False
    
    def _save_deployment_log(self):
        """Save deployment log to file"""
        log_dir = Path("logs/deployment")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"cosmos-schema-deployment-{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_file.write_text("\n".join(self.deployment_log))
        print(f"\n[INFO] Deployment log saved to: {log_file}")


def main():
    parser = argparse.ArgumentParser(description="Deploy CDC Cosmos DB Schema")
    parser.add_argument(
        "--database",
        default="cdc-jurisprudence",
        help="Database name (default: cdc-jurisprudence)"
    )
    parser.add_argument(
        "--containers",
        help="Comma-separated list of containers to deploy (default: all)",
        default=None
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview schema without deploying"
    )
    
    args = parser.parse_args()
    
    container_filter = args.containers.split(',') if args.containers else None
    
    deployer = CosmosSchemaDeployer(database_name=args.database, dry_run=args.dry_run)
    success = deployer.deploy_schema(container_filter=container_filter)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
