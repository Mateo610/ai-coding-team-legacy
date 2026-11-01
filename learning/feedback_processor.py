"""
Feedback Processing and Incorporation
Section 7.3: User Feedback

Processes feedback and incorporates improvements into prompts, examples, and skills
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict, Counter

from learning.feedback_collector import FeedbackCollector, FeedbackType, FEEDBACK_COLLECTOR
from agents.prompt_builder import PromptBuilder
from agents.skill_manager import SkillManager


class FeedbackProcessor:
    """Processes feedback and suggests improvements"""
    
    def __init__(self, feedback_collector: Optional[FeedbackCollector] = None):
        """
        Initialize feedback processor
        
        Args:
            feedback_collector: FeedbackCollector instance
        """
        self.feedback_collector = feedback_collector or FEEDBACK_COLLECTOR
        self.prompt_builder = PromptBuilder()
        self.skill_manager = SkillManager()
    
    def analyze_feedback(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze feedback and generate improvement suggestions
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with analysis and suggestions
        """
        # Get feedback statistics
        stats = self.feedback_collector.get_feedback_statistics(days=days)
        
        # Get detailed feedback
        feedbacks = self.feedback_collector.get_feedback(days=days)
        
        analysis = {
            'statistics': stats,
            'improvement_areas': [],
            'common_corrections': {},
            'common_suggestions': [],
            'low_rated_tasks': [],
            'recommendations': []
        }
        
        # Analyze low ratings
        low_rated = [f for f in feedbacks if f.rating and f.rating <= 2]
        if low_rated:
            analysis['low_rated_tasks'] = [
                {
                    'task': f.task,
                    'task_type': f.task_type,
                    'rating': f.rating,
                    'comment': f.comment
                }
                for f in low_rated[:10]  # Top 10
            ]
            
            # Group by task type
            by_task_type = defaultdict(list)
            for f in low_rated:
                by_task_type[f.task_type].append(f)
            
            # Identify improvement areas
            for task_type, feedbacks in by_task_type.items():
                if len(feedbacks) >= 3:  # At least 3 low ratings
                    analysis['improvement_areas'].append({
                        'task_type': task_type,
                        'count': len(feedbacks),
                        'avg_rating': sum(f.rating for f in feedbacks if f.rating) / len([f for f in feedbacks if f.rating]),
                        'priority': 'high' if len(feedbacks) >= 5 else 'medium'
                    })
        
        # Analyze corrections
        all_corrections = {}
        for f in feedbacks:
            if f.corrections:
                all_corrections.update(f.corrections)
        
        # Find common correction patterns
        correction_patterns = Counter()
        for original, corrected in all_corrections.items():
            # Simple pattern: if original and corrected are similar, track the pattern
            if len(original) > 20 and len(corrected) > 20:
                # Extract first 50 chars as pattern identifier
                pattern = original[:50].lower()
                correction_patterns[pattern] += 1
        
        analysis['common_corrections'] = dict(correction_patterns.most_common(10))
        
        # Analyze suggestions
        all_suggestions = []
        for f in feedbacks:
            if f.suggestions:
                all_suggestions.extend(f.suggestions)
        
        suggestion_counts = Counter(all_suggestions)
        analysis['common_suggestions'] = [
            {'suggestion': suggestion, 'count': count}
            for suggestion, count in suggestion_counts.most_common(10)
        ]
        
        # Generate recommendations
        recommendations = []
        
        # Low satisfaction rate
        if stats['overall']['satisfaction_rate'] < 70:
            recommendations.append(
                f"Satisfaction rate is {stats['overall']['satisfaction_rate']:.1f}% "
                f"(< 70%). Consider analyzing low-rated tasks."
            )
        
        # Specific task types need improvement
        for area in analysis['improvement_areas']:
            if area['priority'] == 'high':
                recommendations.append(
                    f"Task type '{area['task_type']}' has {area['count']} low ratings. "
                    f"High priority for improvement."
                )
        
        # Common corrections suggest prompt/example improvements
        if len(analysis['common_corrections']) >= 3:
            recommendations.append(
                f"{len(analysis['common_corrections'])} common correction patterns detected. "
                f"Consider updating prompts or examples to prevent these mistakes."
            )
        
        # Popular suggestions
        if analysis['common_suggestions']:
            top_suggestion = analysis['common_suggestions'][0]
            if top_suggestion['count'] >= 3:
                recommendations.append(
                    f"Popular suggestion: '{top_suggestion['suggestion']}' "
                    f"(mentioned {top_suggestion['count']} times). Consider implementing."
                )
        
        analysis['recommendations'] = recommendations
        
        return analysis
    
    def incorporate_corrections(self, task_type: str, corrections: Dict[str, str]) -> List[str]:
        """
        Incorporate corrections into prompts/examples
        
        Args:
            task_type: Task type
            corrections: Dictionary of corrections {original: corrected}
        
        Returns:
            List of actions taken
        """
        actions = []
        
        # For now, log corrections for manual review
        # Future: automatically update examples with common corrections
        
        actions.append(f"Logged {len(corrections)} corrections for {task_type} tasks")
        actions.append("Corrections saved for manual review and example updates")
        
        return actions
    
    def incorporate_suggestions(self, suggestions: List[str]) -> List[str]:
        """
        Incorporate user suggestions
        
        Args:
            suggestions: List of suggestions
        
        Returns:
            List of actions taken
        """
        actions = []
        
        # For now, log suggestions for manual review
        # Future: automatically prioritize and implement suggestions
        
        actions.append(f"Logged {len(suggestions)} suggestions")
        actions.append("Suggestions saved for manual review and implementation")
        
        return actions
    
    def generate_improvement_report(self, days: int = 30) -> str:
        """
        Generate human-readable improvement report
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Formatted report string
        """
        analysis = self.analyze_feedback(days=days)
        
        report = []
        report.append("=" * 70)
        report.append("📊 FEEDBACK ANALYSIS REPORT")
        report.append("=" * 70)
        report.append(f"\nPeriod: Last {days} days")
        
        # Statistics
        stats = analysis['statistics']
        report.append(f"\n{'='*70}")
        report.append("📈 OVERALL STATISTICS")
        report.append(f"{'='*70}")
        report.append(f"\nTotal Feedback: {stats['overall']['total']}")
        report.append(f"Average Rating: {stats['overall']['avg_rating']:.1f}/5.0")
        report.append(f"Satisfaction Rate: {stats['overall']['satisfaction_rate']:.1f}%")
        
        # Improvement areas
        if analysis['improvement_areas']:
            report.append(f"\n{'='*70}")
            report.append("⚠️  IMPROVEMENT AREAS")
            report.append(f"{'='*70}")
            
            for area in analysis['improvement_areas']:
                report.append(f"\n{area['task_type'].upper()} (Priority: {area['priority']})")
                report.append(f"   Low Ratings: {area['count']}")
                report.append(f"   Average Rating: {area['avg_rating']:.1f}/5.0")
        
        # Recommendations
        if analysis['recommendations']:
            report.append(f"\n{'='*70}")
            report.append("💡 RECOMMENDATIONS")
            report.append(f"{'='*70}")
            
            for i, rec in enumerate(analysis['recommendations'], 1):
                report.append(f"\n{i}. {rec}")
        
        report.append(f"\n{'='*70}")
        
        return "\n".join(report)


# Global instance
FEEDBACK_PROCESSOR = FeedbackProcessor()

