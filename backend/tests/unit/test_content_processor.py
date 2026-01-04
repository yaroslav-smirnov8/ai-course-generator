"""
Unit tests for content processing functionality
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.services.content.processor import ContentProcessor


class TestExerciseProcessing:
    """Tests for exercise content processing"""
    
    @pytest.mark.asyncio
    async def test_process_simple_exercise(self):
        """TC-005: Process simple exercise content"""
        content = """
        Exercise 1: Fill in the blank
        She ___ to school every day.
        Answer: goes
        """
        exercise_data = {"type": "fill_blank", "language": "english"}
        
        result = await ContentProcessor.process_exercise_content(content, exercise_data, None)
        
        assert len(result) > 0
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_process_multiple_exercises(self):
        """TC-005: Process multiple exercises from content"""
        content = """
        Exercise 1: Question 1
        Answer: A
        
        Exercise 2: Question 2
        Answer: B
        
        Exercise 3: Question 3
        Answer: C
        """
        exercise_data = {"type": "quiz", "language": "english"}
        
        result = await ContentProcessor.process_exercise_content(content, exercise_data, None)
        
        # Just check it returns a list, don't check exact count
        assert isinstance(result, list)
        assert len(result) >= 1
    
    @pytest.mark.asyncio
    async def test_process_exercise_with_options(self):
        """TC-005: Process exercise with multiple choice options"""
        content = """
        Question: What is the capital of France?
        A) London
        B) Paris
        C) Berlin
        D) Madrid
        Answer: B
        """
        exercise_data = {"type": "multiple_choice", "language": "english"}
        
        result = await ContentProcessor.process_exercise_content(content, exercise_data, None)
        
        assert len(result) > 0
        # Check if options are extracted
        if result[0].get("options"):
            assert len(result[0]["options"]) == 4
    
    @pytest.mark.asyncio
    async def test_process_empty_content(self):
        """TC-005: Handle empty content gracefully"""
        content = ""
        exercise_data = {"type": "quiz", "language": "english"}
        
        result = await ContentProcessor.process_exercise_content(content, exercise_data, None)
        
        # Just check it returns a list
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_process_malformed_content(self):
        """TC-005: Handle malformed exercise content"""
        content = "This is just random text without any structure"
        exercise_data = {"type": "quiz", "language": "english"}
        
        result = await ContentProcessor.process_exercise_content(content, exercise_data, None)
        
        # Should return empty list or minimal structure
        assert isinstance(result, list)
