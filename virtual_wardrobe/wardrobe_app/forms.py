from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField()

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ("email",)

class AdminRegistrationForm(UserCreationForm):
    email = forms.EmailField()

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ("email",)

class UserLoginForm(AuthenticationForm):
    pass

class AdminLoginForm(AuthenticationForm):
    pass
from .models import ClothingItem, ClothingCategory, Outfit

class ClothingItemForm(forms.ModelForm):
    """Form for creating and updating clothing items."""
    
    class Meta:
        model = ClothingItem
        fields = [
            'name', 'category', 'color', 'season', 'occasions',
            'image', 'purchase_date', 'brand', 'notes'
        ]
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'occasions': forms.CheckboxSelectMultiple(),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make some fields optional
        self.fields['purchase_date'].required = False
        self.fields['brand'].required = False
        self.fields['notes'].required = False
        self.fields['image'].required = False
        
        # Convert occasions from JSONField to multiple choice field
        OCCASION_CHOICES = [
            ('casual', 'Casual'),
            ('work', 'Work'),
            ('formal', 'Formal'),
            ('sports', 'Sports'),
            ('party', 'Party'),
        ]
        self.fields['occasions'] = forms.MultipleChoiceField(
            choices=OCCASION_CHOICES,
            required=False,
            widget=forms.CheckboxSelectMultiple()
        )
        
        # If we're editing an existing item, set initial values for occasions
        if self.instance.pk and self.instance.occasions:
            self.fields['occasions'].initial = self.instance.occasions
    
    def save(self, commit=True):
        item = super().save(commit=False)
        # Convert occasions from form data to JSON-serializable list
        item.occasions = self.cleaned_data.get('occasions', [])
        if commit:
            item.save()
        return item


class OutfitForm(forms.ModelForm):
    """Form for creating and updating outfits."""
    
    class Meta:
        model = Outfit
        fields = ['name', 'items', 'suggested_temperature_min', 'suggested_temperature_max']
        widgets = {
            'suggested_temperature_min': forms.NumberInput(attrs={'step': '0.1'}),
            'suggested_temperature_max': forms.NumberInput(attrs={'step': '0.1'}),
        }
    
    def __init__(self, *args, **kwargs):
        # Get the user to filter clothing items
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Only show the user's clothing items
            self.fields['items'].queryset = ClothingItem.objects.filter(user=user)
        
        # Make temperature fields optional
        self.fields['suggested_temperature_min'].required = False
        self.fields['suggested_temperature_max'].required = False
        
        # Add help text
        self.fields['suggested_temperature_min'].help_text = 'Minimum temperature in °C'
        self.fields['suggested_temperature_max'].help_text = 'Maximum temperature in °C'


class CategoryForm(forms.ModelForm):
    """Form for creating and updating clothing categories."""
    
    class Meta:
        model = ClothingCategory
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make description optional
        self.fields['description'].required = False
