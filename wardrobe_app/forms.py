from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import ClothingItem, Outfit, ClothingCategory, UserProfile
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import re

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ("email",)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email

class AdminRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ("email",)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email

class UserLoginForm(AuthenticationForm):
    pass

class AdminLoginForm(AuthenticationForm):
    pass

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['preferred_colors', 'preferred_occasions']

    def clean_preferred_colors(self):
        colors = self.cleaned_data.get('preferred_colors')
        if colors and len(colors) > 255:
            raise forms.ValidationError("Preferred colors list is too long.")
        return colors

    def clean_preferred_occasions(self):
        occasions = self.cleaned_data.get('preferred_occasions')
        if occasions and len(occasions) > 255:
            raise forms.ValidationError("Preferred occasions list is too long.")
        return occasions

class ClothingItemForm(forms.ModelForm):
    occasions = forms.ChoiceField(
        choices=ClothingItem.OCCASION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        required=False
    )

    brand = forms.ChoiceField(
        choices=[],  # Choices will be populated in __init__
        widget=forms.Select(attrs={
            'class': 'form-control',
            'placeholder': 'Select brand'
        }),
        required=False
    )

    color = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'type': 'color',
            'placeholder': 'Select color'
        }),
        required=False
    )

    class Meta:
        model = ClothingItem
        fields = [
            'name', 'category', 'color', 'season', 'fit',
            'fabric_type', 'occasions', 'image', 'notes',
            'purchase_date', 'brand', 'color_palette', 'style_embedding', 'features'
        ]
        
        labels = {
            'color_palette': 'Color Palette',
            'style_embedding': 'Style Embedding',
            'features': 'Features',
        }
        help_texts = {
            'color_palette': 'Enter color palette',
            'style_embedding': 'Enter style embedding',
            'features': 'Enter features',
        }
        
        widgets = {
            'color_palette': forms.Textarea(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Enter color palette',
                'required': False
            }),
            'style_embedding': forms.Textarea(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Enter style embedding',
                'required': False
            }),
            'features': forms.Textarea(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Enter features',
                'required': False
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Enter item name'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'color': forms.TextInput(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Enter color'
            }),
            'season': forms.Select(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'fit': forms.Select(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'fabric_type': forms.TextInput(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Enter fabric type'
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'accept': 'image/*'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Add any notes about this item'
            }),
            'purchase_date': forms.DateInput(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'type': 'date'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make sure we have all categories available
        self.fields['category'].empty_label = "Select a category"
        self.fields['category'].required = True
        
        # Add descriptions to category choices
        categories = ClothingCategory.objects.all()
        self.fields['category'].choices = [(c.id, f"{c.get_name_display()} - {c.description}") for c in categories]
        
        # Set initial value for occasions if editing existing item
        if self.instance.pk and self.instance.occasions:
            if isinstance(self.instance.occasions, list) and self.instance.occasions:
                self.initial['occasions'] = self.instance.occasions[0]
            else:
                self.initial['occasions'] = self.instance.occasions

        # Get unique brands from existing items
        brands = ClothingItem.objects.exclude(brand__isnull=True).exclude(brand='').values_list('brand', flat=True).distinct().order_by('brand')
        
        # Add a list of well-known fashion brands
        well_known_brands = [
            "Gucci", "Prada", "Chanel", "Louis Vuitton", "Dior",
            "Hermès", "Versace", "Armani", "Burberry", "Ralph Lauren",
            "Calvin Klein", "Dolce & Gabbana", "Fendi", "Valentino", "Givenchy",
            "Saint Laurent", "Balenciaga", "Tom Ford", "Alexander McQueen", "Bottega Veneta",
            "Celine", "Chloé", "Miu Miu", "Balmain", "Moncler",
            "Off-White", "Zara", "H&M", "Adidas", "Nike",
            "Puma", "Levi's", "Uniqlo", "Gap", "Old Navy",
            "Forever 21", "ASOS", "Mango", "Topshop", "River Island",
            "Miss Selfridge", "New Look", "Primark", "Shein", "Boohoo",
            "PrettyLittleThing", "Michael Kors", "Kate Spade", "Tory Burch", "Coach",
            "Marc Jacobs", "DKNY", "Alexander Wang", "Stella McCartney", "Vivienne Westwood",
            "Comme des Garçons", "Yohji Yamamoto", "Issey Miyake", "Kenzo", "Dries Van Noten",
            "Ann Demeulemeester", "Maison Margiela", "Rick Owens", "Undercover", "Sacai",
            "Acne Studios", "APC", "Opening Ceremony", "Rag & Bone", "Theory",
            "Vince", "Equipment", "Frame", "Citizens of Humanity", "J Brand",
            "AG Jeans", "Supreme", "Stone Island", "Patagonia", "The North Face"
        ]
        brand_choices = [('', 'Select a brand')] + [(brand, brand) for brand in brands] + [(brand, brand) for brand in well_known_brands] + [('other', 'Other')]
        self.fields['brand'].choices = sorted(list(dict.fromkeys(brand_choices)), key=lambda x: x[1])
        
        # To implement the "Other" option, you'll need to add JavaScript to show/hide a text input field when "Other" is selected.
        # The text input field should be initially hidden.
        # When the user selects "Other", the text input field should become visible, allowing them to enter the brand name manually.

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set default values for required fields if they're not set
        if not instance.style_embedding:
            instance.style_embedding = {}
        if not instance.color_palette:
            instance.color_palette = []
        if not instance.features:
            instance.features = {}
            
        if commit:
            instance.save()
        return instance

class OutfitForm(forms.ModelForm):
    """Form for creating and updating outfits."""

    class Meta:
        model = Outfit
        fields = ['name', 'items', 'suggested_temperature_min', 'suggested_temperature_max', 'template_category', 'compatibility_score', 'description', 'tags']
        widgets = {
            'suggested_temperature_min': forms.NumberInput(attrs={'step': '0.1'}),
            'suggested_temperature_max': forms.NumberInput(attrs={'step': '0.1'}),
            'compatibility_score': forms.NumberInput(attrs={'step': '0.01'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
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
        self.fields['compatibility_score'].required = False
        self.fields['template_category'].required = False
        self.fields['description'].required = False
        
        # Add validators
        self.fields['suggested_temperature_min'].validators = [
            MinValueValidator(-50, message="Temperature cannot be below -50°C."),
            MaxValueValidator(50, message="Temperature cannot be above 50°C.")
        ]
        self.fields['suggested_temperature_max'].validators = [
            MinValueValidator(-50, message="Temperature cannot be below -50°C."),
            MaxValueValidator(50, message="Temperature cannot be above 50°C.")
        ]
        self.fields['compatibility_score'].validators = [
            MinValueValidator(0, message="Score cannot be negative."),
            MaxValueValidator(100, message="Score cannot be above 100.")
        ]

        # Add help text
        self.fields['suggested_temperature_min'].help_text = 'Minimum temperature in °C'
        self.fields['suggested_temperature_max'].help_text = 'Maximum temperature in °C'
        self.fields['compatibility_score'].widget = forms.HiddenInput()
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("Name is required.")
        elif len(name) > 100:
            raise forms.ValidationError("Name must be less than 100 characters.")
        return name
    
    def clean_description(self):
        description = self.cleaned_data.get('description', '')
        if description and len(description) > 1000:
            raise forms.ValidationError("Description must be less than 1000 characters.")
        return description
    
    def clean_tags(self):
        tags = self.cleaned_data.get('tags', [])
        if tags:
            if not isinstance(tags, list):
                raise forms.ValidationError("Tags must be a list.")
            if len(tags) > 20:
                raise forms.ValidationError("Maximum of 20 tags allowed.")
            for tag in tags:
                if not isinstance(tag, str):
                    raise forms.ValidationError("Tags must be strings.")
                if len(tag) > 50:
                    raise forms.ValidationError(f"Tag '{tag}' is too long (maximum 50 characters).")
        return tags
    
    def clean(self):
        cleaned_data = super().clean()
        min_temp = cleaned_data.get('suggested_temperature_min')
        max_temp = cleaned_data.get('suggested_temperature_max')
        
        # Validate temperature range if both are provided
        if min_temp is not None and max_temp is not None:
            if min_temp > max_temp:
                self.add_error('suggested_temperature_min', 
                               'Minimum temperature cannot be greater than maximum temperature.')
                self.add_error('suggested_temperature_max', 
                               'Maximum temperature cannot be less than minimum temperature.')
        
        # Validate items are selected
        items = cleaned_data.get('items')
        if not items or items.count() == 0:
            self.add_error('items', 'At least one clothing item must be selected.')
        
        return cleaned_data


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
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("Category name is required.")
        return name
    
    def clean_description(self):
        description = self.cleaned_data.get('description', '')
        if description and len(description) > 500:
            raise forms.ValidationError("Description must be less than 500 characters.")
        return description
