#!/usr/bin/env python3
"""
Code Quality Check Script - T066

Comprehensive code quality analysis and duplication detection for the course platform backend.
Checks for code quality issues, duplications, and potential improvements.
"""

import os
import ast
import re
import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Any, Tuple
from collections import defaultdict, Counter
import hashlib

class CodeQualityChecker:
    """Comprehensive code quality analyzer."""
    
    def __init__(self, src_path: str):
        self.src_path = Path(src_path)
        self.issues = defaultdict(list)
        self.duplications = []
        self.metrics = {
            'total_files': 0,
            'total_lines': 0,
            'total_functions': 0,
            'total_classes': 0,
            'complexity_issues': 0,
            'duplication_blocks': 0,
            'code_smells': 0,
        }
        
        # Quality thresholds
        self.thresholds = {
            'max_function_length': 50,
            'max_class_length': 500,
            'max_complexity': 10,
            'min_duplication_lines': 5,
            'max_duplicated_percentage': 15.0,
        }
    
    def run_analysis(self) -> Dict[str, Any]:
        """Run complete code quality analysis."""
        print("🔍 Starting comprehensive code quality analysis...")
        
        python_files = list(self.src_path.rglob("*.py"))
        self.metrics['total_files'] = len(python_files)
        
        for file_path in python_files:
            if self._should_skip_file(file_path):
                continue
                
            try:
                self._analyze_file(file_path)
            except Exception as e:
                self.issues['parse_errors'].append({
                    'file': str(file_path),
                    'error': str(e)
                })
        
        # Detect code duplications
        self._detect_duplications(python_files)
        
        # Generate report
        return self._generate_report()
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = [
            '__pycache__',
            '.git',
            'migrations',
            'test_',
            'conftest.py',
            '__init__.py'
        ]
        
        path_str = str(file_path)
        return any(pattern in path_str for pattern in skip_patterns)
    
    def _analyze_file(self, file_path: Path):
        """Analyze a single Python file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.splitlines()
        
        self.metrics['total_lines'] += len(lines)
        
        try:
            tree = ast.parse(content)
            self._analyze_ast(tree, file_path, lines)
        except SyntaxError as e:
            self.issues['syntax_errors'].append({
                'file': str(file_path),
                'line': e.lineno,
                'error': str(e)
            })
        
        # Text-based analysis
        self._analyze_text_patterns(file_path, content, lines)
    
    def _analyze_ast(self, tree: ast.AST, file_path: Path, lines: List[str]):
        """Analyze AST for code quality issues."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self.metrics['total_functions'] += 1
                self._check_function_quality(node, file_path, lines)
            
            elif isinstance(node, ast.ClassDef):
                self.metrics['total_classes'] += 1
                self._check_class_quality(node, file_path, lines)
    
    def _check_function_quality(self, node: ast.FunctionDef, file_path: Path, lines: List[str]):
        """Check function-specific quality issues."""
        func_lines = self._get_node_lines(node, lines)
        func_length = len(func_lines)
        
        # Check function length
        if func_length > self.thresholds['max_function_length']:
            self.issues['long_functions'].append({
                'file': str(file_path),
                'function': node.name,
                'line': node.lineno,
                'length': func_length,
                'threshold': self.thresholds['max_function_length']
            })
        
        # Check complexity (simplified cyclomatic complexity)
        complexity = self._calculate_complexity(node)
        if complexity > self.thresholds['max_complexity']:
            self.issues['complex_functions'].append({
                'file': str(file_path),
                'function': node.name,
                'line': node.lineno,
                'complexity': complexity,
                'threshold': self.thresholds['max_complexity']
            })
            self.metrics['complexity_issues'] += 1
        
        # Check for missing docstrings
        if not ast.get_docstring(node):
            self.issues['missing_docstrings'].append({
                'file': str(file_path),
                'function': node.name,
                'line': node.lineno,
                'type': 'function'
            })
        
        # Check for too many parameters
        if len(node.args.args) > 6:
            self.issues['too_many_parameters'].append({
                'file': str(file_path),
                'function': node.name,
                'line': node.lineno,
                'parameters': len(node.args.args)
            })
    
    def _check_class_quality(self, node: ast.ClassDef, file_path: Path, lines: List[str]):
        """Check class-specific quality issues."""
        class_lines = self._get_node_lines(node, lines)
        class_length = len(class_lines)
        
        # Check class length
        if class_length > self.thresholds['max_class_length']:
            self.issues['long_classes'].append({
                'file': str(file_path),
                'class': node.name,
                'line': node.lineno,
                'length': class_length,
                'threshold': self.thresholds['max_class_length']
            })
        
        # Check for missing docstrings
        if not ast.get_docstring(node):
            self.issues['missing_docstrings'].append({
                'file': str(file_path),
                'class': node.name,
                'line': node.lineno,
                'type': 'class'
            })
        
        # Count methods
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        if len(methods) > 20:
            self.issues['too_many_methods'].append({
                'file': str(file_path),
                'class': node.name,
                'line': node.lineno,
                'methods': len(methods)
            })
    
    def _analyze_text_patterns(self, file_path: Path, content: str, lines: List[str]):
        """Analyze text patterns for code smells."""
        # Check for TODO/FIXME comments
        for i, line in enumerate(lines, 1):
            if re.search(r'(TODO|FIXME|XXX|HACK)', line, re.IGNORECASE):
                self.issues['todo_comments'].append({
                    'file': str(file_path),
                    'line': i,
                    'content': line.strip()
                })
        
        # Check for long lines
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                self.issues['long_lines'].append({
                    'file': str(file_path),
                    'line': i,
                    'length': len(line),
                    'content': line[:100] + '...' if len(line) > 100 else line
                })
        
        # Check for print statements (should use logging)
        for i, line in enumerate(lines, 1):
            if re.search(r'\bprint\s*\(', line) and 'test' not in str(file_path).lower():
                self.issues['print_statements'].append({
                    'file': str(file_path),
                    'line': i,
                    'content': line.strip()
                })
        
        # Check for hardcoded strings that might be constants
        hardcoded_pattern = r'["\']([A-Z_]{3,})["\']'
        for i, line in enumerate(lines, 1):
            matches = re.findall(hardcoded_pattern, line)
            for match in matches:
                if match not in ['GET', 'POST', 'PUT', 'DELETE']:  # Common HTTP methods
                    self.issues['hardcoded_strings'].append({
                        'file': str(file_path),
                        'line': i,
                        'string': match,
                        'content': line.strip()
                    })
    
    def _detect_duplications(self, python_files: List[Path]):
        """Detect code duplications."""
        print("🔍 Detecting code duplications...")
        
        # Simple line-based duplication detection
        line_hashes = defaultdict(list)
        
        for file_path in python_files:
            if self._should_skip_file(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for i, line in enumerate(lines):
                    # Skip empty lines and comments
                    clean_line = line.strip()
                    if not clean_line or clean_line.startswith('#'):
                        continue
                    
                    # Create hash of normalized line
                    normalized = re.sub(r'\s+', ' ', clean_line)
                    line_hash = hashlib.md5(normalized.encode()).hexdigest()
                    
                    line_hashes[line_hash].append({
                        'file': str(file_path),
                        'line_num': i + 1,
                        'content': clean_line
                    })
            
            except Exception as e:
                continue
        
        # Find duplicated blocks
        for line_hash, occurrences in line_hashes.items():
            if len(occurrences) > 1:
                # Group by content to find actual duplications
                content_groups = defaultdict(list)
                for occ in occurrences:
                    content_groups[occ['content']].append(occ)
                
                for content, instances in content_groups.items():
                    if len(instances) > 1:
                        self.duplications.append({
                            'content': content,
                            'occurrences': instances,
                            'count': len(instances)
                        })
        
        self.metrics['duplication_blocks'] = len(self.duplications)
    
    def _get_node_lines(self, node: ast.AST, lines: List[str]) -> List[str]:
        """Get lines of code for an AST node."""
        if hasattr(node, 'end_lineno') and node.end_lineno:
            return lines[node.lineno - 1:node.end_lineno]
        else:
            # Fallback for older Python versions
            return lines[node.lineno - 1:node.lineno + 10]  # Approximate
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate simplified cyclomatic complexity."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive quality report."""
        total_lines = self.metrics['total_lines']
        
        # Calculate duplication percentage
        duplicated_lines = sum(dup['count'] for dup in self.duplications)
        duplication_percentage = (duplicated_lines / total_lines * 100) if total_lines > 0 else 0
        
        # Count total issues
        total_issues = sum(len(issues) for issues in self.issues.values())
        self.metrics['code_smells'] = total_issues
        
        report = {
            'summary': {
                'total_files_analyzed': self.metrics['total_files'],
                'total_lines_of_code': total_lines,
                'total_functions': self.metrics['total_functions'],
                'total_classes': self.metrics['total_classes'],
                'total_issues_found': total_issues,
                'duplication_percentage': round(duplication_percentage, 2),
                'quality_score': self._calculate_quality_score(),
            },
            'issues_by_category': dict(self.issues),
            'duplications': self.duplications[:20],  # Top 20 duplications
            'metrics': self.metrics,
            'thresholds': self.thresholds,
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _calculate_quality_score(self) -> float:
        """Calculate overall quality score (0-100)."""
        total_lines = self.metrics['total_lines']
        if total_lines == 0:
            return 100.0
        
        # Deduct points for various issues
        score = 100.0
        
        # Complexity issues (heavy penalty)
        score -= self.metrics['complexity_issues'] * 5
        
        # Duplication (moderate penalty)
        duplicated_lines = sum(dup['count'] for dup in self.duplications)
        duplication_ratio = duplicated_lines / total_lines
        score -= duplication_ratio * 30
        
        # Code smells (light penalty)
        total_issues = sum(len(issues) for issues in self.issues.values())
        issue_ratio = total_issues / total_lines
        score -= issue_ratio * 1000  # Scale appropriately
        
        return max(0.0, min(100.0, score))
    
    def _generate_recommendations(self) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []
        
        if self.issues.get('long_functions'):
            recommendations.append("Consider breaking down long functions into smaller, more focused functions")
        
        if self.issues.get('complex_functions'):
            recommendations.append("Reduce cyclomatic complexity by extracting logic into separate functions")
        
        if self.issues.get('missing_docstrings'):
            recommendations.append("Add docstrings to all public functions and classes")
        
        if self.duplications:
            recommendations.append("Extract duplicated code into reusable functions or constants")
        
        if self.issues.get('print_statements'):
            recommendations.append("Replace print statements with proper logging")
        
        if self.issues.get('hardcoded_strings'):
            recommendations.append("Move hardcoded strings to constants or configuration files")
        
        if self.issues.get('long_lines'):
            recommendations.append("Break long lines to improve readability (max 120 characters)")
        
        if self.issues.get('todo_comments'):
            recommendations.append("Address TODO/FIXME comments or convert them to proper issues")
        
        return recommendations


class CodeDeduplicator:
    """Automated code deduplication suggestions."""
    
    def __init__(self, duplications: List[Dict]):
        self.duplications = duplications
    
    def generate_deduplication_plan(self) -> List[Dict[str, Any]]:
        """Generate plan for removing duplications."""
        plan = []
        
        # Group duplications by similarity
        high_priority = [dup for dup in self.duplications if dup['count'] >= 3]
        
        for i, duplication in enumerate(high_priority[:10]):  # Top 10 priority
            content = duplication['content']
            
            # Suggest extraction
            if len(content) > 20:  # Substantial duplications
                plan.append({
                    'priority': 'high',
                    'type': 'extract_function',
                    'description': f"Extract duplicated logic: {content[:50]}...",
                    'occurrences': duplication['occurrences'],
                    'suggested_function_name': self._suggest_function_name(content),
                    'files_affected': list(set(occ['file'] for occ in duplication['occurrences']))
                })
        
        return plan
    
    def _suggest_function_name(self, content: str) -> str:
        """Suggest a function name based on content."""
        # Simple heuristic - extract meaningful words
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', content)
        meaningful_words = [w for w in words if len(w) > 3 and not w.isupper()]
        
        if meaningful_words:
            return f"extracted_{meaningful_words[0].lower()}"
        else:
            return "extracted_function"


def main():
    """Main execution function."""
    if len(sys.argv) > 1:
        src_path = sys.argv[1]
    else:
        src_path = "src"
    
    if not os.path.exists(src_path):
        print(f"❌ Error: Source path '{src_path}' does not exist")
        sys.exit(1)
    
    print(f"🔍 Analyzing code quality in: {src_path}")
    print("=" * 60)
    
    # Run quality analysis
    checker = CodeQualityChecker(src_path)
    report = checker.run_analysis()
    
    # Display summary
    summary = report['summary']
    print(f"📊 ANALYSIS SUMMARY")
    print(f"Files analyzed: {summary['total_files_analyzed']}")
    print(f"Lines of code: {summary['total_lines_of_code']:,}")
    print(f"Functions: {summary['total_functions']}")
    print(f"Classes: {summary['total_classes']}")
    print(f"Issues found: {summary['total_issues_found']}")
    print(f"Duplication: {summary['duplication_percentage']}%")
    print(f"Quality score: {summary['quality_score']:.1f}/100")
    print("=" * 60)
    
    # Display top issues
    print("🚨 TOP ISSUES BY CATEGORY:")
    for category, issues in report['issues_by_category'].items():
        if issues:
            print(f"  {category}: {len(issues)} issues")
            # Show first few examples
            for issue in issues[:3]:
                if 'file' in issue:
                    file_short = issue['file'].split('/')[-1]
                    line = issue.get('line', '?')
                    print(f"    - {file_short}:{line}")
    
    # Display duplications
    if report['duplications']:
        print("\n🔄 TOP CODE DUPLICATIONS:")
        for i, dup in enumerate(report['duplications'][:5], 1):
            print(f"  {i}. Found {dup['count']} times: {dup['content'][:60]}...")
    
    # Display recommendations
    if report['recommendations']:
        print("\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
    
    # Generate deduplication plan
    if report['duplications']:
        print("\n🛠️  DEDUPLICATION PLAN:")
        deduplicator = CodeDeduplicator(report['duplications'])
        plan = deduplicator.generate_deduplication_plan()
        
        for i, item in enumerate(plan, 1):
            print(f"  {i}. {item['description']}")
            print(f"     Priority: {item['priority']}")
            print(f"     Files: {len(item['files_affected'])}")
            print(f"     Suggested function: {item['suggested_function_name']}")
    
    # Save detailed report
    report_file = "code_quality_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📋 Detailed report saved to: {report_file}")
    
    # Quality gates
    print("\n🚦 QUALITY GATES:")
    quality_score = summary['quality_score']
    duplication_pct = summary['duplication_percentage']
    
    if quality_score >= 80:
        print("  ✅ Quality Score: PASSED")
    elif quality_score >= 60:
        print("  ⚠️  Quality Score: WARNING")
    else:
        print("  ❌ Quality Score: FAILED")
    
    if duplication_pct <= 15:
        print("  ✅ Duplication: PASSED")
    elif duplication_pct <= 25:
        print("  ⚠️  Duplication: WARNING")
    else:
        print("  ❌ Duplication: FAILED")
    
    # Overall status
    overall_passed = quality_score >= 60 and duplication_pct <= 25
    print(f"\n🎯 OVERALL STATUS: {'✅ PASSED' if overall_passed else '❌ FAILED'}")
    
    return 0 if overall_passed else 1


if __name__ == "__main__":
    sys.exit(main())