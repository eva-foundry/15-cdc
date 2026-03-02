# GitHub Copilot Instructions Template

**Template Version**: 2.1.0  
**Generated**: January 30, 2026, 2:00 PM EST  
**Last Updated**: January 30, 2026  
**Project Type**: {PROJECT_TYPE}  
**Based on**: EVA Professional Component Architecture Standards (from EVA-JP-v1.2 production learnings)

---

## Release Notes

### Version 2.1.0 (January 30, 2026)
**Breaking Changes**:
- Redesigned PART 2 from generic [TODO] format to AI-instructional placeholders
- Added [INSTRUCTION for AI] markers explaining what content to fill and why
- Introduced **[MANDATORY]** vs **[RECOMMENDED]** category markers for prioritization

**New Features**:
- 11 structured placeholder categories based on production analysis (EVA-JP-v1.2, MS-InfoJP)
- Enhanced placeholder syntax with examples: `[TODO: Add X - e.g., value format]`
- Quick Commands Table (action-oriented lookup)
- Azure Resource Inventory (subscription IDs, resource groups)
- Anti-Patterns sections ([x] FORBIDDEN patterns with explanations)
- Success Criteria / Testable Goals
- Performance/Timing Expectations
- Deployment Status & Known Issues tracking

**Improvements**:
- Template now generates AI instruction manual (not documentation)
- Placeholders show correct format/structure (imperative, conditional, reference patterns)
- Backward compatible: existing PART 2 sections remain valid
- Research-based design: 100% coverage of high-frequency patterns (Quick Commands, Environment Config, File Paths)

**Migration Notes**:
- Projects using v2.0.0 template can continue as-is
- New projects should use v2.1.0 structured placeholders
- Apply-Project07-Artifacts.ps1 v1.4.0+ compatible with both versions

### Version 2.0.0 (January 29, 2026)
**Breaking Changes**:
- Transformed from project-specific to reusable template
- Added comprehensive placeholder system for all project-specific values
- Enhanced with anti-patterns prevention and quality gates

**New Features**:
- Template Usage Instructions section
- Anti-Patterns Prevention section
- Emergency Debugging Protocol
- File Organization Requirements
- Quality Gates checklist

**Improvements**:
- Complete PART 1 preservation (universal best practices)
- Structured placeholder guidance in PART 2
- Professional component implementations remain intact
- Enhanced documentation structure

### Version 1.0.0 (January 9, 2026)
**Initial Production Release**:
- Universal best practices (PART 1)
- EVA-JP-v1.2 project-specific patterns (PART 2)
- Professional Component Architecture (DebugArtifactCollector, SessionManager, StructuredErrorHandler, ProfessionalRunner)
- Azure account management patterns
- Workspace housekeeping principles
- Encoding safety standards

---

## Table of Contents

### PART 1: Universal Best Practices
- [Encoding & Script Safety](#critical-encoding--script-safety)
- [Azure Account Management](#critical-azure-account-management)
- [AI Context Management](#ai-context-management-strategy)
- [Azure Services Inventory](#azure-services--capabilities-inventory)
- [Professional Component Architecture](#professional-component-architecture)
  - [DebugArtifactCollector](#implementation-debugartifactcollector)
  - [SessionManager](#implementation-sessionmanager)
  - [StructuredErrorHandler](#implementation-structurederrorhandler)
  - [ProfessionalRunner](#implementation-zero-setup-project-runner)
- [Professional Transformation](#professional-transformation-methodology)
- [Dependency Management](#dependency-management-with-alternatives)
- [Workspace Housekeeping](#workspace-housekeeping-principles)
- [Code Style Standards](#code-style-standards)

### PART 2: {PROJECT_NAME} Project Specific
- [Documentation Guide](#documentation-guide)
- [Architecture Overview](#architecture-overview)
- [Development Workflows](#development-workflows)
- [Project-Specific Automation](#project-specific-automation)
- [Critical Code Patterns](#critical-code-patterns)
- [Testing](#testing)
- [CI/CD Pipeline](#cicd-pipeline)
- [Troubleshooting](#troubleshooting)
- [Performance Optimization](#performance-optimization)

### PART 3: Quality & Safety
- [Anti-Patterns Prevention](#anti-patterns-prevention)
- [File Organization Requirements](#file-organization-requirements)
- [Quality Gates](#quality-gates)
- [Emergency Debugging Protocol](#emergency-debugging-protocol)

### PART 4: Template Usage
- [Template Usage Instructions](#template-usage-instructions)

---

## Quick Reference

**Most Critical Patterns**:
1. **Encoding Safety** - Always use ASCII-only in scripts (prevents UnicodeEncodeError in Windows cp1252)
2. **Azure Account** - Professional account {PROFESSIONAL_EMAIL} required for {ORGANIZATION} resources (configure based on your subscription)
3. **Component Architecture** - DebugArtifactCollector + SessionManager + StructuredErrorHandler + ProfessionalRunner
4. **Session Management** - Checkpoint/resume capability for long-running operations
5. **Evidence Collection** - Screenshots, HTML dumps, network traces at operation boundaries

**Professional Components** (Full Working Implementations):

| Component | Purpose | Key Methods |
|-----------|---------|-------------|
| **DebugArtifactCollector** | Capture HTML/screenshots/traces | `capture_state()`, `set_page()` |
| **SessionManager** | Checkpoint/resume operations | `save_checkpoint()`, `load_latest_checkpoint()` |
| **StructuredErrorHandler** | JSON error logging | `log_error()`, `log_structured_event()` |
| **ProfessionalRunner** | Zero-setup execution | `auto_detect_project_root()`, `validate_pre_flight()` |

**Where to Find Source**:
- Complete working system: `{PROJECT_IMPLEMENTATION_PATH}`
- Best practices reference: `{BEST_PRACTICES_PATH}`
- Framework architecture: `{FRAMEWORK_ARCHITECTURE_PATH}`

---

## PART 1: UNIVERSAL BEST PRACTICES

> **Applicable to any project, any scenario**  
> Critical patterns, Azure inventory management, workspace organization principles

### Critical: Encoding & Script Safety

**ABSOLUTE BAN: No Unicode/Emojis Anywhere**
- **NEVER use in code**: Checkmarks, X marks, emojis, Unicode symbols, ellipsis
- **NEVER use in reports**: Unicode decorations, fancy bullets, special characters
- **NEVER use in documentation**: Unless explicitly required by specification
- **ALWAYS use**: Pure ASCII - "[PASS]", "[FAIL]", "[ERROR]", "[INFO]", "[WARN]", "..."
- **Reason**: Enterprise Windows cp1252 encoding causes silent UnicodeEncodeError crashes
- **Solution**: Set `PYTHONIOENCODING=utf-8` in batch files as safety measure

**Examples**:
```python
# [FORBIDDEN] Will crash in enterprise Windows
print(" Success")  # Unicode checkmark - NEVER
print("[x] Failed")   # Unicode X - NEVER
print(" Wait...")    # Unicode symbols - NEVER

# [REQUIRED] ASCII-only alternatives
print("[PASS] Success")
print("[FAIL] Failed")
print("[INFO] Wait...")
```

### Critical: Azure Account Management

**Multiple Azure Accounts Pattern**
- **Personal Account**: {PERSONAL_SUBSCRIPTION_NAME} ({PERSONAL_SUBSCRIPTION_ID}) - personal sandbox
- **Professional Account**: {PROFESSIONAL_EMAIL} - {ORGANIZATION} production access
- **{ORGANIZATION} Subscriptions** (require professional account):
  - {DEV_SUBSCRIPTION_NAME} ({DEV_SUBSCRIPTION_ID}) - Dev+Stage environments
  - {PROD_SUBSCRIPTION_NAME} ({PROD_SUBSCRIPTION_ID}) - Production environments

**When Azure CLI fails with "subscription doesn't exist"**:
1. Check current account: `az account show --query user.name`
2. Switch accounts: `az logout` then `az login --use-device-code --tenant {TENANT_ID}`
3. Authenticate with professional email: {PROFESSIONAL_EMAIL}
4. Verify access: `az account list --query "[?contains(id, '{DEV_SUBSCRIPTION_ID_PARTIAL}') || contains(id, '{PROD_SUBSCRIPTION_ID_PARTIAL}')]"`

**Pattern**: If accessing {ORGANIZATION} resources, ALWAYS use professional account

### AI Context Management Strategy

**Pattern**: Systematic approach to avoid context overload

**5-Step Process**:
1. **Assess**: What context do I need? (Don't load everything)
2. **Prioritize**: What's most relevant NOW? (Focus on current task)
3. **Load**: Get specific context only (Use targeted file reads, grep searches)
4. **Execute**: Perform task with loaded context
5. **Verify**: Validate result matches intent

**Example**:
```python
# [AVOID] Bad: Load entire file when only need one function
with open('large_file.py') as f:
    content = f.read()  # Loads 10,000 lines

# [RECOMMENDED] Good: Targeted context loading
grep_search(query="def target_function", includePattern="large_file.py")
read_file(filePath="large_file.py", startLine=450, endLine=500)
```

**When to re-assess context**:
- Task scope changes
- Error requires different context
- User provides new information

### Azure Services & Capabilities Inventory

**Azure OpenAI**
- **Models**: GPT-4, GPT-4 Turbo, text-embedding-ada-002
- **Endpoints**: {AZURE_OPENAI_ENDPOINT}
- **Use Cases**: Chat completions, embeddings, content generation
- **Authentication**: API key or DefaultAzureCredential

**Azure AI Services (Cognitive Services)**
- **Capabilities**: Query optimization, content safety, content understanding
- **Use Cases**: Text analysis, translation, content moderation
- **Pattern**: Always implement fallback for private endpoint failures

**Azure Cognitive Search**
- **Capabilities**: Hybrid search (vector + keyword), semantic ranking
- **Use Cases**: Document search, RAG systems, knowledge bases
- **Pattern**: Use index-based access, implement retry logic

**Azure Cosmos DB**
- **Capabilities**: NoSQL database, session storage, change feed
- **Use Cases**: Session management, audit logs, CDC patterns
- **Pattern**: Use partition keys effectively, implement TTL

**Azure Blob Storage**
- **Capabilities**: Object storage, containers, metadata
- **Use Cases**: Document storage, file uploads, static assets
- **Pattern**: Use managed identity, implement lifecycle policies

**Azure Functions**
- **Capabilities**: Serverless compute, event-driven processing
- **Use Cases**: Document pipelines, webhook handlers, scheduled jobs
- **Pattern**: Use blob triggers, queue bindings

**Azure Document Intelligence**
- **Capabilities**: OCR, form recognition, layout analysis
- **Use Cases**: PDF processing, document extraction
- **Pattern**: Handle rate limits, implement retry logic

### Professional Component Architecture

**Pattern**: Enterprise-grade component design (from Project 06/07)

**Every professional component implements**:
- **DebugArtifactCollector**: Evidence at operation boundaries
- **SessionManager**: Checkpoint/resume capabilities
- **StructuredErrorHandler**: JSON logging with context
- **Observability Wrapper**: Pre-state, execution, post-state capture

**Usage Pattern - Combining Components**:

> **Note**: The following shows a conceptual pattern for combining components. For complete, production-ready implementations you can copy-paste directly, see the detailed sections below.
```python
from pathlib import Path
from datetime import datetime
import json

class ProfessionalComponent:
    """Base class for enterprise-grade components"""
    
    def __init__(self, component_name: str, base_path: Path):
        self.component_name = component_name
        self.base_path = base_path
        
        # Core professional infrastructure
        self.debug_collector = DebugArtifactCollector(component_name, base_path)
        self.session_manager = SessionManager(component_name, base_path)
        self.error_handler = StructuredErrorHandler(component_name, base_path)
    
    async def execute_with_observability(self, operation_name: str, operation):
        """Execute operation with full evidence collection"""
        # 1. ALWAYS capture pre-state
        await self.debug_collector.capture_state(f"{operation_name}_before")
        await self.session_manager.save_checkpoint("before_operation", {
            "operation": operation_name,
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            # 2. Execute operation
            result = await operation()
            
            # 3. ALWAYS capture success state
            await self.debug_collector.capture_state(f"{operation_name}_success")
            await self.session_manager.save_checkpoint("operation_success", {
                "operation": operation_name,
                "result_preview": str(result)[:200]
            })
            return result
            
        except Exception as e:
            # 4. ALWAYS capture error state
            await self.debug_collector.capture_state(f"{operation_name}_error")
            await self.error_handler.log_structured_error(operation_name, e)
            raise
```

**When to use**: Any component that interacts with external systems, complex logic, or enterprise automation

---

### Implementation: DebugArtifactCollector

**Purpose**: Capture comprehensive diagnostic state at system boundaries for rapid debugging

**Working Implementation** (from Project 06):
```python
from pathlib import Path
from datetime import datetime
import json
import asyncio

class DebugArtifactCollector:
    """Systematic evidence capture at operation boundaries
    
    Captures HTML, screenshots, network traces, and structured logs
    for every significant operation to enable rapid debugging.
    """
    
    def __init__(self, component_name: str, base_path: Path):
        """Initialize collector for specific component
        
        Args:
            component_name: Name of component (e.g., "authentication", "data_extraction")
            base_path: Project root directory
        """
        self.component_name = component_name
        self.debug_dir = base_path / "debug" / component_name
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        
        self.page = None  # Set by browser automation
        self.network_log = []  # Populated by network listener
    
    async def capture_state(self, context: str):
        """Capture complete diagnostic state
        
        Args:
            context: Operation context (e.g., "before_login", "after_submit", "error_state")
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Capture HTML snapshot
        if self.page:
            html_file = self.debug_dir / f"{context}_{timestamp}.html"
            html_content = await self.page.content()
            html_file.write_text(html_content, encoding='utf-8')
        
        # 2. Capture screenshot
        if self.page:
            screenshot_file = self.debug_dir / f"{context}_{timestamp}.png"
            await self.page.screenshot(path=str(screenshot_file), full_page=True)
        
        # 3. Capture network trace
        if self.network_log:
            network_file = self.debug_dir / f"{context}_{timestamp}_network.json"
            network_file.write_text(json.dumps(self.network_log, indent=2))
        
        # 4. Capture structured log with application state
        log_file = self.debug_dir / f"{context}_{timestamp}.json"
        log_file.write_text(json.dumps({
            "timestamp": timestamp,
            "context": context,
            "component": self.component_name,
            "url": self.page.url if self.page else None,
            "viewport": await self.page.viewport_size() if self.page else None
        }, indent=2))
        
        return {
            "html": str(html_file) if self.page else None,
            "screenshot": str(screenshot_file) if self.page else None,
            "network": str(network_file) if self.network_log else None,
            "log": str(log_file)
        }
    
    def set_page(self, page):
        """Attach to browser page for capture"""
        self.page = page
        
        # Enable network logging
        async def log_request(request):
            self.network_log.append({
                "timestamp": datetime.now().isoformat(),
                "type": "request",
                "url": request.url,
                "method": request.method
            })
        
        page.on("request", lambda req: asyncio.create_task(log_request(req)))
```

**Usage Pattern**:
```python
# In your automation component
collector = DebugArtifactCollector("my_component", project_root)
collector.set_page(page)

# Before risky operation
await collector.capture_state("before_submit")

try:
    await risky_operation()
    await collector.capture_state("success")
except Exception as e:
    await collector.capture_state("error")
    raise
```

---

### Implementation: SessionManager

**Purpose**: Enable checkpoint/resume capabilities for long-running operations

**Working Implementation** (from Project 06):
```python
from pathlib import Path
from datetime import datetime, timedelta
import json
import shutil
from typing import Dict, Optional

class SessionManager:
    """Manages persistent session state for checkpoint/resume operations
    
    Enables long-running automation to save progress and resume
    from last successful checkpoint if interrupted.
    """
    
    def __init__(self, component_name: str, base_path: Path):
        """Initialize session manager
        
        Args:
            component_name: Component identifier
            base_path: Project root directory
        """
        self.component_name = component_name
        self.session_dir = base_path / "sessions" / component_name
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        self.session_file = self.session_dir / "session_state.json"
        self.checkpoint_dir = self.session_dir / "checkpoints"
        self.checkpoint_dir.mkdir(exist_ok=True)
    
    def save_checkpoint(self, checkpoint_id: str, data: Dict) -> Path:
        """Save checkpoint with state data
        
        Args:
            checkpoint_id: Unique checkpoint identifier (e.g., "item_5_processed")
            data: State data to persist
            
        Returns:
            Path to saved checkpoint file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}_{timestamp}.json"
        
        checkpoint_data = {
            "checkpoint_id": checkpoint_id,
            "timestamp": datetime.now().isoformat(),
            "component": self.component_name,
            "data": data
        }
        
        checkpoint_file.write_text(json.dumps(checkpoint_data, indent=2))
        
        # Update session state to point to latest checkpoint
        self.update_session_state(checkpoint_id, str(checkpoint_file))
        
        return checkpoint_file
    
    def load_latest_checkpoint(self) -> Optional[Dict]:
        """Load most recent checkpoint if available
        
        Returns:
            Checkpoint data or None if no checkpoint exists
        """
        if not self.session_file.exists():
            return None
        
        try:
            session_data = json.loads(self.session_file.read_text())
            checkpoint_file = Path(session_data.get("latest_checkpoint"))
            
            if checkpoint_file.exists():
                return json.loads(checkpoint_file.read_text())
            
        except Exception as e:
            print(f"[WARN] Failed to load checkpoint: {e}")
        
        return None
    
    def update_session_state(self, checkpoint_id: str, checkpoint_path: str):
        """Update session state with latest checkpoint reference"""
        session_data = {
            "component": self.component_name,
            "last_updated": datetime.now().isoformat(),
            "latest_checkpoint": checkpoint_path,
            "checkpoint_id": checkpoint_id
        }
        
        self.session_file.write_text(json.dumps(session_data, indent=2))
    
    def clear_session(self):
        """Clear all session state and checkpoints"""
        if self.checkpoint_dir.exists():
            shutil.rmtree(self.checkpoint_dir)
            self.checkpoint_dir.mkdir()
        
        if self.session_file.exists():
            self.session_file.unlink()
```

**Usage Pattern**:
```python
# Initialize session manager
session_mgr = SessionManager("batch_processor", project_root)

# Try to resume from checkpoint
checkpoint = session_mgr.load_latest_checkpoint()
if checkpoint:
    start_index = checkpoint["data"]["last_processed_index"]
    print(f"[INFO] Resuming from checkpoint: item {start_index}")
else:
    start_index = 0

# Process items with checkpoints
for i in range(start_index, len(items)):
    process_item(items[i])
    
    # Save checkpoint every 10 items
    if i % 10 == 0:
        session_mgr.save_checkpoint(f"item_{i}", {
            "last_processed_index": i,
            "items_completed": i + 1,
            "timestamp": datetime.now().isoformat()
        })
```

---

### Implementation: StructuredErrorHandler

**Purpose**: Provide JSON-based error logging with full context for debugging

**Working Implementation** (from Project 06):
```python
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import json
import traceback

class StructuredErrorHandler:
    """Enterprise-grade error handling with structured logging
    
    Captures errors with full context in JSON format for easy parsing
    and analysis. All output is ASCII-safe for enterprise Windows.
    """
    
    def __init__(self, component_name: str, base_path: Path):
        """Initialize error handler
        
        Args:
            component_name: Component identifier
            base_path: Project root directory
        """
        self.component_name = component_name
        self.error_dir = base_path / "logs" / "errors"
        self.error_dir.mkdir(parents=True, exist_ok=True)
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict:
        """Log error with structured context
        
        Args:
            error: Exception object
            context: Additional context (operation name, parameters, etc.)
            
        Returns:
            Error report dictionary
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        error_report = {
            "timestamp": datetime.now().isoformat(),
            "component": self.component_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {}
        }
        
        # Save to timestamped file
        error_file = self.error_dir / f"{self.component_name}_error_{timestamp}.json"
        error_file.write_text(json.dumps(error_report, indent=2))
        
        # Print ASCII-safe error message
        print(f"[ERROR] {self.component_name}: {type(error).__name__}")
        print(f"[ERROR] Message: {str(error)}")
        print(f"[ERROR] Details saved to: {error_file}")
        
        return error_report
    
    def log_structured_event(self, event_type: str, data: Dict[str, Any]):
        """Log structured event (non-error)
        
        Args:
            event_type: Event type (e.g., "operation_start", "data_validated")
            data: Event data
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        event_report = {
            "timestamp": datetime.now().isoformat(),
            "component": self.component_name,
            "event_type": event_type,
            "data": data
        }
        
        # Save to events log
        event_file = self.error_dir.parent / f"{self.component_name}_events_{timestamp}.json"
        event_file.write_text(json.dumps(event_report, indent=2))

class ProjectBaseException(Exception):
    """Base exception with structured error reporting
    
    All custom exceptions should inherit from this to ensure
    consistent error handling and reporting.
    """
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Initialize exception with context
        
        Args:
            message: Error description (ASCII only)
            context: Additional error context
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.timestamp = datetime.now().isoformat()
    
    def get_error_report(self) -> Dict[str, Any]:
        """Generate structured error report
        
        Returns:
            Dictionary with full error details
        """
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp
        }
```

**Usage Pattern**:
```python
# Initialize error handler
error_handler = StructuredErrorHandler("my_automation", project_root)

try:
    risky_operation()
except Exception as e:
    # Log with context
    error_handler.log_error(e, context={
        "operation": "data_processing",
        "input_file": "data.csv",
        "current_row": 42
    })
    raise

# Custom exception with automatic context
class DataValidationError(ProjectBaseException):
    pass

try:
    if not is_valid(data):
        raise DataValidationError(
            "Invalid data format",
            context={"expected": "CSV", "received": "JSON"}
        )
except DataValidationError as e:
    error_report = e.get_error_report()
    error_handler.log_error(e, context=error_report["context"])
```

---

### Implementation: Zero-Setup Project Runner

**Purpose**: Enable users to run project from anywhere without configuration

**Working Implementation** (from Project 06):
```python
#!/usr/bin/env python3
"""Professional project runner with zero-setup execution"""

import os
import sys
import argparse
from pathlib import Path
import subprocess
from typing import List

# Set UTF-8 encoding for Windows
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

class ProfessionalRunner:
    """Zero-setup professional automation wrapper"""
    
    def __init__(self):
        self.project_root = self.auto_detect_project_root()
        self.main_script = "scripts/main_automation.py"
    
    def auto_detect_project_root(self) -> Path:
        """Find project root from any subdirectory
        
        Searches for project markers in current and parent directories
        to enable running from any location within the project.
        """
        current = Path.cwd()
        
        # Project indicators (customize for your project)
        indicators = [
            "scripts/main_automation.py",
            "ACCEPTANCE.md",
            "README.md",
            ".git"
        ]
        
        # Check current directory
        for indicator in indicators:
            if (current / indicator).exists():
                return current
        
        # Check parent directories
        for parent in current.parents:
            for indicator in indicators:
                if (parent / indicator).exists():
                    return parent
        
        # Fallback to current directory
        print("[WARN] Could not auto-detect project root, using current directory")
        return current
    
    def validate_pre_flight(self) -> tuple[bool, str]:
        """Pre-flight checks before execution
        
        Validates environment, dependencies, and project structure.
        
        Returns:
            (success: bool, message: str)
        """
        checks = []
        
        # Check main script exists
        main_script_path = self.project_root / self.main_script
        if not main_script_path.exists():
            return False, f"[FAIL] Main script not found: {main_script_path}"
        checks.append("[PASS] Main script found")
        
        # Check required directories
        required_dirs = ["input", "output", "logs"]
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True)
                checks.append(f"[INFO] Created directory: {dir_name}")
            else:
                checks.append(f"[PASS] Directory exists: {dir_name}")
        
        # Check Python dependencies
        try:
            import pandas
            import asyncio
            checks.append("[PASS] Required Python modules available")
        except ImportError as e:
            return False, f"[FAIL] Missing Python module: {e}"
        
        return True, "\n".join(checks)
    
    def build_command(self, **kwargs) -> List[str]:
        """Build command with normalized parameters
        
        Converts user inputs to proper command structure.
        """
        cmd = [
            sys.executable,
            str(self.project_root / self.main_script)
        ]
        
        # Add parameters (customize for your project)
        for key, value in kwargs.items():
            if value is not None:
                if isinstance(value, bool):
                    if value:
                        cmd.append(f"--{key}")
                else:
                    cmd.extend([f"--{key}", str(value)])
        
        return cmd
    
    def execute_with_enterprise_safety(self, cmd: List[str]) -> int:
        """Execute with proper encoding and error handling"""
        # Set environment
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # Change to project root
        original_cwd = os.getcwd()
        os.chdir(self.project_root)
        
        try:
            print(f"[INFO] Project root: {self.project_root}")
            print(f"[INFO] Command: {' '.join(cmd)}")
            print("-" * 60)
            
            result = subprocess.run(cmd, env=env)
            return result.returncode
            
        finally:
            os.chdir(original_cwd)
    
    def run(self, **kwargs) -> int:
        """Main execution entry point"""
        print("[INFO] Professional Runner - Zero-Setup Execution")
        print(f"[INFO] Detected project root: {self.project_root}")
        
        # Pre-flight validation
        success, message = self.validate_pre_flight()
        print("\n" + message)
        
        if not success:
            print("\n[FAIL] Pre-flight checks failed")
            return 1
        
        # Build and execute command
        cmd = self.build_command(**kwargs)
        return self.execute_with_enterprise_safety(cmd)

def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Professional automation runner with zero-setup execution"
    )
    
    # Add your project-specific arguments here
    parser.add_argument("--input", help="Input file path")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    
    args = parser.parse_args()
    
    # Create runner and execute
    runner = ProfessionalRunner()
    sys.exit(runner.run(**vars(args)))

if __name__ == "__main__":
    main()
```

**Usage**:
```bash
# Run from anywhere in the project
python run_project.py --input data.csv --output results.csv

# Or create Windows batch wrapper
# run_project.bat:
@echo off
set PYTHONIOENCODING=utf-8
python run_project.py %*
```

---

### Professional Transformation Methodology

**Pattern**: Systematic 4-step approach to enterprise-grade development

**When refactoring or creating automation systems**:

1. **Foundation Systems** (20% of work)
   - Create `debug/`, `evidence/`, `logs/` directory structure
   - Establish coding standards and utilities
   - Implement ASCII-only error handling
   - Set up structured logging infrastructure

2. **Testing Framework** (30% of work)
   - Automated validation with evidence collection
   - Component-level unit tests
   - Integration tests with retry logic
   - Acceptance criteria validation

3. **Main System Refactoring** (40% of work)
   - Apply professional component architecture
   - Integrate validation and observability
   - Implement graceful error handling
   - Add session management and checkpoints

4. **Documentation & Cleanup** (10% of work)
   - Consolidate redundant code
   - Document patterns and decisions
   - Create runbooks and troubleshooting guides
   - Archive superseded implementations

**Quality Gate**: Each phase produces evidence before proceeding to next phase

### Dependency Management with Alternatives

**Pattern**: Handle blocked packages in enterprise environments

**Always provide fallback alternatives**:

```python
# Pattern 1: Try primary, fall back to alternative
try:
    from playwright.async_api import async_playwright
    BROWSER_ENGINE = "playwright"
except ImportError:
    print("[INFO] Playwright not available, using Selenium")
    from selenium import webdriver
    BROWSER_ENGINE = "selenium"

# Pattern 2: Feature detection
def get_available_http_client():
    """Return best available HTTP client"""
    if importlib.util.find_spec("httpx"):
        import httpx
        return httpx.AsyncClient()
    elif importlib.util.find_spec("aiohttp"):
        import aiohttp
        return aiohttp.ClientSession()
    else:
        import urllib.request
        return urllib.request  # Fallback to stdlib

# Pattern 3: Document alternatives in requirements
# requirements.txt:
# playwright>=1.40.0  # Primary choice
# selenium>=4.15.0    # Alternative if playwright blocked
# requests>=2.31.0    # Fallback for basic HTTP
```

**Document why alternatives chosen**: Add comments explaining enterprise constraints

### Workspace Housekeeping Principles

**Context Engineering - Keep AI context clean and focused**

**Best Practices**:
- **Root directory**: Active operations only (`RESTART_SERVERS.ps1`, `README.md`)
- **Context folder**: Use `docs/eva-foundry/` as AI agent "brain"
  - `projects/` - Active work with debugging artifacts
  - `workspace-notes/` - Ephemeral notes, workflow docs
  - `system-analysis/` - Architecture docs, inventory reports
  - `comparison-reports/` - Automated comparison outputs
  - `automation/` - Code generation scripts

**Pattern**: If referenced in copilot-instructions.md or used for AI context -> belongs in `docs/eva-foundry/`

**File Organization Rules**:
1. **Logs** -> `logs/{category}/`
   - `logs/deployment/terraform/` - Terraform logs
   - `logs/deployment/` - Deployment logs
   - `logs/tests/` - Test output

2. **Scripts** -> `scripts/{category}/`
   - `scripts/deployment/` - Deploy, build, infrastructure
   - `scripts/testing/` - Test runners, evidence capture
   - `scripts/setup/` - Installation, configuration
   - `scripts/diagnostics/` - Health checks, validation
   - `scripts/housekeeping/` - Workspace organization

3. **Documentation** -> `docs/{category}/`
   - Implementation docs -> `docs/eva-foundry/projects/{project-name}/`
   - Deployment guides -> `docs/deployment/`
   - Debug sessions -> `docs/eva-foundry/projects/{session-name}-debug/`

**Naming Conventions**:
- **Scripts**: `verb-noun.ps1` (lowercase-with-dashes)
  - [RECOMMENDED] Good: `deploy-infrastructure.ps1`, `test-environment.ps1`
  - [AVOID] Bad: `Deploy-MSInfo-Fixed.ps1`, `TEST_COMPLETE.ps1`
- **Docs**: `CATEGORY-DESCRIPTION.md` (UPPERCASE for status docs)
  - [RECOMMENDED] Good: `DEPLOYMENT-STATUS.md`, `IMPLEMENTATION-SUMMARY.md`
  - [AVOID] Bad: `Final-Status-Report.ps1.md`
- **Logs**: `{operation}-{timestamp}.log` or `{component}.log`

**Self-Organizing Rules for AI Agents**:
- **Before creating a file**: Check if similar file exists in `docs/eva-foundry/`
- **When debugging**: Create session folder `docs/eva-foundry/projects/{issue-name}-debug/`
- **After completing work**: Summarize findings in `docs/eva-foundry/workspace-notes/`
- **When context grows**: Create comparison report, archive superseded versions

**Housekeeping Automation**:
```powershell
# Daily cleanup
.\scripts\housekeeping\organize-workspace.ps1

# Weekly archival
.\scripts\housekeeping\archive-debug-sessions.ps1
```

### Evidence Collection at Operation Boundaries

**Goal**: Systematic evidence capture for rapid debugging

**MANDATORY: Every component operation must capture**:
- **Pre-state**: HTML, screenshots, network traces BEFORE execution
- **Success state**: Evidence on successful completion  
- **Error state**: Full diagnostic artifacts on failure
- **Structured logging**: JSON-based error context with timestamps

**Implementation Pattern**:
```python
class DebugArtifactCollector:
    def __init__(self, component_name: str, base_path: Path):
        self.component_name = component_name
        self.debug_dir = base_path / "debug" / component_name
        self.debug_dir.mkdir(parents=True, exist_ok=True)
    
    async def capture_state(self, context: str):
        """Capture complete diagnostic state"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Capture HTML snapshot
        if self.page:  # Browser automation
            html_file = self.debug_dir / f"{context}_{timestamp}.html"
            await self.page.content().write(html_file)
        
        # Capture screenshot
        if self.page:
            screenshot_file = self.debug_dir / f"{context}_{timestamp}.png"
            await self.page.screenshot(path=screenshot_file)
        
        # Capture network trace
        if self.network_log:
            network_file = self.debug_dir / f"{context}_{timestamp}_network.json"
            network_file.write_text(json.dumps(self.network_log, indent=2))
        
        # Capture structured log
        log_file = self.debug_dir / f"{context}_{timestamp}.json"
        log_file.write_text(json.dumps({
            "timestamp": timestamp,
            "context": context,
            "component": self.component_name,
            "url": str(self.page.url) if self.page else None,
            "state": await self._capture_application_state()
        }, indent=2))
```

**Timestamped Naming Convention (MANDATORY)**:
- Pattern: `{component}_{context}_{YYYYMMDD_HHMMSS}.{ext}`
- Examples:
  - `{component}_debug_error_attempt_1_{YYYYMMDD_HHMMSS}.html`
  - `automation_execution_{YYYYMMDD_HHMMSS}.log`
  - `results_batch_001_{YYYYMMDD_HHMMSS}.csv`
- Benefits: Chronological sorting, parallel execution support, audit trails

**Azure Configuration State Tracking**:

**Structure**:
```
docs/eva-foundry/system-analysis/inventory/.eva-cache/
  azure-connectivity-{subscription}-{timestamp}.md
  azure-permissions-{subscription}-{timestamp}.md
  evidence-{subscription}-{timestamp}.md
  canonical-analysis/{storage-account}-{timestamp}.md
```

**Usage Pattern**:
1. Capture current state: `evidence-{subscription}-{timestamp}.md`
2. Compare with previous state: `evidence-{subscription}-{earlier-timestamp}.md`
3. Generate comparison report: `comparison-report-{timestamp}.md`
4. Document findings in project debug folder

### Code Style Standards

**Python**:
- **Type Hints**: Use for all function signatures
- **Async/Await**: Use throughout for I/O operations
- **Naming**: `snake_case` functions/variables, `PascalCase` classes
- **Formatting**: Black (line length 180) + isort
- **Error Handling**: Wrap external calls with try/except, respect `OPTIONAL` flags

**TypeScript**:
- **Naming**: `camelCase` functions/variables, `PascalCase` components/types
- **Components**: Functional components with hooks
- **State**: React Context for global state
- **Styling**: CSS Modules + component libraries

**Files**:
- Python: `snake_case.py`
- TypeScript: `lowercase-with-dashes.tsx`

---

**You are now ready for project-specific patterns**  
See [PART 2: {PROJECT_NAME} Project Specific](#part-2-project-name-project-specific) below for AI-instructional project patterns.

---



## PART 2: 15-CDC PROJECT SPECIFIC

### Project Lock

This file is the copilot-instructions for **15-cdc** (15-cdc).

The workspace-level bootstrap rule "Step 1 -- Identify the active project from the currently open file path"
applies **only at the initial load of this file** (first read at session start).
Once this file has been loaded, the active project is locked to **15-cdc** for the entire session.
Do NOT re-evaluate project identity from editorContext or terminal CWD on each subsequent request.
Work state and sprint context are read from `STATUS.md` and `PLAN.md` at bootstrap -- not from this file.

---

> **MS-InfoJP Change Data Capture (CDC) System**  
> RAG corpus freshness management through delta-only processing  
> Updated: February 7, 2026 (DevBox container deployment ready)

### Quick Reference

**Most Critical Patterns**:
1. **Queue-Based Architecture** - 5 Azure Storage Queues for downstream actions
2. **Professional Components** - SessionManager (checkpoint every 100 cases), DebugArtifactCollector
3. **Function Reuse** - 2 existing EVA-JP functions + 4 new CDC functions
4. **Policy-Driven Classification** - 7 change classes from change-policy.yaml
5. **DevBox Container** - Full Azure private endpoint access, no VPN required

**Quick Commands**:

| Command | Purpose |
|---------|---------|
| `python scripts/dev/test-azure-connectivity.py` | Validate Azure connectivity (7 tests) |
| `python scripts/deployment/deploy-cosmos-schema.py` | Deploy 12 Cosmos DB containers |
| `pwsh scripts/deployment/create-storage-queues.ps1` | Create 5 downstream processing queues |
| `pytest tests/ -v -m unit` | Run unit tests |
| `pytest tests/ -v -m integration` | Run integration tests (requires Azure) |

### Documentation Guide

**Primary References**:
- **This file** (copilot-instructions.md): Quick reference workflows and patterns
- **[README.md](../README.md)**: Project overview, prerequisites, architecture
- **[CDC-IMPLEMENTATION-START.md](../CDC-IMPLEMENTATION-START.md)**: Complete implementation guide (1,479 lines)
- **[cdc-mvp-design.md](../cdc-mvp-design.md)**: Architecture principles (671 lines)
- **[DEVBOX-DEPLOYMENT.md](../DEVBOX-DEPLOYMENT.md)**: DevBox container deployment guide

### Architecture Overview

**System Type**: Change Data Capture (CDC) for RAG corpus freshness

**Core Components**:

1. **Change Detection** - Tier1CDCPoller (scheduled polling of CanLII metadata)
2. **CDC Evidence** - 12 Cosmos DB containers tracking cases, versions, artifacts, changes
3. **Downstream Processing** - Queue-based action execution (fetch, extract, chunk, embed, index)
4. **Freshness-Aware Retrieval** - Recency-boosted Azure AI Search queries

**Technology Stack**:
- **Language**: Python 3.10+
- **Azure Services**: Cosmos DB, Blob Storage, Queue Storage, Azure AI Search, Azure Functions, Key Vault
- **Data Source**: CanLII API (Canadian case law metadata)
- **Orchestration**: Azure Functions (Timer + Queue triggers)
- **Professional Components**: SessionManager, DebugArtifactCollector, StructuredErrorHandler

**Critical Architecture Patterns**:

**1. Queue-Based Downstream Architecture** (Critical Improvement #1):
```
Tier1CDCPoller -> change_event created -> Queue messages triggered
    
Azure Storage Queues:
  - fetch-artifact-queue     -> FetchArtifact function
  - extract-text-queue       -> FileFormRecSubmissionPDF (existing)
  - generate-chunks-queue    -> TextEnrichment (existing)
  - embed-chunks-queue       -> TextEnrichment (existing)
  - update-index-queue       -> UpdateSearchIndex function
```

**Storage Location**: `marcosand20260203/Queues/`  
**Pattern**: Each change_event triggers downstream actions via queue messages

**2. Function Reuse Strategy** (Critical Improvement #2):
```
marco-sandbox-func/ (Consumption Plan)
 [EXISTING - REUSE]
    FileFormRecSubmissionPDF    -> extract_text action
    TextEnrichment              -> generate_chunks + embed_chunks actions

 [NEW - CDC CORE]
    Tier1CDCPoller              -> Timer trigger (daily 2AM UTC)
    FetchArtifact               -> Queue trigger (fetch-artifact-queue)
    ProcessChangeEvent          -> Queue trigger (change-event-queue)
    UpdateSearchIndex           -> Queue trigger (update-index-queue)
```

**Key Insight**: 50% of functions already deployed! Just add 4 new CDC-specific functions.

**3. Professional Components Integration** (Critical Improvement #3):

**SessionManager - Critical for CDC**:
- **Why**: Tier1CDCPoller processes 10,000+ cases per run (5-10 minutes)
- **Pattern**: Checkpoint every 100 cases for resume capability
- **Storage**: `marcosand20260203/cdc-checkpoints/tier1-poller/`

```python
# In Tier1CDCPoller function
from professional_components import SessionManager

session_mgr = SessionManager("tier1-cdc-poller", base_path)
checkpoint = session_mgr.load_latest_checkpoint()
start_case_index = checkpoint["data"]["last_processed_index"] if checkpoint else 0

for i in range(start_case_index, len(cases)):
    process_case(cases[i])
    if i % 100 == 0:
        session_mgr.save_checkpoint(f"case_{i}", {
            "last_processed_index": i,
            "cases_processed": i + 1
        })
```

**DebugArtifactCollector - Evidence at Boundaries**:
- **Why**: ATO compliance requires evidence of CDC operations
- **Pattern**: Capture state before/after poll operations
- **Storage**: `marcosand20260203/cdc-debug/{timestamp}/`

```python
from professional_components import DebugArtifactCollector

debug_collector = DebugArtifactCollector("cdc-poller", base_path)

# Capture pre-poll state
await debug_collector.capture_state("before_poll")
try:
    poll_result = await execute_poll()
    await debug_collector.capture_state("poll_success")
except Exception as e:
    await debug_collector.capture_state("poll_error")
    raise
```

**4. Observability Strategy** (Critical Improvement #4):

**Application Insights Metrics**:
```python
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace

configure_azure_monitor(connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"))
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("tier1_cdc_poll") as span:
    span.set_attribute("scope_id", scope_id)
    span.set_attribute("cases_checked", len(cases))
    span.set_attribute("changes_detected", change_count)
    result = execute_poll()
```

**Kusto Queries for Monitoring**:
```kusto
// CDC Poll Performance
traces
| where operation_Name == "tier1_cdc_poll"
| summarize avg(duration_ms), max(duration_ms) by bin(timestamp, 1d)

// Change Detection Rate
customEvents
| where name == "change_detected"
| summarize count() by change_class, bin(timestamp, 1h)
```

### Project Structure

```
15-cdc/
 README.md                              # Project overview
 CDC-IMPLEMENTATION-START.md            # Complete implementation guide
 DEVBOX-DEPLOYMENT.md                   # DevBox container deployment
 cdc-mvp-design.md                      # Architecture principles
 downstream-invalidation-contract.md    # Processing rules
 acceptance-tests.md                    # 26 test specifications

 .env.template                          # Environment configuration template
 .github/
    copilot-instructions.md            # This file

 scripts/
    dev/
       test-azure-connectivity.py     # Azure connectivity validation (7 tests)
    deployment/
        deploy-cosmos-schema.py        # Deploy 12 Cosmos DB containers
        create-storage-queues.ps1      # Create 5 downstream queues

 src/                                   # CDC implementation (Week 2+)
    case_registry.py                   # Stable case identities
    artifact_index.py                  # Content-addressable artifact storage
    corpus_registry.py                 # Multi-corpus management
    change_classifier.py               # Policy-driven classification
    downstream_processor.py            # Action execution

 tests/
    conftest.py                        # Shared test fixtures
    pytest.ini                         # Pytest configuration
    requirements.txt                   # Test dependencies
    test_cosmos_connectivity.py        # Cosmos DB tests

 change-policy.yaml                     # 7 change class definitions
 scope.yaml                             # Corpus boundaries
 immutability.yaml                      # Polling frequencies
 language-policy.yaml                   # EN/FR/BI handling

 debug/                                 # DebugArtifactCollector output
 sessions/                              # SessionManager checkpoints
 logs/                                  # Structured error logs
```

### Development Workflows

**DevBox Container Setup** (Week 0):

```bash
# 1. Copy environment template
cd /workspace/15-cdc
cp .env.template .env

# 2. Fill Azure resource details
# Edit .env with:
# - AZURE_COSMOSDB_ENDPOINT=https://marco-sandbox-cosmos.documents.azure.com
# - AZURE_STORAGE_ACCOUNT_NAME=marcosand20260203
# - AZURE_FUNCTION_APP_NAME=marco-sandbox-func
# - AZURE_KEY_VAULT_URL=https://marcosandkv20260203.vault.azure.net
# - CANLII_API_KEY=<your-api-key>

# 3. Load environment
export $(cat .env | grep -v '^#' | xargs)

# 4. Install dependencies
pip install -r tests/requirements.txt
pip install azure-cosmos azure-storage-blob azure-storage-queue azure-identity

# 5. Run connectivity validation
python scripts/dev/test-azure-connectivity.py

# Expected: 7/7 tests passed
```

**Schema Deployment** (Week 1):

```bash
# Deploy Cosmos DB schema (12 containers)
python scripts/deployment/deploy-cosmos-schema.py

# Create storage queues (5 queues)
pwsh scripts/deployment/create-storage-queues.ps1

# Verify deployment
az cosmosdb sql container list \
  --account-name marco-sandbox-cosmos \
  --database-name cdc-jurisprudence \
  --resource-group EsDAICoE-Sandbox

az storage queue list \
  --account-name marcosand20260203 \
  --auth-mode login
```

**Quick Commands**:

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `python scripts/dev/test-azure-connectivity.py` | Validate Azure connectivity | Before deployment |
| `python scripts/dev/test-azure-connectivity.py --dry-run` | Preview without writes | Safe validation |
| `python scripts/deployment/deploy-cosmos-schema.py` | Deploy Cosmos DB schema | Week 1 deployment |
| `python scripts/deployment/deploy-cosmos-schema.py --dry-run` | Preview schema | Before actual deployment |
| `pwsh scripts/deployment/create-storage-queues.ps1` | Create 5 queues | Week 1 deployment |
| `pwsh scripts/deployment/create-storage-queues.ps1 -DryRun` | Preview queue creation | Safe validation |
| `pytest tests/ -v` | Run all tests | Development |
| `pytest tests/ -v -m unit` | Run unit tests only | Fast validation |
| `pytest tests/ -v -m integration` | Run integration tests | Requires Azure access |
| `pytest tests/ -v -m acceptance` | Run acceptance tests | End-to-end validation |
| `pytest tests/ -v -m cosmos` | Run Cosmos DB tests | Cosmos-specific validation |

### Azure Resource Inventory

**EsDAICoE-Sandbox Resources** (All Already Deployed):

| Resource | Purpose | Configuration |
|----------|---------|---------------|
| **marco-sandbox-cosmos** | CDC evidence storage | 12 containers, serverless mode |
| **marcosand20260203** | Artifacts + Queues + Checkpoints | Blob + Queue services enabled |
| **marco-sandbox-func** | CDC + existing functions | Consumption Plan, Python 3.10 |
| **marco-sandbox-search** | Jurisprudence index | Standard S1, hybrid search |
| **marcosandkv20260203** | Secrets storage | API keys, connection strings |

**Cosmos DB Containers** (12 total):
1. `corpus_registry` - Multi-corpus management with SLO tiers
2. `case_registry` - Stable case identities across external key changes
3. `case_source_key` - External identifiers (URLs, case IDs)
4. `case_version` - Versioned case states
5. `case_text` - Extracted text with language tracking
6. `artifact` - Content-addressable artifact storage
7. `poll_run` - CDC execution records
8. `change_event` - Detected changes with classifications
9. `scope_definition` - Corpus boundaries and polling frequencies
10. `policy_version` - Change classification policies
11. `downstream_action` - Action execution tracking
12. `freshness_metric` - SLO monitoring data

**Storage Account Structure**:
```
marcosand20260203/
 Containers (Blobs):
    cdc-artifacts/           # PDFs, HTML, text files
    cdc-checkpoints/         # SessionManager state
    cdc-debug/               # DebugArtifactCollector evidence

 Queues:
     fetch-artifact-queue     # Triggers FetchArtifact function
     extract-text-queue       # Triggers FileFormRecSubmissionPDF
     generate-chunks-queue    # Triggers TextEnrichment
     embed-chunks-queue       # Triggers TextEnrichment
     update-index-queue       # Triggers UpdateSearchIndex
```

### Environment Configuration

**Required Environment Variables** (`.env` template provided):

```bash
# Azure Credentials
AZURE_SUBSCRIPTION_ID=d2d4e571-e0f2-4f6c-901a-f88f7669bcba
AZURE_TENANT_ID=bfb12ca1-7f37-47d5-9cf5-8aa52214a0d8

# Cosmos DB
AZURE_COSMOSDB_ENDPOINT=https://marco-sandbox-cosmos.documents.azure.com
AZURE_COSMOSDB_DATABASE=cdc-jurisprudence

# Blob Storage
AZURE_STORAGE_ACCOUNT_NAME=marcosand20260203
AZURE_STORAGE_CONNECTION_STRING=<from-azure-cli>

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://marco-sandbox-search.search.windows.net
AZURE_SEARCH_INDEX_NAME=index-jurisprudence

# Function App
AZURE_FUNCTION_APP_NAME=marco-sandbox-func
AZURE_RESOURCE_GROUP=EsDAICoE-Sandbox

# Key Vault
AZURE_KEY_VAULT_URL=https://marcosandkv20260203.vault.azure.net

# CanLII API
CANLII_API_KEY=<your-api-key>

# Professional Components
ENABLE_DEBUG_ARTIFACT_COLLECTOR=true
ENABLE_SESSION_MANAGER=true
ENABLE_STRUCTURED_ERROR_HANDLER=true
SESSION_CHECKPOINT_INTERVAL=100

# DevBox Container
DEVBOX_CONTAINER_NAME=cdc-devbox
LOCAL_DEBUG=false
AZURE_IDENTITY_EXCLUDE_MANAGED_IDENTITY_CREDENTIAL=true
PYTHONIOENCODING=utf-8
```

### Critical Code Patterns

#### Pattern 1: Case Registry (Stable Identity Across External Key Changes)

**Purpose**: Assign immutable `case_id` based on canonical inputs even when CanLII URLs change

**Implementation**:
```python
class CaseRegistry:
    """Maintain stable case identities across external key changes"""
    
    def register_case(self, tribunal_id: str, decision_date: str, 
                      external_keys: List[str], metadata: Dict) -> str:
        """
        Find existing case by external_keys, or create new case.
        Returns case_id (immutable).
        """
        # 1. Search for existing case by known external keys
        existing_case = self._find_by_external_key(external_keys)
        if existing_case:
            return existing_case["case_id"]
        
        # 2. Create new case with deterministic UUID
        case_id = self._generate_case_id(tribunal_id, decision_date, metadata)
        
        # 3. Store case and external key mappings
        self.cosmos_container.upsert_item({
            "id": case_id,
            "tribunal_id": tribunal_id,
            "decision_date": decision_date,
            "metadata": metadata
        })
        
        for key in external_keys:
            self.external_key_container.upsert_item({
                "external_key": key,
                "case_id": case_id
            })
        
        return case_id
    
    def _generate_case_id(self, tribunal_id: str, decision_date: str, 
                          metadata: Dict) -> str:
        """Deterministic UUID from canonical inputs"""
        canonical_input = f"{tribunal_id}|{decision_date}|{metadata.get('neutral_citation')}"
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, canonical_input))
```

**Test Coverage**: B1, B2, B3 from [acceptance-tests.md](../acceptance-tests.md)

#### Pattern 2: Artifact Index (Content-Addressable Storage)

**Purpose**: Track observed artifacts with content hashes to avoid redundant blob storage

**Implementation**:
```python
class ArtifactIndex:
    """Track observed artifacts (PDF/HTML/text) with content hashes"""
    
    def track_artifact(self, case_version_id: str, artifact_type: str, 
                       content_bytes: bytes) -> str:
        """
        Compute content hash, check if artifact already exists.
        If new, upload to blob storage and create artifact record.
        Returns artifact_id.
        """
        content_hash = self._compute_content_hash(content_bytes)
        
        # Check if artifact already exists
        existing = self.cosmos_container.query_items(
            query="SELECT * FROM c WHERE c.content_hash = @hash",
            parameters=[{"name": "@hash", "value": content_hash}]
        )
        
        if existing:
            return existing[0]["artifact_id"]
        
        # New artifact - upload to blob
        artifact_id = str(ulid.ULID())
        blob_url = self._upload_to_blob(artifact_id, content_bytes, artifact_type)
        
        # Create artifact record
        self.cosmos_container.upsert_item({
            "id": artifact_id,
            "case_version_id": case_version_id,
            "artifact_type": artifact_type,
            "content_hash": content_hash,
            "blob_url": blob_url,
            "size_bytes": len(content_bytes)
        })
        
        return artifact_id
    
    def _compute_content_hash(self, content_bytes: bytes) -> str:
        """SHA-256 hash of raw bytes"""
        return hashlib.sha256(content_bytes).hexdigest()
    
    def _upload_to_blob(self, artifact_id: str, content_bytes: bytes, 
                        artifact_type: str) -> str:
        """Upload to Azure Blob Storage if not already present"""
        container_client = self.blob_service.get_container_client("cdc-artifacts")
        blob_name = f"{artifact_type}/{artifact_id}.{self._get_extension(artifact_type)}"
        container_client.upload_blob(blob_name, content_bytes, overwrite=False)
        return f"https://{self.storage_account}.blob.core.windows.net/cdc-artifacts/{blob_name}"
```

**Test Coverage**: C1, C2, C3, C4 from [acceptance-tests.md](../acceptance-tests.md)

#### Pattern 3: Change Classification (Policy-Driven)

**Purpose**: Classify changes based on rules in change-policy.yaml

**Implementation**:
```python
class ChangeClassifier:
    """Policy-driven change classification"""
    
    def __init__(self, policy_path: Path):
        with open(policy_path) as f:
            self.policy = yaml.safe_load(f)
        self.policy_version = self.policy["version"]
        self.policy_hash = hashlib.sha256(policy_path.read_bytes()).hexdigest()
    
    def classify_change(self, old_metadata: Dict, new_metadata: Dict, 
                        old_artifact_hash: str, new_artifact_hash: str) -> Tuple[str, str]:
        """
        Classify change based on policy rules.
        Returns (change_class, reason)
        """
        # Check for structural changes (new case, identity remapping)
        if not old_metadata:
            return "structural", "New case detected"
        
        # Check for availability changes (language added/removed)
        if old_metadata.get("language") != new_metadata.get("language"):
            return "availability", "Language availability changed"
        
        # Check for content changes (PDF bytes changed)
        if old_artifact_hash != new_artifact_hash:
            return "content", "PDF content hash changed"
        
        # Check for metadata changes (title, keywords)
        metadata_diff = self._metadata_diff(old_metadata, new_metadata)
        if metadata_diff:
            return "metadata", f"Metadata changed: {', '.join(metadata_diff)}"
        
        # No meaningful change
        return "cosmetic", "No meaningful change detected"
    
    def get_downstream_actions(self, change_class: str) -> List[str]:
        """Get required downstream actions from policy"""
        return self.policy["change_classes"][change_class]["actions"]
```

**Policy Definition** (change-policy.yaml):
```yaml
version: "0.1.0"
change_classes:
  structural:
    actions: [update_registry, fetch_artifact, extract_text, generate_chunks, embed_chunks, update_index]
  content:
    actions: [fetch_artifact, extract_text, generate_chunks, embed_chunks, update_index]
  metadata:
    actions: [update_registry, update_index_metadata_only]
  cosmetic:
    actions: [update_registry]
```

### Testing

**Test Structure**:

```
tests/
 conftest.py                     # Shared fixtures (mock clients, sample data)
 pytest.ini                      # Pytest configuration (markers, coverage)
 requirements.txt                # Test dependencies

 test_cosmos_connectivity.py     # Cosmos DB operations
 test_blob_storage.py            # Blob upload/download
 test_queue_messaging.py         # Queue send/receive
 test_case_registry.py           # Case identity logic
 test_artifact_index.py          # Content-addressable storage
 test_change_classifier.py       # Change detection rules
 test_professional_components.py # SessionManager, DebugArtifactCollector
```

**Running Tests**:

```bash
# All tests (unit + integration)
pytest tests/ -v

# Unit tests only (fast, no Azure)
pytest tests/ -v -m unit

# Integration tests (requires Azure access)
pytest tests/ -v -m integration

# Acceptance tests (end-to-end scenarios)
pytest tests/ -v -m acceptance

# Specific component tests
pytest tests/ -v -m cosmos        # Cosmos DB tests
pytest tests/ -v -m blob          # Blob Storage tests
pytest tests/ -v -m queue         # Queue tests

# Coverage report
pytest tests/ -v --cov=src --cov-report=html
```

**Test Markers** (defined in pytest.ini):
- `unit` - Unit tests (fast, no external dependencies)
- `integration` - Integration tests (requires Azure services)
- `acceptance` - Acceptance tests (end-to-end scenarios from acceptance-tests.md)
- `smoke` - Smoke tests (critical path validation)
- `slow` - Tests that take >5 seconds
- `cosmos`, `blob`, `queue`, `search`, `canlii` - Component-specific tests

### CI/CD Pipeline

**Week 0-1**: Manual deployment (prerequisite validation + schema deployment)

**Week 2+**: Automated CI/CD (to be implemented)

**Proposed Pipeline Stages**:
1. **Validation** - Run pytest unit tests, lint checks
2. **Integration** - Deploy to dev environment, run integration tests
3. **Deployment** - Deploy functions to marco-sandbox-func
4. **Smoke Test** - Validate critical path (poll -> detect -> process)
5. **Monitoring** - Alert on test failures, deployment issues

### Troubleshooting

#### Issue 1: Cosmos DB Connection Timeout

**Symptom**: `azure.cosmos.errors.CosmosHttpResponseError: Request timeout`  
**Cause**: Network connectivity or private endpoint configuration  
**Solution**:

```bash
# Verify endpoint reachable
curl -I https://marco-sandbox-cosmos.documents.azure.com

# Check private endpoint status
az cosmosdb show --name marco-sandbox-cosmos \
  --resource-group EsDAICoE-Sandbox \
  --query "privateEndpointConnections"

# Test with DefaultAzureCredential
python scripts/dev/test-azure-connectivity.py --tests cosmos
```

#### Issue 2: Queue Not Found

**Symptom**: `azure.core.exceptions.ResourceNotFoundError: Queue not found`  
**Cause**: Queue not created or wrong storage account  
**Solution**:

```bash
# List existing queues
az storage queue list \
  --account-name marcosand20260203 \
  --auth-mode login

# Recreate queues
pwsh scripts/deployment/create-storage-queues.ps1
```

#### Issue 3: CANLII_API_KEY Invalid

**Symptom**: `[FAIL] CanLII API returned 401: Unauthorized`  
**Cause**: API key not set or expired  
**Solution**:

```bash
# Verify API key in .env
cat .env | grep CANLII_API_KEY

# Test API key manually
curl -H "API-Key: $CANLII_API_KEY" https://api.canlii.org/v1/caseBrowse/en/sst/

# Store in Key Vault (recommended)
az keyvault secret set \
  --vault-name marcosandkv20260203 \
  --name canlii-api-key \
  --value "<your-api-key>"
```

#### Issue 4: SessionManager Checkpoint Not Resuming

**Symptom**: Poll restarts from beginning instead of last checkpoint  
**Cause**: Checkpoint file not found or corrupted  
**Solution**:

```bash
# Check checkpoint directory
az storage blob list \
  --container-name cdc-checkpoints \
  --account-name marcosand20260203 \
  --prefix tier1-poller/

# Manually load latest checkpoint
python -c "
from src.professional_components import SessionManager
mgr = SessionManager('tier1-cdc-poller', '.')
checkpoint = mgr.load_latest_checkpoint()
print(checkpoint)
"
```

### Performance Optimization

**CDC Poll Performance**:
- **Target**: Process 10,000 cases in <10 minutes
- **Checkpointing**: Save checkpoint every 100 cases (6-second overhead per checkpoint)
- **Parallel Processing**: Not needed for Tier 1 (metadata-only, fast CanLII API)
- **Bottleneck**: CanLII API rate limit (monitor with Application Insights)

**Cosmos DB Optimization**:
- **Partition Keys**: Chosen for query patterns (tribunal_id, scope_id, poll_run_id)
- **Indexing**: Default indexing adequate for MVP
- **Serverless Mode**: Cost-effective for CDC workload (bursty, daily polling)

**Queue Processing**:
- **Throughput**: Downstream functions auto-scale based on queue depth
- **Retry Policy**: Built into Azure Functions (exponential backoff)
- **Dead Letter**: Poisonous messages moved to DLQ after 5 retries

**Monitoring Queries**:
```kusto
// CDC Poll Performance (Application Insights)
traces
| where operation_Name == "tier1_cdc_poll"
| summarize 
    avg_duration=avg(duration_ms),
    max_duration=max(duration_ms),
    p95_duration=percentile(duration_ms, 95)
  by bin(timestamp, 1d)

// Change Detection Rate
customEvents
| where name == "change_detected"
| summarize count() by change_class, bin(timestamp, 1h)
| render columnchart

// Queue Depth Monitoring
customMetrics
| where name == "queue_depth"
| summarize avg(value) by queue_name, bin(timestamp, 5m)
| render timechart
```

---

**For comprehensive architecture details, see [cdc-mvp-design.md](../cdc-mvp-design.md)**  
**For complete implementation guide, see [CDC-IMPLEMENTATION-START.md](../CDC-IMPLEMENTATION-START.md)**  
**For DevBox deployment instructions, see [DEVBOX-DEPLOYMENT.md](../DEVBOX-DEPLOYMENT.md)**
