"""
Unit tests for JSON extraction and fixing functionality
"""
import pytest
import json
import sys
import os

# Add tests directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from improved_json_extractor import (
    fix_json_brackets,
    extract_json_object,
    process_truncated_json
)


class TestJSONBracketFix:
    """Tests for bracket balancing functionality"""
    
    def test_fix_missing_closing_brace(self):
        """Fix JSON with missing closing brace"""
        json_str = '{"name": "test", "value": 123'
        result = fix_json_brackets(json_str)
        assert result.count('{') == result.count('}')
        assert json.loads(result) == {"name": "test", "value": 123}
    
    def test_already_balanced_json(self):
        """Don't modify already balanced JSON"""
        json_str = '{"name": "test", "items": [1, 2, 3]}'
        result = fix_json_brackets(json_str)
        assert result == json_str
    
    def test_count_brackets(self):
        """Count brackets correctly"""
        json_str = '{"a": {"b": {"c": 1}}}'
        result = fix_json_brackets(json_str)
        assert result.count('{') == result.count('}')


class TestJSONExtraction:
    """Tests for JSON extraction from text"""
    
    def test_extract_incomplete_json(self):
        """Handle incomplete JSON"""
        text = '{"name": "test", "items": [1, 2, 3'
        result, is_complete = extract_json_object(text)
        assert not is_complete
        assert result.startswith('{')
    
    def test_no_json_in_text(self):
        """Handle text without JSON"""
        text = 'This is just plain text without any JSON'
        result, is_complete = extract_json_object(text)
        assert not is_complete
        assert result == text
    
    def test_extract_json_with_strings_containing_braces(self):
        """Handle JSON with braces in string values"""
        text = '{"message": "Use {variable} in text", "count": 5}'
        result, is_complete = extract_json_object(text)
        assert is_complete
        parsed = json.loads(result)
        assert "{variable}" in parsed["message"]


class TestTruncatedJSON:
    """Tests for truncated JSON processing"""
    
    def test_process_empty_input(self):
        """Handle empty input"""
        result = process_truncated_json("", debug=True)
        assert result is None
    
    def test_process_non_json_text(self):
        """Handle non-JSON text"""
        text = "This is not JSON at all"
        result = process_truncated_json(text, debug=True)
        assert result is None
    
    def test_process_valid_json(self):
        """Process valid JSON"""
        text = '{"name": "test", "value": 123}'
        result = process_truncated_json(text, debug=True)
        assert result is not None
        assert isinstance(result, dict)


class TestCourseExtraction:
    """Tests for course structure extraction"""
    
    def test_extract_complete_course(self):
        """Extract complete course structure"""
        json_text = '''
        {
            "name": "English Grammar Basics",
            "description": "Introduction to English grammar",
            "lessons": [
                {
                    "title": "Present Simple",
                    "description": "Learn present simple tense",
                    "activities": []
                }
            ]
        }
        '''
        result = process_truncated_json(json_text, debug=True)
        assert result is not None
        assert result["name"] == "English Grammar Basics"
        # Just check lessons field exists
        assert "lessons" in result
    
    def test_extract_course_with_missing_fields(self):
        """Handle course with missing optional fields"""
        json_text = '{"name": "Test Course", "lessons": []}'
        result = process_truncated_json(json_text, debug=True)
        assert result is not None
        assert result["name"] == "Test Course"
    
    def test_extract_truncated_course(self):
        """Extract data from truncated course JSON"""
        json_text = '{"name": "Incomplete Course", "description": "This JSON is cut off"'
        result = process_truncated_json(json_text, debug=True)
        # Should at least extract something
        assert result is not None


class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""
    
    def test_very_large_json(self):
        """Handle very large JSON structures"""
        large_json = '{"items": [' + ','.join([f'{{"id": {i}}}' for i in range(100)]) + ']}'
        result, is_complete = extract_json_object(large_json)
        assert is_complete
        parsed = json.loads(result)
        assert len(parsed["items"]) == 100
    
    def test_simple_object(self):
        """Handle simple JSON object"""
        json_str = '{"name": "test", "lessons": []}'
        result = process_truncated_json(json_str)
        assert result is not None
    
    def test_empty_object(self):
        """Handle empty JSON object"""
        json_str = '{}'
        result = process_truncated_json(json_str)
        assert result is not None
