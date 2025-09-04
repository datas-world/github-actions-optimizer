"""Generate SBOM command implementation."""

import argparse
import json
import os
import subprocess  # nosec B404
import tempfile
from pathlib import Path

from ...shared import Colors, log_error, log_info, log_success


def _validate_output_path(output_path: str) -> Path:
    """Validate and sanitize the output path to prevent security issues.
    
    Args:
        output_path: The user-provided output path
        
    Returns:
        Validated Path object
        
    Raises:
        ValueError: If the path is invalid or unsafe
    """
    # Convert to Path object for proper handling
    path = Path(output_path)
    
    # Check for directory traversal attempts
    if '..' in path.parts:
        raise ValueError("Path cannot contain '..' components")
    
    # Ensure the path is not absolute to prevent writing to system directories
    if path.is_absolute():
        # Allow absolute paths only if they are in safe locations
        safe_prefixes = [
            Path.home(),  # User home directory
            Path.cwd(),   # Current working directory
            Path(tempfile.gettempdir()), # Secure temporary directory
        ]
        if not any(path.is_relative_to(prefix) for prefix in safe_prefixes):
            raise ValueError("Absolute paths must be within safe directories")
    
    # Resolve the path to handle any remaining relative components safely
    try:
        resolved_path = path.resolve()
    except OSError as e:
        raise ValueError(f"Invalid path: {e}")
    
    # Ensure parent directory exists or can be created
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    
    return resolved_path


def cmd_generate_sbom(args: argparse.Namespace) -> None:
    """Generate Software Bill of Materials (SBOM)."""
    if not args.quiet:
        log_info("Generating Software Bill of Materials (SBOM)...")

    try:
        # Generate SBOM using pip-audit (ignore vulnerabilities for SBOM generation)
        cmd = ["pip-audit", "--format=cyclonedx-json", "--ignore-vuln", "*"]
        
        validated_output_path = None
        if args.output:
            try:
                validated_output_path = _validate_output_path(args.output)
                cmd.extend(["--output", str(validated_output_path)])
            except ValueError as e:
                log_error(f"Invalid output path: {e}")
                return
        
        # Use more secure subprocess execution with explicit argument handling
        result = subprocess.run(  # nosec B603
            cmd, 
            capture_output=True, 
            text=True, 
            check=True,
            env=dict(os.environ, PYTHONPATH=""),  # Clean environment
            timeout=60  # Prevent hanging
        )
        
        if validated_output_path:
            log_success(f"SBOM saved to {validated_output_path}")
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
    except subprocess.TimeoutExpired:
        log_error("SBOM generation timed out after 60 seconds")
    except FileNotFoundError:
        log_error("pip-audit not found. Install with: pip install pip-audit")
    except json.JSONDecodeError as e:
        log_error(f"Failed to parse SBOM JSON: {e}")
    except Exception as e:
        log_error(f"Unexpected error generating SBOM: {e}")