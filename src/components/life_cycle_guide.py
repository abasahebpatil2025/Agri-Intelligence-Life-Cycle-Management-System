"""
Life Cycle Guide Component

Provides crop-specific guidance for different growth stages.
Includes practices, inputs, pest management, and irrigation advice.
Supports Marathi and English languages.

Requirements: 11.1, 11.2, 11.3, 11.4, 11.5
"""

import json
import os
from typing import List, Dict, Any, Optional


class LifeCycleGuide:
    """
    Life cycle guide for agricultural crops.
    
    Provides stage-specific guidance for crop management.
    Supports 5 crops and 5 growth stages with bilingual content.
    """
    
    # Supported crops
    CROPS = ['Onion', 'Tomato', 'Cotton', 'Tur', 'Soybean']
    
    # Growth stages
    STAGES = ['Sowing', 'Vegetative', 'Flowering', 'Maturity', 'Harvest']
    
    def __init__(self, data_file: Optional[str] = None):
        """
        Initialize Life Cycle Guide.
        
        Args:
            data_file: Optional path to crop guidance JSON file
        """
        if data_file is None:
            # Default to data/crop_guidance.json
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            data_file = os.path.join(project_root, 'data', 'crop_guidance.json')
        
        self.data_file = data_file
        self.guidance_data = self._load_guidance_data()
    
    def _load_guidance_data(self) -> Dict[str, Any]:
        """
        Load crop guidance data from JSON file.
        
        Returns:
            Dictionary with crop guidance data
        """
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return empty dict if file not found
            return {}
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in guidance file: {e}")
    
    def get_crops(self) -> List[str]:
        """
        Get list of supported crops.
        
        Returns:
            List of crop names
        """
        return self.CROPS.copy()
    
    def get_stages(self) -> List[str]:
        """
        Get list of growth stages.
        
        Returns:
            List of stage names
        """
        return self.STAGES.copy()
    
    def get_guidance(
        self,
        crop: str,
        stage: str,
        language: str = 'marathi'
    ) -> Dict[str, Any]:
        """
        Get guidance for specific crop and stage.
        
        Args:
            crop: Crop name (e.g., 'Onion', 'Tomato')
            stage: Growth stage (e.g., 'Sowing', 'Vegetative')
            language: Language preference ('marathi' or 'english')
            
        Returns:
            Dictionary with guidance information:
            - practices: Farming practices
            - inputs: Required inputs (fertilizers, seeds)
            - timeline_days: Duration in days
            - pest_mgmt: Pest management advice
            - irrigation: Irrigation recommendations
        """
        if crop not in self.guidance_data:
            raise ValueError(f"Crop '{crop}' not found. Available crops: {', '.join(self.CROPS)}")
        
        if stage not in self.guidance_data[crop]:
            raise ValueError(f"Stage '{stage}' not found for crop '{crop}'. Available stages: {', '.join(self.STAGES)}")
        
        stage_data = self.guidance_data[crop][stage].copy()
        
        # Return appropriate language version
        if language.lower() == 'english':
            # Use English fields
            return {
                'practices': stage_data.get('practices_en', stage_data.get('practices', '')),
                'inputs': stage_data.get('inputs_en', stage_data.get('inputs', '')),
                'timeline_days': stage_data.get('timeline_days', 0),
                'pest_mgmt': stage_data.get('pest_mgmt_en', stage_data.get('pest_mgmt', '')),
                'irrigation': stage_data.get('irrigation_en', stage_data.get('irrigation', ''))
            }
        else:
            # Use Marathi fields (default)
            return {
                'practices': stage_data.get('practices', ''),
                'inputs': stage_data.get('inputs', ''),
                'timeline_days': stage_data.get('timeline_days', 0),
                'pest_mgmt': stage_data.get('pest_mgmt', ''),
                'irrigation': stage_data.get('irrigation', '')
            }
    
    def get_full_lifecycle(
        self,
        crop: str,
        language: str = 'marathi'
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get complete lifecycle guidance for a crop.
        
        Args:
            crop: Crop name
            language: Language preference ('marathi' or 'english')
            
        Returns:
            Dictionary with all stages and their guidance
        """
        if crop not in self.guidance_data:
            raise ValueError(f"Crop '{crop}' not found")
        
        lifecycle = {}
        for stage in self.STAGES:
            lifecycle[stage] = self.get_guidance(crop, stage, language)
        
        return lifecycle
    
    def get_total_duration(self, crop: str) -> int:
        """
        Get total crop duration in days.
        
        Args:
            crop: Crop name
            
        Returns:
            Total duration in days
        """
        if crop not in self.guidance_data:
            raise ValueError(f"Crop '{crop}' not found")
        
        total_days = 0
        for stage in self.STAGES:
            stage_data = self.guidance_data[crop][stage]
            total_days += stage_data.get('timeline_days', 0)
        
        return total_days
    
    def search_guidance(
        self,
        keyword: str,
        language: str = 'marathi'
    ) -> List[Dict[str, Any]]:
        """
        Search for guidance containing keyword.
        
        Args:
            keyword: Search keyword
            language: Language preference
            
        Returns:
            List of matching guidance entries with crop and stage info
        """
        results = []
        keyword_lower = keyword.lower()
        
        for crop in self.CROPS:
            for stage in self.STAGES:
                try:
                    guidance = self.get_guidance(crop, stage, language)
                    
                    # Search in all fields
                    found = False
                    for field_value in guidance.values():
                        if isinstance(field_value, str) and keyword_lower in field_value.lower():
                            found = True
                            break
                    
                    if found:
                        results.append({
                            'crop': crop,
                            'stage': stage,
                            'guidance': guidance
                        })
                except ValueError:
                    continue
        
        return results
    
    def get_stage_summary(
        self,
        crop: str,
        stage: str,
        language: str = 'marathi'
    ) -> str:
        """
        Get formatted summary of stage guidance.
        
        Args:
            crop: Crop name
            stage: Growth stage
            language: Language preference
            
        Returns:
            Formatted summary string
        """
        guidance = self.get_guidance(crop, stage, language)
        
        if language.lower() == 'english':
            summary = f"**{crop} - {stage} Stage ({guidance['timeline_days']} days)**\n\n"
            summary += f"**Practices:** {guidance['practices']}\n\n"
            summary += f"**Inputs:** {guidance['inputs']}\n\n"
            summary += f"**Pest Management:** {guidance['pest_mgmt']}\n\n"
            summary += f"**Irrigation:** {guidance['irrigation']}"
        else:
            summary = f"**{crop} - {stage} टप्पा ({guidance['timeline_days']} दिवस)**\n\n"
            summary += f"**मशागत:** {guidance['practices']}\n\n"
            summary += f"**खते/औषधे:** {guidance['inputs']}\n\n"
            summary += f"**कीड व्यवस्थापन:** {guidance['pest_mgmt']}\n\n"
            summary += f"**पाणी व्यवस्थापन:** {guidance['irrigation']}"
        
        return summary
    
    def validate_data(self) -> Dict[str, Any]:
        """
        Validate loaded guidance data.
        
        Returns:
            Dictionary with validation results
        """
        issues = []
        
        # Check all crops are present
        for crop in self.CROPS:
            if crop not in self.guidance_data:
                issues.append(f"Missing crop: {crop}")
                continue
            
            # Check all stages are present
            for stage in self.STAGES:
                if stage not in self.guidance_data[crop]:
                    issues.append(f"Missing stage '{stage}' for crop '{crop}'")
                    continue
                
                stage_data = self.guidance_data[crop][stage]
                
                # Check required fields
                required_fields = ['practices', 'inputs', 'timeline_days', 'pest_mgmt', 'irrigation']
                for field in required_fields:
                    if field not in stage_data:
                        issues.append(f"Missing field '{field}' in {crop}/{stage}")
                
                # Check English translations
                english_fields = ['practices_en', 'inputs_en', 'pest_mgmt_en', 'irrigation_en']
                for field in english_fields:
                    if field not in stage_data:
                        issues.append(f"Missing English field '{field}' in {crop}/{stage}")
        
        return {
            'valid': len(issues) == 0,
            'total_crops': len(self.CROPS),
            'total_stages': len(self.STAGES),
            'issues': issues
        }
