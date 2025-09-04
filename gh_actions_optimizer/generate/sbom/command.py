"""Generate SBOM command implementation."""

import argparse
import json
import subprocess  # nosec B404
from pathlib import Path

from ...shared import Colors, log_error, log_info, log_success


def cmd_generate_sbom(args: argparse.Namespace) -> None:
    """Generate Software Bill of Materials (SBOM)."""
    if not args.quiet:
        log_info("Generating Software Bill of Materials (SBOM)...")

    try:
        # Generate SBOM using pip-audit (ignore vulnerabilities for SBOM generation)
        cmd = ["pip-audit", "--format=cyclonedx-json", "--ignore-vuln", "*"]
        
        if args.output:
            output_path = Path(args.output)
            cmd.extend(["--output", str(output_path)])
        
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True
        )
        
        if args.output:
            log_success(f"SBOM saved to {args.output}")
        else:
            # Print to stdout
            if args.format == "json":
                sbom_data = json.loads(result.stdout)
                print(json.dumps(sbom_data, indent=2))
            else:
                # Parse and display in human-readable format
                sbom_data = json.loads(result.stdout)
                components = sbom_data.get("components", [])
                
                print(f"\n{Colors.BOLD}Software Bill of Materials{Colors.NC}")
                print("=" * 60)
                print(f"Project: {sbom_data.get('metadata', {}).get('component', {}).get('name', 'Unknown')}")
                print(f"Components: {len(components)}")
                print(f"Generated: {sbom_data.get('metadata', {}).get('timestamp', 'Unknown')}")
                
                print(f"\n{Colors.BOLD}Dependencies:{Colors.NC}")
                for component in components:
                    name = component.get("name", "Unknown")
                    version = component.get("version", "Unknown")
                    licenses = component.get("licenses", [])
                    license_str = ", ".join([l.get("license", {}).get("name", "Unknown") for l in licenses]) if licenses else "Unknown"
                    
                    print(f"  {Colors.BOLD}{name}{Colors.NC} {version} ({license_str})")

    except subprocess.CalledProcessError as e:
        log_error(f"Failed to generate SBOM: {e}")
        if e.stderr:
            log_error(f"Error output: {e.stderr}")
    except FileNotFoundError:
        log_error("pip-audit not found. Install with: pip install pip-audit")
    except json.JSONDecodeError as e:
        log_error(f"Failed to parse SBOM JSON: {e}")
    except Exception as e:
        log_error(f"Unexpected error generating SBOM: {e}")