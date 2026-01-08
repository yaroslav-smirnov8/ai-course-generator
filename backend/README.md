# Enhanced JSON Handler for Language Model APIs

## Project Overview

This project is an enhanced JSON handler for processing responses from language model APIs (Gemini, Mistral, Claude, etc.) when generating language courses. The handler is capable of processing various data formats, fixing JSON errors, and converting results to a unified structure.

## Key Features

- Processing various JSON formats from language model APIs
- Extracting course structure from incomplete or corrupted responses
- Standardizing data format for use in the application
- Detailed logging for debugging and monitoring
- Recovering data from truncated API responses

## Supported Data Formats

1. **Standard course format** - with fields `name`, `description` and array `lessons`
2. **Individual lesson** - object with field `title` and others
3. **Array of lessons** - list of objects with fields `title` and others
4. **"lesson X" format** - object with keys like "lesson 1", "lesson 2", etc.

## Project Structure

- `app/services/content/json_extractor.py` - main handler module
- `content_generator/course_generator.py` - course generation module using the handler
- `demo_json_extractor.py` - demonstration script for testing the handler
- `test_course_generator.py` - testing course generator with enhanced handler
- `README_json_extractor.md` - detailed documentation for JSON handler

## Installation and Setup

### Database Creation

The PostgreSQL database will be automatically created with the correct UTF8 encoding on the first application run. The `create_database_if_not_exists()` function in `app/core/database.py` will automatically:
- Check for database existence
- Create the database with UTF8 encoding if it doesn't exist
- Configure proper localization parameters

### Environment Variables Setup

Make sure the correct database password is specified in the `.env` file:

```
DATABASE_URL=postgresql://postgres:P8j#Kq2@vL7xZs9$Rt5!@localhost:5432/pldb
```

## Usage

### Basic Usage

```python
from app.services.content.json_extractor import extract_course_from_api_response

# Get response from API
api_response = "...API response..."

# Process response and get course structure
course_data = extract_course_from_api_response(api_response, debug=True)

# Use the retrieved data
print(f"Course name: {course_data.get('name')}")
print(f"Number of lessons: {len(course_data.get('lessons', []))}")
```

### Running the Demonstration

```bash
# Demonstration of processing various JSON formats
python demo_json_extractor.py

# Testing course generator with enhanced handler
python test_course_generator.py
```

## Integration with Existing Systems

The handler is integrated with the `CourseGenerator` class, which is used for generating language courses. The `_process_course_response` method has been updated to use the enhanced handler.

## Additional Information

More detailed information can be found in the `README_json_extractor.md` file, which contains a detailed description of the handler's operation, usage examples, and solutions to possible problems. 