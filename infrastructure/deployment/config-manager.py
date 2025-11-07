"""
Environment Configuration Manager
Manages environment-specific configurations for deployments
"""

import os
import json
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class ServiceConfig:
    """Service configuration"""
    name: str
    image: str
    port: int
    cpu: str
    memory: str
    min_instances: int
    max_instances: int
    timeout: int
    env_vars: Dict[str, str]
    secrets: Dict[str, str]


@dataclass
class EnvironmentConfig:
    """Environment configuration"""
    name: str
    gcp_project_id: str
    gcp_region: str
    domain: str
    services: Dict[str, ServiceConfig]


class ConfigManager:
    """Manage environment-specific configurations"""
    
    def __init__(self, config_dir: str = "infrastructure/deployment/configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def load_environment_config(self, environment: str) -> EnvironmentConfig:
        """
        Load configuration for specific environment
        
        Args:
            environment: Environment name (development, staging, production)
            
        Returns:
            EnvironmentConfig object
        """
        config_file = self.config_dir / f"{environment}.yaml"
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Parse service configs
        services = {}
        for service_name, service_data in config_data.get('services', {}).items():
            services[service_name] = ServiceConfig(
                name=service_name,
                image=service_data.get('image', ''),
                port=service_data.get('port', 8080),
                cpu=service_data.get('cpu', '1'),
                memory=service_data.get('memory', '512Mi'),
                min_instances=service_data.get('min_instances', 0),
                max_instances=service_data.get('max_instances', 10),
                timeout=service_data.get('timeout', 300),
                env_vars=service_data.get('env_vars', {}),
                secrets=service_data.get('secrets', {})
            )
        
        return EnvironmentConfig(
            name=environment,
            gcp_project_id=config_data.get('gcp_project_id', ''),
            gcp_region=config_data.get('gcp_region', 'us-central1'),
            domain=config_data.get('domain', ''),
            services=services
        )
    
    def save_environment_config(self, config: EnvironmentConfig):
        """
        Save environment configuration to file
        
        Args:
            config: EnvironmentConfig object to save
        """
        config_file = self.config_dir / f"{config.name}.yaml"
        
        config_data = {
            'gcp_project_id': config.gcp_project_id,
            'gcp_region': config.gcp_region,
            'domain': config.domain,
            'services': {}
        }
        
        for service_name, service_config in config.services.items():
            config_data['services'][service_name] = {
                'image': service_config.image,
                'port': service_config.port,
                'cpu': service_config.cpu,
                'memory': service_config.memory,
                'min_instances': service_config.min_instances,
                'max_instances': service_config.max_instances,
                'timeout': service_config.timeout,
                'env_vars': service_config.env_vars,
                'secrets': service_config.secrets
            }
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
    
    def generate_cloud_run_yaml(
        self,
        service_config: ServiceConfig,
        environment: str
    ) -> str:
        """
        Generate Cloud Run service YAML
        
        Args:
            service_config: Service configuration
            environment: Environment name
            
        Returns:
            YAML string for Cloud Run service
        """
        service_yaml = {
            'apiVersion': 'serving.knative.dev/v1',
            'kind': 'Service',
            'metadata': {
                'name': f"utxoiq-{service_config.name}",
                'labels': {
                    'environment': environment,
                    'service': service_config.name
                }
            },
            'spec': {
                'template': {
                    'metadata': {
                        'annotations': {
                            'autoscaling.knative.dev/minScale': str(service_config.min_instances),
                            'autoscaling.knative.dev/maxScale': str(service_config.max_instances)
                        }
                    },
                    'spec': {
                        'containerConcurrency': 80,
                        'timeoutSeconds': service_config.timeout,
                        'containers': [
                            {
                                'image': service_config.image,
                                'ports': [
                                    {
                                        'containerPort': service_config.port
                                    }
                                ],
                                'resources': {
                                    'limits': {
                                        'cpu': service_config.cpu,
                                        'memory': service_config.memory
                                    }
                                },
                                'env': []
                            }
                        ]
                    }
                }
            }
        }
        
        # Add environment variables
        for key, value in service_config.env_vars.items():
            service_yaml['spec']['template']['spec']['containers'][0]['env'].append({
                'name': key,
                'value': value
            })
        
        # Add secrets
        for key, secret_ref in service_config.secrets.items():
            service_yaml['spec']['template']['spec']['containers'][0]['env'].append({
                'name': key,
                'valueFrom': {
                    'secretKeyRef': {
                        'name': secret_ref,
                        'key': 'latest'
                    }
                }
            })
        
        return yaml.dump(service_yaml, default_flow_style=False, sort_keys=False)
    
    def get_deployment_command(
        self,
        service_config: ServiceConfig,
        environment: str,
        gcp_project_id: str,
        gcp_region: str
    ) -> str:
        """
        Generate gcloud deployment command
        
        Args:
            service_config: Service configuration
            environment: Environment name
            gcp_project_id: GCP project ID
            gcp_region: GCP region
            
        Returns:
            gcloud command string
        """
        service_name = f"utxoiq-{service_config.name}"
        if environment != "production":
            service_name += f"-{environment}"
        
        cmd_parts = [
            "gcloud run deploy",
            service_name,
            f"--image {service_config.image}",
            f"--region {gcp_region}",
            f"--platform managed",
            f"--port {service_config.port}",
            f"--cpu {service_config.cpu}",
            f"--memory {service_config.memory}",
            f"--min-instances {service_config.min_instances}",
            f"--max-instances {service_config.max_instances}",
            f"--timeout {service_config.timeout}",
            f"--allow-unauthenticated"
        ]
        
        # Add environment variables
        if service_config.env_vars:
            env_vars = ','.join([f"{k}={v}" for k, v in service_config.env_vars.items()])
            cmd_parts.append(f"--set-env-vars \"{env_vars}\"")
        
        # Add secrets
        if service_config.secrets:
            secrets = ','.join([f"{k}={v}:latest" for k, v in service_config.secrets.items()])
            cmd_parts.append(f"--set-secrets \"{secrets}\"")
        
        return " \\\n  ".join(cmd_parts)


def create_default_configs():
    """Create default configuration files for all environments"""
    manager = ConfigManager()
    
    # Development configuration
    dev_config = EnvironmentConfig(
        name="development",
        gcp_project_id="utxoiq-dev",
        gcp_region="us-central1",
        domain="dev.utxoiq.com",
        services={
            "web-api": ServiceConfig(
                name="web-api",
                image="gcr.io/utxoiq-dev/utxoiq-web-api:latest",
                port=8080,
                cpu="1",
                memory="512Mi",
                min_instances=0,
                max_instances=5,
                timeout=300,
                env_vars={
                    "ENVIRONMENT": "development",
                    "LOG_LEVEL": "DEBUG",
                    "CORS_ORIGINS": "*"
                },
                secrets={
                    "DATABASE_URL": "database-url",
                    "FIREBASE_CREDENTIALS": "firebase-credentials"
                }
            ),
            "feature-engine": ServiceConfig(
                name="feature-engine",
                image="gcr.io/utxoiq-dev/utxoiq-feature-engine:latest",
                port=8080,
                cpu="2",
                memory="1Gi",
                min_instances=0,
                max_instances=5,
                timeout=600,
                env_vars={
                    "ENVIRONMENT": "development",
                    "LOG_LEVEL": "DEBUG"
                },
                secrets={
                    "BIGQUERY_CREDENTIALS": "bigquery-credentials"
                }
            )
        }
    )
    
    # Staging configuration
    staging_config = EnvironmentConfig(
        name="staging",
        gcp_project_id="utxoiq-staging",
        gcp_region="us-central1",
        domain="staging.utxoiq.com",
        services={
            "web-api": ServiceConfig(
                name="web-api",
                image="gcr.io/utxoiq-staging/utxoiq-web-api:latest",
                port=8080,
                cpu="2",
                memory="1Gi",
                min_instances=1,
                max_instances=10,
                timeout=300,
                env_vars={
                    "ENVIRONMENT": "staging",
                    "LOG_LEVEL": "INFO",
                    "CORS_ORIGINS": "https://staging.utxoiq.com"
                },
                secrets={
                    "DATABASE_URL": "database-url",
                    "FIREBASE_CREDENTIALS": "firebase-credentials"
                }
            ),
            "feature-engine": ServiceConfig(
                name="feature-engine",
                image="gcr.io/utxoiq-staging/utxoiq-feature-engine:latest",
                port=8080,
                cpu="4",
                memory="2Gi",
                min_instances=1,
                max_instances=10,
                timeout=600,
                env_vars={
                    "ENVIRONMENT": "staging",
                    "LOG_LEVEL": "INFO"
                },
                secrets={
                    "BIGQUERY_CREDENTIALS": "bigquery-credentials"
                }
            )
        }
    )
    
    # Production configuration
    prod_config = EnvironmentConfig(
        name="production",
        gcp_project_id="utxoiq-prod",
        gcp_region="us-central1",
        domain="utxoiq.com",
        services={
            "web-api": ServiceConfig(
                name="web-api",
                image="gcr.io/utxoiq-prod/utxoiq-web-api:latest",
                port=8080,
                cpu="4",
                memory="2Gi",
                min_instances=2,
                max_instances=50,
                timeout=300,
                env_vars={
                    "ENVIRONMENT": "production",
                    "LOG_LEVEL": "WARNING",
                    "CORS_ORIGINS": "https://utxoiq.com"
                },
                secrets={
                    "DATABASE_URL": "database-url",
                    "FIREBASE_CREDENTIALS": "firebase-credentials"
                }
            ),
            "feature-engine": ServiceConfig(
                name="feature-engine",
                image="gcr.io/utxoiq-prod/utxoiq-feature-engine:latest",
                port=8080,
                cpu="8",
                memory="4Gi",
                min_instances=2,
                max_instances=20,
                timeout=600,
                env_vars={
                    "ENVIRONMENT": "production",
                    "LOG_LEVEL": "WARNING"
                },
                secrets={
                    "BIGQUERY_CREDENTIALS": "bigquery-credentials"
                }
            )
        }
    )
    
    # Save configurations
    manager.save_environment_config(dev_config)
    manager.save_environment_config(staging_config)
    manager.save_environment_config(prod_config)
    
    print("Default configuration files created:")
    print(f"  - {manager.config_dir}/development.yaml")
    print(f"  - {manager.config_dir}/staging.yaml")
    print(f"  - {manager.config_dir}/production.yaml")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Environment configuration manager")
    parser.add_argument("--create-defaults", action="store_true", help="Create default config files")
    parser.add_argument("--environment", help="Environment name")
    parser.add_argument("--service", help="Service name")
    parser.add_argument("--generate-yaml", action="store_true", help="Generate Cloud Run YAML")
    parser.add_argument("--generate-command", action="store_true", help="Generate gcloud command")
    
    args = parser.parse_args()
    
    if args.create_defaults:
        create_default_configs()
    elif args.environment and args.service:
        manager = ConfigManager()
        env_config = manager.load_environment_config(args.environment)
        service_config = env_config.services.get(args.service)
        
        if not service_config:
            print(f"Service '{args.service}' not found in {args.environment} configuration")
            exit(1)
        
        if args.generate_yaml:
            yaml_output = manager.generate_cloud_run_yaml(service_config, args.environment)
            print(yaml_output)
        elif args.generate_command:
            cmd = manager.get_deployment_command(
                service_config,
                args.environment,
                env_config.gcp_project_id,
                env_config.gcp_region
            )
            print(cmd)
    else:
        parser.print_help()
