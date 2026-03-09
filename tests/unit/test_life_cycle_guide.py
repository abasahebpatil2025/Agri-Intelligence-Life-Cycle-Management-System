"""
Unit tests for Life Cycle Guide Component

Tests crop guidance retrieval, bilingual support, and data validation.
Property-based tests for guidance completeness.
"""

import pytest
from hypothesis import given, strategies as st, settings

# Import the component
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'components'))
from life_cycle_guide import LifeCycleGuide


class TestLifeCycleGuide:
    """Test suite for LifeCycleGuide component"""
    
    def test_initialization(self):
        """Test guide initialization"""
        guide = LifeCycleGuide()
        
        assert guide is not None
        assert len(guide.CROPS) == 5
        assert len(guide.STAGES) == 5
    
    def test_get_crops(self):
        """Test getting list of crops"""
        guide = LifeCycleGuide()
        
        crops = guide.get_crops()
        
        assert len(crops) == 5
        assert 'Onion' in crops
        assert 'Tomato' in crops
        assert 'Cotton' in crops
        assert 'Tur' in crops
        assert 'Soybean' in crops
    
    def test_get_stages(self):
        """Test getting list of stages"""
        guide = LifeCycleGuide()
        
        stages = guide.get_stages()
        
        assert len(stages) == 5
        assert 'Sowing' in stages
        assert 'Vegetative' in stages
        assert 'Flowering' in stages
        assert 'Maturity' in stages
        assert 'Harvest' in stages
    
    def test_get_guidance_marathi(self):
        """Test getting guidance in Marathi"""
        guide = LifeCycleGuide()
        
        guidance = guide.get_guidance('Onion', 'Sowing', language='marathi')
        
        assert 'practices' in guidance
        assert 'inputs' in guidance
        assert 'timeline_days' in guidance
        assert 'pest_mgmt' in guidance
        assert 'irrigation' in guidance
        
        # Verify Marathi content
        assert any(ord(char) >= 0x0900 and ord(char) <= 0x097F for char in guidance['practices'])
    
    def test_get_guidance_english(self):
        """Test getting guidance in English"""
        guide = LifeCycleGuide()
        
        guidance = guide.get_guidance('Onion', 'Sowing', language='english')
        
        assert 'practices' in guidance
        assert 'inputs' in guidance
        assert 'timeline_days' in guidance
        assert 'pest_mgmt' in guidance
        assert 'irrigation' in guidance
        
        # Verify English content (no Devanagari characters)
        has_devanagari = any(ord(char) >= 0x0900 and ord(char) <= 0x097F for char in guidance['practices'])
        assert not has_devanagari
    
    def test_get_guidance_invalid_crop(self):
        """Test getting guidance for invalid crop"""
        guide = LifeCycleGuide()
        
        with pytest.raises(ValueError, match="Crop .* not found"):
            guide.get_guidance('InvalidCrop', 'Sowing')
    
    def test_get_guidance_invalid_stage(self):
        """Test getting guidance for invalid stage"""
        guide = LifeCycleGuide()
        
        with pytest.raises(ValueError, match="Stage .* not found"):
            guide.get_guidance('Onion', 'InvalidStage')
    
    def test_get_full_lifecycle(self):
        """Test getting full lifecycle for a crop"""
        guide = LifeCycleGuide()
        
        lifecycle = guide.get_full_lifecycle('Onion', language='marathi')
        
        assert len(lifecycle) == 5
        assert 'Sowing' in lifecycle
        assert 'Vegetative' in lifecycle
        assert 'Flowering' in lifecycle
        assert 'Maturity' in lifecycle
        assert 'Harvest' in lifecycle
        
        # Verify each stage has required fields
        for stage, guidance in lifecycle.items():
            assert 'practices' in guidance
            assert 'timeline_days' in guidance
    
    def test_get_total_duration(self):
        """Test getting total crop duration"""
        guide = LifeCycleGuide()
        
        duration = guide.get_total_duration('Onion')
        
        assert duration > 0
        assert isinstance(duration, int)
        # Onion typically takes 130 days (30+40+30+20+10)
        assert duration == 130
    
    def test_get_total_duration_invalid_crop(self):
        """Test getting duration for invalid crop"""
        guide = LifeCycleGuide()
        
        with pytest.raises(ValueError, match="Crop .* not found"):
            guide.get_total_duration('InvalidCrop')
    
    def test_search_guidance(self):
        """Test searching guidance by keyword"""
        guide = LifeCycleGuide()
        
        # Search for 'बियाणे' (seed in Marathi)
        results = guide.search_guidance('बियाणे', language='marathi')
        
        assert len(results) > 0
        assert all('crop' in r and 'stage' in r and 'guidance' in r for r in results)
    
    def test_search_guidance_english(self):
        """Test searching guidance in English"""
        guide = LifeCycleGuide()
        
        results = guide.search_guidance('seed', language='english')
        
        assert len(results) > 0
    
    def test_search_guidance_no_results(self):
        """Test searching with keyword that has no matches"""
        guide = LifeCycleGuide()
        
        results = guide.search_guidance('xyz123notfound')
        
        assert len(results) == 0
    
    def test_get_stage_summary_marathi(self):
        """Test getting formatted stage summary in Marathi"""
        guide = LifeCycleGuide()
        
        summary = guide.get_stage_summary('Onion', 'Sowing', language='marathi')
        
        assert isinstance(summary, str)
        assert 'Onion' in summary
        assert 'Sowing' in summary or 'टप्पा' in summary
        assert 'मशागत' in summary
        assert 'दिवस' in summary
    
    def test_get_stage_summary_english(self):
        """Test getting formatted stage summary in English"""
        guide = LifeCycleGuide()
        
        summary = guide.get_stage_summary('Onion', 'Sowing', language='english')
        
        assert isinstance(summary, str)
        assert 'Onion' in summary
        assert 'Sowing' in summary
        assert 'Practices' in summary
        assert 'days' in summary
    
    def test_validate_data(self):
        """Test data validation"""
        guide = LifeCycleGuide()
        
        validation = guide.validate_data()
        
        assert 'valid' in validation
        assert 'total_crops' in validation
        assert 'total_stages' in validation
        assert 'issues' in validation
        
        # Should be valid if data file is properly loaded
        if validation['valid']:
            assert len(validation['issues']) == 0
    
    def test_all_crops_have_all_stages(self):
        """Test that all crops have all stages defined"""
        guide = LifeCycleGuide()
        
        for crop in guide.CROPS:
            for stage in guide.STAGES:
                # Should not raise exception
                guidance = guide.get_guidance(crop, stage)
                assert guidance is not None
    
    def test_timeline_days_positive(self):
        """Test that all timeline_days are positive"""
        guide = LifeCycleGuide()
        
        for crop in guide.CROPS:
            for stage in guide.STAGES:
                guidance = guide.get_guidance(crop, stage)
                assert guidance['timeline_days'] > 0


# Property-Based Tests
class TestLifeCycleGuideProperties:
    """Property-based tests for Life Cycle Guide"""
    
    @settings(deadline=None, max_examples=10)
    @given(
        crop=st.sampled_from(['Onion', 'Tomato', 'Cotton', 'Tur', 'Soybean']),
        stage=st.sampled_from(['Sowing', 'Vegetative', 'Flowering', 'Maturity', 'Harvest'])
    )
    def test_property_guidance_completeness(self, crop, stage):
        """
        Property 22: Life Cycle Guidance Completeness
        
        GIVEN any crop and stage combination
        WHEN guidance is retrieved
        THEN all required fields are present
        
        Validates: Requirements 11.4, 11.5
        """
        guide = LifeCycleGuide()
        
        guidance = guide.get_guidance(crop, stage)
        
        # Verify all required fields are present
        required_fields = ['practices', 'inputs', 'timeline_days', 'pest_mgmt', 'irrigation']
        for field in required_fields:
            assert field in guidance
            
            # Verify non-empty values
            if field == 'timeline_days':
                assert guidance[field] > 0
            else:
                assert len(guidance[field]) > 0
    
    @settings(deadline=None, max_examples=10)
    @given(
        crop=st.sampled_from(['Onion', 'Tomato', 'Cotton', 'Tur', 'Soybean']),
        stage=st.sampled_from(['Sowing', 'Vegetative', 'Flowering', 'Maturity', 'Harvest'])
    )
    def test_property_bilingual_support(self, crop, stage):
        """
        Property: Bilingual Support
        
        GIVEN any crop and stage
        WHEN guidance is retrieved in both languages
        THEN both Marathi and English versions are available
        
        Validates: Requirement 11.3
        """
        guide = LifeCycleGuide()
        
        marathi_guidance = guide.get_guidance(crop, stage, language='marathi')
        english_guidance = guide.get_guidance(crop, stage, language='english')
        
        # Both should have same structure
        assert marathi_guidance.keys() == english_guidance.keys()
        
        # Timeline should be same in both languages
        assert marathi_guidance['timeline_days'] == english_guidance['timeline_days']
        
        # Content should be different (different languages)
        assert marathi_guidance['practices'] != english_guidance['practices']
