from django import forms
from .models import Presentation


class TopicForm(forms.ModelForm):
    """Form for topic selection"""
    
    topic = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'topic-input',
            'placeholder': 'Enter your presentation topic...',
            'autocomplete': 'off'
        }),
        label='',
        help_text='Enter a topic for your presentation (e.g., "Artificial Intelligence", "Climate Change", "Digital Marketing")'
    )
    
    class Meta:
        model = Presentation
        fields = ['topic']
    
    def clean_topic(self):
        """Validate and clean the topic field"""
        topic = self.cleaned_data.get('topic')
        
        if not topic or len(topic.strip()) < 3:
            raise forms.ValidationError('Topic must be at least 3 characters long')
        
        if len(topic) > 500:
            raise forms.ValidationError('Topic is too long (maximum 500 characters)')
        
        return topic.strip()
