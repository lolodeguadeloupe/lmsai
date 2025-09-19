# Course Management CLI Usage Guide

The Course Management CLI provides powerful command-line tools for managing courses in the Learning Management System. This comprehensive CLI interface allows administrators and developers to perform all essential course operations from the terminal.

## 🚀 Quick Start

```bash
# Show all available commands
python -m cli.courses --help

# Create a new course
python -m cli.courses create \
  --title "Introduction to Python" \
  --description "Learn Python programming fundamentals" \
  --domain programming \
  --proficiency beginner \
  --objectives "Understand Python syntax" \
  --objectives "Write basic programs"

# List all courses
python -m cli.courses list --format table

# Export a course to SCORM format
python -m cli.courses export <course-id> --format scorm2004
```

## 📋 Available Commands

### Course Creation
```bash
# Basic course creation
python -m cli.courses create \
  --title "Course Title" \
  --description "Course description" \
  --domain "programming" \
  --proficiency beginner \
  --difficulty 2.0 \
  --duration PT20H \
  --language en \
  --objectives "Learning objective 1" \
  --objectives "Learning objective 2" \
  --objectives "Learning objective 3"

# Advanced course creation with custom settings
python -m cli.courses create \
  --title "Advanced Python" \
  --description "Advanced Python programming concepts" \
  --domain programming \
  --proficiency advanced \
  --difficulty 4.5 \
  --duration PT40H \
  --objectives "Master decorators" \
  --objectives "Understand metaclasses" \
  --objectives "Build complex applications" \
  --mode premium \
  --strategy parallel

# Asynchronous course creation
python -m cli.courses create \
  --title "Data Science Fundamentals" \
  --description "Introduction to data science" \
  --domain "data-science" \
  --proficiency intermediate \
  --objectives "Learn pandas" \
  --objectives "Master visualization" \
  --async
```

### Course Listing and Filtering
```bash
# List all courses in table format
python -m cli.courses list

# List with detailed information
python -m cli.courses list --details

# Filter by status
python -m cli.courses list --status ready

# Filter by domain
python -m cli.courses list --domain programming

# Pagination
python -m cli.courses list --page 2 --limit 5

# Sort by different fields
python -m cli.courses list --sort title
python -m cli.courses list --sort status

# Output in different formats
python -m cli.courses list --format json
python -m cli.courses list --format csv
```

### Course Status Monitoring
```bash
# Check course status
python -m cli.courses status <course-id>

# Watch for status changes (real-time monitoring)
python -m cli.courses status <course-id> --watch

# Custom watch interval
python -m cli.courses status <course-id> --watch --interval 10
```

### Export Operations
```bash
# Show available export formats
python -m cli.courses export-formats

# Export to SCORM 2004
python -m cli.courses export <course-id> --format scorm2004

# Export to xAPI with specific profile
python -m cli.courses export <course-id> --format xapi --xapi-profile cmi5

# Export to PDF
python -m cli.courses export <course-id> --format pdf

# Export to standalone HTML
python -m cli.courses export <course-id> --format html

# Export without assessments
python -m cli.courses export <course-id> --format scorm2004 --no-assessments

# Export without multimedia
python -m cli.courses export <course-id> --format pdf --no-multimedia
```

### Chapter Operations
```bash
# Regenerate a specific chapter
python -m cli.courses regenerate-chapter <course-id> 3

# Regenerate with premium mode
python -m cli.courses regenerate-chapter <course-id> 2 --mode premium

# Regenerate with reason for logging
python -m cli.courses regenerate-chapter <course-id> 1 \
  --mode balanced \
  --reason "Improve content quality based on feedback"
```

### Course Deletion
```bash
# Delete a course (with confirmation)
python -m cli.courses delete <course-id>

# Delete without confirmation prompt
python -m cli.courses delete <course-id> --confirm

# Force delete (even if generating)
python -m cli.courses delete <course-id> --force
```

### Batch Operations
```bash
# Batch delete draft courses older than 30 days (dry run)
python -m cli.courses batch delete \
  --status draft \
  --older-than 30 \
  --dry-run

# Batch delete archived courses
python -m cli.courses batch delete \
  --status archived \
  --confirm

# Batch export all ready courses to PDF
python -m cli.courses batch export \
  --status ready \
  --format pdf \
  --output-dir ./exports

# Batch export with concurrency control
python -m cli.courses batch export \
  --status published \
  --format scorm2004 \
  --max-concurrent 3
```

## 🔧 Configuration Options

### Generation Modes
- **fast**: Speed optimized with basic validation
- **balanced**: Default mode with standard validation (recommended)
- **premium**: Quality optimized with extensive validation

### Generation Strategies
- **sequential**: Generate chapters one by one (preserves dependencies)
- **parallel**: Generate all chapters simultaneously (fastest)
- **hybrid**: Balanced approach with batched parallel generation (recommended)

### Proficiency Levels
- **beginner**: Difficulty ≤ 2.5
- **intermediate**: Difficulty 2.0-4.0
- **advanced**: Difficulty ≥ 3.0
- **expert**: Difficulty ≥ 4.0

### Export Formats
| Format | Description | File Type | Standards |
|--------|-------------|-----------|-----------|
| `scorm2004` | SCORM 2004 4th Edition | ZIP | SCORM, IMS |
| `xapi` | xAPI (Tin Can API) | ZIP | xAPI, cmi5 |
| `qti21` | QTI 2.1 Assessment | ZIP | QTI, IMS |
| `pdf` | PDF Document | PDF | Portable |
| `html` | Standalone HTML | ZIP | Web Standard |

## 📊 Output Formats

### Table Format (Default)
Beautiful console tables with color coding and proper formatting.

### JSON Format
Machine-readable JSON output for automation and integration:
```json
{
  "courses": [...],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 25,
    "pages": 3
  }
}
```

### CSV Format
Comma-separated values for spreadsheet analysis.

## 🎨 Rich Console Features

- **Color-coded status indicators**
- **Progress bars for long operations**
- **Formatted tables with proper alignment**
- **Interactive confirmations**
- **Real-time status updates**
- **Beautiful panels and formatting**

## ⚡ Performance Features

- **Asynchronous operations** for non-blocking execution
- **Batch processing** for bulk operations
- **Concurrency control** for optimal resource usage
- **Pagination** for large datasets
- **Caching** for improved response times

## 🛡️ Safety Features

- **Confirmation prompts** for destructive operations
- **Dry run mode** for testing batch operations
- **Force flags** for overriding safety checks
- **Comprehensive validation** of input parameters
- **Graceful error handling** with helpful messages

## 🔍 Filtering and Search

### Status Filters
```bash
--status draft       # Show draft courses
--status generating  # Show courses being generated
--status ready       # Show completed courses
--status published   # Show published courses
--status archived    # Show archived courses
```

### Domain Filters
```bash
--domain programming     # Programming courses
--domain mathematics     # Math courses
--domain "data-science"  # Data science courses
```

### Time-based Filters
```bash
--older-than 30  # Courses older than 30 days
--older-than 7   # Courses older than 1 week
```

## 📈 Monitoring and Tracking

### Real-time Status Monitoring
```bash
# Watch course generation progress
python -m cli.courses status <course-id> --watch

# Custom refresh interval
python -m cli.courses status <course-id> --watch --interval 5
```

### Progress Indicators
- Spinner animations for ongoing operations
- Progress bars for batch operations
- Estimated time remaining
- Completion percentages

## 🚨 Error Handling

The CLI provides comprehensive error handling with:
- Clear error messages
- Validation feedback
- Recovery suggestions
- Exit codes for scripting

### Common Error Scenarios
- **Invalid UUID**: Clear validation message with format example
- **Course not found**: Helpful suggestions for finding courses
- **Permission errors**: Clear indication of access issues
- **Network timeouts**: Retry suggestions and troubleshooting tips

## 🔌 Integration with Existing Services

The CLI seamlessly integrates with:
- **CourseGenerationService**: AI-powered content creation
- **ExportService**: Multi-format exports
- **Database models**: Direct access to course data
- **Exception handling**: Consistent error patterns
- **Configuration system**: Uses existing settings

## 📝 Scripting and Automation

### Example Scripts
```bash
#!/bin/bash
# Automated course creation and export

COURSE_ID=$(python -m cli.courses create \
  --title "Automated Course" \
  --description "Generated via script" \
  --domain programming \
  --proficiency beginner \
  --objectives "Learn automation" \
  --format json | jq -r '.course_id')

echo "Created course: $COURSE_ID"

# Wait for completion and export
python -m cli.courses status $COURSE_ID --watch
python -m cli.courses export $COURSE_ID --format pdf
```

### Exit Codes
- `0`: Success
- `1`: General error
- `2`: Invalid arguments
- `3`: Resource not found
- `4`: Permission denied

## 🔧 Troubleshooting

### Common Issues

**Database Connection Errors**
```bash
# Check database configuration
echo $DATABASE_URL

# Test database connection
python -c "from src.database.session import get_db_session; print('DB OK')"
```

**Import Errors**
```bash
# Ensure you're in the correct directory
cd backend/

# Check Python path
python -c "import sys; print(sys.path)"
```

**Permission Issues**
```bash
# Check file permissions
ls -la src/cli/

# Ensure CLI module is executable
chmod +x src/cli/courses.py
```

### Debug Mode
```bash
# Enable verbose output
python -m cli.courses --verbose list

# Show detailed error information
python -m cli.courses create --title "Test" --verbose
```

## 📚 Examples Repository

Complete examples are available in `example_cli_usage.py`:
```bash
python example_cli_usage.py
```

This demonstrates all CLI features with practical examples and use cases.

## 🎯 Best Practices

1. **Always use confirmation prompts** for destructive operations
2. **Test with dry-run mode** before batch operations
3. **Use appropriate generation modes** based on quality needs
4. **Monitor resource usage** during batch exports
5. **Keep courses organized** with consistent naming
6. **Use filters effectively** for large course collections
7. **Regular cleanup** of draft and archived courses
8. **Export backups** before major operations

## 🔄 Future Enhancements

- Course templates and presets
- Advanced search and filtering
- Course analytics and reporting
- Integration with external LMS systems
- Automated quality assurance workflows
- Course versioning and rollback
- Advanced batch scheduling
- REST API integration for remote operations