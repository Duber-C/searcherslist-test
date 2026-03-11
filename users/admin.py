from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from .otp_models import OTP
from .models import Question, Signed_links, OTPVerification

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin interface for the extended User model
    """
    # Fields to display in the user list
    list_display = [
        'username', 'email', 'first_name', 'last_name', 
        'phone_number', 'country', 'city', 'current_role', 'company', 'acquisition_target', 
        'target_statement', 'profile_completed', 'published', 'public_token', 'is_staff', 'created_at', 'token_create_at'
    ]
    
    # Fields to filter by
    list_filter = [
        'is_staff', 'is_superuser', 'is_active', 'profile_completed',
        'published', 'country', 'state', 'created_at'
    ]
    
    # Fields to search
    search_fields = [
        'username', 'first_name', 'last_name', 'email', 
        'phone_number', 'city', 'country', 'current_role', 'company', 'acquisition_target'
    ]
    
    # Ordering
    ordering = ['-created_at']
    
    # Fields to display in the user detail/edit form
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Basic Profile Information', {
            'fields': (
                'phone_number', 'linkedin_url', 'website', 'languages'
            )
        }),
        ('Location Information', {
            'fields': ('country', 'city', 'state')
        }),
        ('Professional Background', {
            'fields': (
                'background', 'target_statement', 'acquisition_target', 'current_role', 'company', 'years_experience', 'bio'
            )
        }),
        ('Investment & Expertise', {
            'fields': (
                'value_proposition', 'areas_of_expertise', 'skills',
                'investment_experience', 'deal_size_preference', 
                'industry_focus', 'geographic_focus'
            )
        }),
        ('Education & Experience', {
            'fields': ('education_display', 'education', 'professional_experience_display', 'professional_experience', 'certifications', 'achievements')
        }),
        ('File Uploads', {
            'fields': ('resume', 'buyer_profile')
        }),
        ('Profile Status', {
            'fields': ('profile_completed','published','public_token')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'token_create_at'),
            'classes': ('collapse',),
        }),
    )
    
    # Fields to display when creating a new user
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Basic Profile Information', {
            'fields': (
                'first_name', 'last_name', 'email', 'phone_number',
                'linkedin_url', 'website', 'languages'
            )
        }),
        ('Location Information', {
            'fields': ('country', 'city', 'state')
        }),
        ('Professional Information', {
            'fields': ('current_role', 'company', 'background')
        }),
    )
    
    # Read-only fields
    readonly_fields = ['created_at', 'updated_at', 'professional_experience_display', 'education_display', 'public_token', 'token_create_at']
    
    def professional_experience_display(self, obj):
        """Display professional experience in a formatted way with management controls"""
        if not obj.professional_experience or obj.professional_experience is None or not isinstance(obj.professional_experience, list):
            return format_html(
                '<p>No professional experience recorded</p>'
                '<a href="{}add-experience/" class="button">Add Experience</a>',
                f'/admin/users/user/{obj.pk}/'
            )
        
        html_parts = [
            f'<div style="max-width: 800px;"><div style="margin-bottom: 10px;"><a href="/admin/users/user/{obj.pk}/add-experience/" class="button">Add New Experience</a></div>'
        ]
        
        for i, exp in enumerate(obj.professional_experience):
            # Skip None entries
            if exp is None or not isinstance(exp, dict):
                continue
            
            # Safely get values, handling None cases
            exp_id = exp.get('id', i+1)
            title = exp.get('title') or 'No Title'
            company = exp.get('company') or 'No Company'  
            duration = exp.get('duration') or 'No Duration'
            description = exp.get('description') or 'No Description'
            
            # Safely truncate description
            description_truncated = description[:200] if description and len(description) > 200 else description
            ellipsis = '...' if description and len(description) > 200 else ''
                
            html_parts.append(f"""
            <div style='margin-bottom: 15px; padding: 10px; border: 1px solid #ccc; border-radius: 5px; background: #f8f9fa; color: #333; position: relative;'>
                <div style='float: right; margin-left: 10px;'>
                    <a href='/admin/users/user/{obj.pk}/edit-experience/{i}/' style='margin-right: 5px;' class='button'>Edit</a>
                    <a href='/admin/users/user/{obj.pk}/delete-experience/{i}/' style='margin-right: 5px; color: #dc3545;' class='button'>Delete</a>
                    {f'<a href="/admin/users/user/{obj.pk}/move-experience/{i}/up/" class="button">↑</a>' if i > 0 else ''}
                    {f'<a href="/admin/users/user/{obj.pk}/move-experience/{i}/down/" class="button">↓</a>' if i < len(obj.professional_experience) - 1 else ''}
                </div>
                <strong style='color: #2c3e50; font-size: 14px;'>{exp_id}. {title}</strong><br>
                <em style='color: #555; font-size: 13px;'>{company} ({duration})</em><br>
                <p style='margin: 8px 0 0 0; font-size: 12px; color: #666; line-height: 1.4; clear: both;'>{description_truncated}{ellipsis}</p>
            </div>
            """)
        html_parts.append("</div>")
        return mark_safe("".join(html_parts))
    
    professional_experience_display.allow_tags = True
    professional_experience_display.short_description = "Professional Experience (Formatted)"
    
    def education_display(self, obj):
        """Display education in a formatted way with management controls"""
        if not obj.education or obj.education is None or not isinstance(obj.education, list):
            return format_html(
                '<p>No education recorded</p>'
                '<a href="{}add-education/" class="button">Add Education</a>',
                f'/admin/users/user/{obj.pk}/'
            )
        
        html_parts = [
            f'<div style="max-width: 800px;"><div style="margin-bottom: 10px;"><a href="/admin/users/user/{obj.pk}/add-education/" class="button">Add New Education</a></div>'
        ]
        
        for i, edu in enumerate(obj.education):
            # Skip None entries
            if edu is None or not isinstance(edu, dict):
                continue
            
            # Safely get values, handling None cases
            degree = edu.get('degree') or 'No Degree'
            field = edu.get('field') or 'No Field'  
            school = edu.get('school') or 'No School'
            years = edu.get('years') or 'No Years'
            description = edu.get('description') or 'No Description'
            
            # Safely truncate description
            description_truncated = description[:200] if description and len(description) > 200 else description
            ellipsis = '...' if description and len(description) > 200 else ''
                
            html_parts.append(f"""
            <div style='margin-bottom: 15px; padding: 10px; border: 1px solid #ccc; border-radius: 5px; background: #f0f8ff; color: #333; position: relative;'>
                <div style='float: right; margin-left: 10px;'>
                    <a href='/admin/users/user/{obj.pk}/edit-education/{i}/' style='margin-right: 5px;' class='button'>Edit</a>
                    <a href='/admin/users/user/{obj.pk}/delete-education/{i}/' style='margin-right: 5px; color: #dc3545;' class='button'>Delete</a>
                    {f'<a href="/admin/users/user/{obj.pk}/move-education/{i}/up/" class="button">↑</a>' if i > 0 else ''}
                    {f'<a href="/admin/users/user/{obj.pk}/move-education/{i}/down/" class="button">↓</a>' if i < len(obj.education) - 1 else ''}
                </div>
                <strong style='color: #1e3a8a; font-size: 14px;'>{degree} in {field}</strong><br>
                <em style='color: #555; font-size: 13px;'>{school} ({years})</em><br>
                <p style='margin: 8px 0 0 0; font-size: 12px; color: #666; line-height: 1.4; clear: both;'>{description_truncated}{ellipsis}</p>
            </div>
            """)
        html_parts.append("</div>")
        return mark_safe("".join(html_parts))
    
    education_display.allow_tags = True
    education_display.short_description = "Education (Formatted)"
    
    def get_readonly_fields(self, request, obj=None):
        """Make the formatted display field readonly"""
        readonly = list(super().get_readonly_fields(request, obj))
        readonly.extend(['created_at', 'updated_at', 'professional_experience_display', 'education_display'])
        return readonly
    
    def get_urls(self):
        """Add custom URLs for experience and education management"""
        urls = super().get_urls()
        custom_urls = [
            # Professional Experience URLs
            path('<int:user_id>/add-experience/', self.admin_site.admin_view(self.add_experience_view), name='users_user_add_experience'),
            path('<int:user_id>/edit-experience/<int:exp_index>/', self.admin_site.admin_view(self.edit_experience_view), name='users_user_edit_experience'),
            path('<int:user_id>/delete-experience/<int:exp_index>/', self.admin_site.admin_view(self.delete_experience_view), name='users_user_delete_experience'),
            path('<int:user_id>/move-experience/<int:exp_index>/<str:direction>/', self.admin_site.admin_view(self.move_experience_view), name='users_user_move_experience'),
            # Education URLs
            path('<int:user_id>/add-education/', self.admin_site.admin_view(self.add_education_view), name='users_user_add_education'),
            path('<int:user_id>/edit-education/<int:edu_index>/', self.admin_site.admin_view(self.edit_education_view), name='users_user_edit_education'),
            path('<int:user_id>/delete-education/<int:edu_index>/', self.admin_site.admin_view(self.delete_education_view), name='users_user_delete_education'),
            path('<int:user_id>/move-education/<int:edu_index>/<str:direction>/', self.admin_site.admin_view(self.move_education_view), name='users_user_move_education'),
        ]
        return custom_urls + urls
    
    def add_experience_view(self, request, user_id):
        """Add new professional experience"""
        user = User.objects.get(pk=user_id)
        
        if request.method == 'POST':
            new_exp = {
                'id': len(user.professional_experience) + 1,
                'title': request.POST.get('title', ''),
                'company': request.POST.get('company', ''),
                'duration': request.POST.get('duration', ''),
                'description': request.POST.get('description', '')
            }
            
            if not user.professional_experience:
                user.professional_experience = []
            user.professional_experience.append(new_exp)
            user.save()
            
            messages.success(request, f'Added experience: {new_exp["title"]} at {new_exp["company"]}')
            return redirect(f'/admin/users/user/{user_id}/change/')
        
        # Simple form for adding experience
        html = f'''
        <html><head><title>Add Professional Experience</title></head>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
        <h2>Add Professional Experience for {user.email}</h2>
        <form method="post">
            <p><label>Title:</label><br><input type="text" name="title" style="width: 300px;" required></p>
            <p><label>Company:</label><br><input type="text" name="company" style="width: 300px;" required></p>
            <p><label>Duration:</label><br><input type="text" name="duration" placeholder="e.g., 2020-01-01 - 2022-12-31" style="width: 300px;" required></p>
            <p><label>Description:</label><br><textarea name="description" rows="4" style="width: 500px;" required></textarea></p>
            <p><input type="submit" value="Add Experience" class="button"> <a href="/admin/users/user/{user_id}/change/" class="button">Cancel</a></p>
        </form>
        </body></html>
        '''
        return format_html(html)
    
    def edit_experience_view(self, request, user_id, exp_index):
        """Edit existing professional experience"""
        user = User.objects.get(pk=user_id)
        
        if exp_index >= len(user.professional_experience):
            messages.error(request, 'Experience not found')
            return redirect(f'/admin/users/user/{user_id}/change/')
        
        exp = user.professional_experience[exp_index]
        
        if request.method == 'POST':
            user.professional_experience[exp_index] = {
                'id': exp.get('id', exp_index + 1),
                'title': request.POST.get('title', ''),
                'company': request.POST.get('company', ''),
                'duration': request.POST.get('duration', ''),
                'description': request.POST.get('description', '')
            }
            user.save()
            
            messages.success(request, f'Updated experience: {request.POST.get("title")} at {request.POST.get("company")}')
            return redirect(f'/admin/users/user/{user_id}/change/')
        
        # Pre-filled form for editing
        html = f'''
        <html><head><title>Edit Professional Experience</title></head>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
        <h2>Edit Professional Experience for {user.email}</h2>
        <form method="post">
            <p><label>Title:</label><br><input type="text" name="title" value="{exp.get('title', '')}" style="width: 300px;" required></p>
            <p><label>Company:</label><br><input type="text" name="company" value="{exp.get('company', '')}" style="width: 300px;" required></p>
            <p><label>Duration:</label><br><input type="text" name="duration" value="{exp.get('duration', '')}" style="width: 300px;" required></p>
            <p><label>Description:</label><br><textarea name="description" rows="4" style="width: 500px;" required>{exp.get('description', '')}</textarea></p>
            <p><input type="submit" value="Update Experience" class="button"> <a href="/admin/users/user/{user_id}/change/" class="button">Cancel</a></p>
        </form>
        </body></html>
        '''
        return format_html(html)
    
    def delete_experience_view(self, request, user_id, exp_index):
        """Delete professional experience"""
        user = User.objects.get(pk=user_id)
        
        if exp_index >= len(user.professional_experience):
            messages.error(request, 'Experience not found')
            return redirect(f'/admin/users/user/{user_id}/change/')
        
        deleted_exp = user.professional_experience.pop(exp_index)
        
        # Reindex remaining experiences
        for i, exp in enumerate(user.professional_experience):
            exp['id'] = i + 1
        
        user.save()
        
        messages.success(request, f'Deleted experience: {deleted_exp.get("title")} at {deleted_exp.get("company")}')
        return redirect(f'/admin/users/user/{user_id}/change/')
    
    def move_experience_view(self, request, user_id, exp_index, direction):
        """Move professional experience up or down"""
        user = User.objects.get(pk=user_id)
        
        if exp_index >= len(user.professional_experience):
            messages.error(request, 'Experience not found')
            return redirect(f'/admin/users/user/{user_id}/change/')
        
        experiences = user.professional_experience
        
        if direction == 'up' and exp_index > 0:
            # Swap with previous
            experiences[exp_index], experiences[exp_index - 1] = experiences[exp_index - 1], experiences[exp_index]
            messages.success(request, 'Moved experience up')
        elif direction == 'down' and exp_index < len(experiences) - 1:
            # Swap with next
            experiences[exp_index], experiences[exp_index + 1] = experiences[exp_index + 1], experiences[exp_index]
            messages.success(request, 'Moved experience down')
        else:
            messages.warning(request, 'Cannot move experience in that direction')
        
        # Reindex all experiences
        for i, exp in enumerate(experiences):
            exp['id'] = i + 1
        
        user.save()
        return redirect(f'/admin/users/user/{user_id}/change/')
    
    # Education Management Methods
    def add_education_view(self, request, user_id):
        """Add new education entry"""
        user = User.objects.get(pk=user_id)
        
        if request.method == 'POST':
            new_edu = {
                'id': len(user.education) + 1,
                'school': request.POST.get('school', ''),
                'degree': request.POST.get('degree', ''),
                'field': request.POST.get('field', ''),
                'years': request.POST.get('years', ''),
                'description': request.POST.get('description', '')
            }
            
            if not user.education:
                user.education = []
            user.education.append(new_edu)
            user.save()
            
            messages.success(request, f'Added education: {new_edu["degree"]} in {new_edu["field"]} from {new_edu["school"]}')
            return redirect(f'/admin/users/user/{user_id}/change/')
        
        html = f'''
        <html><head><title>Add Education</title></head>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
        <h2>Add Education for {user.email}</h2>
        <form method="post">
            <p><label>School/Institution:</label><br><input type="text" name="school" style="width: 400px;" required></p>
            <p><label>Degree:</label><br><input type="text" name="degree" placeholder="e.g., Bachelor of Science, MBA, PhD" style="width: 300px;" required></p>
            <p><label>Field of Study:</label><br><input type="text" name="field" placeholder="e.g., Computer Science, Business Administration" style="width: 300px;" required></p>
            <p><label>Years:</label><br><input type="text" name="years" placeholder="e.g., 2010-2014, 2020" style="width: 200px;" required></p>
            <p><label>Description (optional):</label><br><textarea name="description" rows="3" style="width: 500px;" placeholder="Additional details, honors, achievements..."></textarea></p>
            <p><input type="submit" value="Add Education" class="button"> <a href="/admin/users/user/{user_id}/change/" class="button">Cancel</a></p>
        </form>
        </body></html>
        '''
        return format_html(html)
    
    def edit_education_view(self, request, user_id, edu_index):
        """Edit existing education entry"""
        user = User.objects.get(pk=user_id)
        
        if edu_index >= len(user.education):
            messages.error(request, 'Education entry not found')
            return redirect(f'/admin/users/user/{user_id}/change/')
        
        edu = user.education[edu_index]
        
        if request.method == 'POST':
            user.education[edu_index] = {
                'id': edu.get('id', edu_index + 1),
                'school': request.POST.get('school', ''),
                'degree': request.POST.get('degree', ''),
                'field': request.POST.get('field', ''),
                'years': request.POST.get('years', ''),
                'description': request.POST.get('description', '')
            }
            user.save()
            
            messages.success(request, f'Updated education: {request.POST.get("degree")} in {request.POST.get("field")}')
            return redirect(f'/admin/users/user/{user_id}/change/')
        
        html = f'''
        <html><head><title>Edit Education</title></head>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
        <h2>Edit Education for {user.email}</h2>
        <form method="post">
            <p><label>School/Institution:</label><br><input type="text" name="school" value="{edu.get('school', '')}" style="width: 400px;" required></p>
            <p><label>Degree:</label><br><input type="text" name="degree" value="{edu.get('degree', '')}" style="width: 300px;" required></p>
            <p><label>Field of Study:</label><br><input type="text" name="field" value="{edu.get('field', '')}" style="width: 300px;" required></p>
            <p><label>Years:</label><br><input type="text" name="years" value="{edu.get('years', '')}" style="width: 200px;" required></p>
            <p><label>Description:</label><br><textarea name="description" rows="3" style="width: 500px;">{edu.get('description', '')}</textarea></p>
            <p><input type="submit" value="Update Education" class="button"> <a href="/admin/users/user/{user_id}/change/" class="button">Cancel</a></p>
        </form>
        </body></html>
        '''
        return format_html(html)
    
    def delete_education_view(self, request, user_id, edu_index):
        """Delete education entry"""
        user = User.objects.get(pk=user_id)
        
        if edu_index >= len(user.education):
            messages.error(request, 'Education entry not found')
            return redirect(f'/admin/users/user/{user_id}/change/')
        
        deleted_edu = user.education.pop(edu_index)
        
        # Reindex remaining education entries
        for i, edu in enumerate(user.education):
            edu['id'] = i + 1
        
        user.save()
        
        messages.success(request, f'Deleted education: {deleted_edu.get("degree")} from {deleted_edu.get("school")}')
        return redirect(f'/admin/users/user/{user_id}/change/')
    
    def move_education_view(self, request, user_id, edu_index, direction):
        """Move education entry up or down"""
        user = User.objects.get(pk=user_id)
        
        if edu_index >= len(user.education):
            messages.error(request, 'Education entry not found')
            return redirect(f'/admin/users/user/{user_id}/change/')
        
        education = user.education
        
        if direction == 'up' and edu_index > 0:
            education[edu_index], education[edu_index - 1] = education[edu_index - 1], education[edu_index]
            messages.success(request, 'Moved education entry up')
        elif direction == 'down' and edu_index < len(education) - 1:
            education[edu_index], education[edu_index + 1] = education[edu_index + 1], education[edu_index]
            messages.success(request, 'Moved education entry down')
        else:
            messages.warning(request, 'Cannot move education entry in that direction')
        
        # Reindex all education entries
        for i, edu in enumerate(education):
            edu['id'] = i + 1
        
        user.save()
        return redirect(f'/admin/users/user/{user_id}/change/')
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete users"""
        return request.user.is_superuser


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    """
    Admin interface for OTP model
    """
    list_display = [
        'email', 'otp_code', 'user_exists', 'is_verified', 
        'is_used', 'attempts', 'created_at', 'expires_at'
    ]
    
    list_filter = [
        'user_exists', 'is_verified', 'is_used', 'created_at'
    ]
    
    search_fields = ['email', 'otp_code']
    
    readonly_fields = [
        'otp_code', 'created_at', 'expires_at', 'user_exists', 'user', 
    ]
    
    ordering = ['-created_at']
    
    fieldsets = (
        ('OTP Information', {
            'fields': ('email', 'otp_code', 'user_exists', 'user')
        }),
        ('Verification Status', {
            'fields': ('is_verified', 'is_used', 'attempts', 'max_attempts')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Don't allow manual creation of OTPs through admin"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Allow viewing but limited editing"""
        return True
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion of expired/used OTPs"""
        return True


# ==========================================
# AI MODELS ADMIN CONFIGURATION
# ==========================================

from .models import AIService, AIAgent, AIInteractionLog


@admin.register(AIService)
class AIServiceAdmin(admin.ModelAdmin):
    """
    Admin interface for AI Services
    """
    list_display = [
        'name', 'service_type', 'model_name', 'is_active', 'is_default', 
        'temperature', 'max_tokens', 'created_at'
    ]
    list_filter = ['service_type', 'is_active', 'is_default', 'created_at']
    search_fields = ['name', 'model_name', 'service_type']
    ordering = ['-is_default', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'service_type', 'model_name', 'description')
        }),
        ('API Configuration', {
            'fields': ('api_endpoint', 'api_key_name'),
            'classes': ('collapse',)
        }),
        ('Model Settings', {
            'fields': ('temperature', 'max_tokens'),
        }),
        ('Pricing', {
            'fields': ('input_cost_per_1k_tokens', 'output_cost_per_1k_tokens'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_default'),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('created_at', 'updated_at')
        return self.readonly_fields


@admin.register(AIAgent)
class AIAgentAdmin(admin.ModelAdmin):
    """
    Admin interface for AI Agents
    """
    list_display = [
        'name', 'agent_type', 'ai_service', 'is_active', 
        'get_effective_temperature', 'get_effective_max_tokens', 'created_at'
    ]
    list_filter = ['agent_type', 'ai_service', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'agent_type']
    ordering = ['agent_type', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'agent_type', 'description', 'is_active')
        }),
        ('AI Configuration', {
            'fields': ('ai_service',),
        }),
        ('Custom Settings (Optional)', {
            'fields': ('custom_temperature', 'custom_max_tokens'),
            'classes': ('collapse',),
            'description': 'Leave empty to use AI service defaults'
        }),
        ('Prompts', {
            'fields': ('system_prompt', 'user_prompt_template'),
            'classes': ('wide',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('created_at', 'updated_at')
        return self.readonly_fields
    
    def get_effective_temperature(self, obj):
        return obj.get_effective_temperature()
    get_effective_temperature.short_description = 'Temperature'
    
    def get_effective_max_tokens(self, obj):
        return obj.get_effective_max_tokens()
    get_effective_max_tokens.short_description = 'Max Tokens'


@admin.register(AIInteractionLog)
class AIInteractionLogAdmin(admin.ModelAdmin):
    """
    Admin interface for AI Interaction Logs
    """
    list_display = [
        'id', 'agent', 'user', 'status', 'model_used', 'total_tokens', 
        'total_cost', 'duration_seconds', 'request_timestamp'
    ]
    list_filter = [
        'status', 'agent', 'agent__ai_service', 'model_used', 
        'request_timestamp', 'response_timestamp'
    ]
    search_fields = [
        'agent__name', 'user__email', 'user__first_name', 'user__last_name',
        'session_id', 'model_used', 'input_text', 'response_text'
    ]
    ordering = ['-request_timestamp']
    date_hierarchy = 'request_timestamp'
    
    readonly_fields = [
        'agent', 'user', 'session_id', 'input_text', 'system_prompt_used', 
        'user_prompt_used', 'temperature_used', 'max_tokens_used', 'model_used',
        'response_text', 'parsed_response', 'request_timestamp', 
        'response_timestamp', 'duration_seconds', 'input_tokens', 
        'output_tokens', 'total_tokens', 'input_cost', 'output_cost', 
        'total_cost', 'ip_address', 'user_agent', 'additional_metadata'
    ]
    
    fieldsets = (
        ('Request Information', {
            'fields': ('agent', 'user', 'session_id', 'request_timestamp', 'ip_address', 'user_agent')
        }),
        ('Input Data', {
            'fields': ('input_text', 'system_prompt_used', 'user_prompt_used'),
            'classes': ('collapse',)
        }),
        ('AI Configuration Used', {
            'fields': ('model_used', 'temperature_used', 'max_tokens_used'),
            'classes': ('collapse',)
        }),
        ('Response Data', {
            'fields': ('status', 'response_text', 'parsed_response', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Performance Metrics', {
            'fields': ('response_timestamp', 'duration_seconds'),
        }),
        ('Token Usage & Cost', {
            'fields': ('input_tokens', 'output_tokens', 'total_tokens', 'input_cost', 'output_cost', 'total_cost'),
            'classes': ('wide',)
        }),
        ('Additional Data', {
            'fields': ('additional_metadata',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Don't allow manual creation of logs"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Allow viewing but no editing of logs"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion of old logs"""
        return request.user.is_superuser
    
    # Custom admin actions
    actions = ['mark_as_error', 'calculate_costs']
    
    def mark_as_error(self, request, queryset):
        """Mark selected logs as error status"""
        updated = queryset.update(status='error')
        self.message_user(request, f'{updated} logs marked as error.')
    mark_as_error.short_description = "Mark selected logs as error"
    
    def calculate_costs(self, request, queryset):
        """Recalculate costs for selected logs"""
        count = 0
        for log in queryset:
            if log.input_tokens and log.output_tokens:
                log.calculate_cost()
                count += 1
        self.message_user(request, f'Costs recalculated for {count} logs.')
    calculate_costs.short_description = "Recalculate costs for selected logs"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin interface for Question model"""
    list_display = ['id', 'text', 'subtitle', 'question_type', 'required', 'page', 'order', 'is_active', 'examples_display']
    list_filter = ['question_type', 'required', 'is_active', 'page']
    search_fields = ['text', 'placeholder', 'subtitle']
    ordering = ['page', 'order', 'id']

    fieldsets = (
        ('Question Details', {
            'fields': ('text', 'subtitle', 'question_type', 'required', 'page', 'order', 'is_active')
        }),
        ('Options', {
            'fields': ('options', 'placeholder', 'examples'),
            'description': 'Options should be a JSON array for select type questions'
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        # Make order field editable but show it prominently
        return []

    def examples_display(self, obj):
        """Render the examples list as small chips for easy viewing in list display."""
        examples = getattr(obj, 'examples', None) or []
        if not examples:
            return ''
        parts = [f'<span style="display:inline-block;margin:0 4px 4px 0;padding:4px 8px;background:#f3f4f6;border-radius:12px;border:1px solid #e5e7eb;font-size:12px;color:#111">{str(x)}</span>' for x in examples]
        return mark_safe(''.join(parts))
    examples_display.short_description = 'Examples'


@admin.register(Signed_links)
class SignedLinksAdmin(admin.ModelAdmin):
    """
    Admin interface for Signed Links with email sending functionality
    """
    list_display = ['email', 'token', 'created_at', 'expires_at', 'used', 'used_at', 'status_display']
    list_filter = ['used', 'created_at', 'expires_at']
    search_fields = ['email']
    readonly_fields = ['token', 'created_at', 'used_at']
    ordering = ['-created_at']
    
    def status_display(self, obj):
        """Display colored status indicator"""
        if obj.used:
            return format_html('<span style="color: red;">Used</span>')
        elif obj.is_valid():
            return format_html('<span style="color: green;">Valid</span>')
        else:
            return format_html('<span style="color: orange;">Expired</span>')
    status_display.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        """Override save to send email when creating new signed link"""
        is_new = obj._state.adding
        super().save_model(request, obj, form, change)
        
        if is_new:
            # Send invitation email
            self.send_invitation_email(obj)
            messages.success(request, f"Signed link created and invitation email sent to {obj.email}")
    
    def send_invitation_email(self, signed_link):
        """Send invitation email with signed link"""
        frontend_url = "https://www.searcherlist.com/"  # You can make this configurable
        # The signed link goes to profile-upload for validation, then redirects to the initial flow
        invitation_link = f"{frontend_url}/profile-upload?token={signed_link.token}&email={signed_link.email}"
        
        subject = "You've been invited to SearcherList!"
        
        message = f"""
Hello,

You have been invited to join SearcherList! 

Please click on the link below to get started:
{invitation_link}

This link will expire in 24 hours.

Best regards,
SearcherList Team
        """
        
        html_message = f"""
<html>
<body>
    <h2>You've been invited to SearcherList!</h2>
    
    <p>Hello,</p>
    
    <p>You have been invited to join SearcherList!</p>
    
    <p>Please click on the button below to get started:</p>
    
    <div style="margin: 20px 0;">
        <a href="{invitation_link}" 
           style="background-color: #007bff; color: white; padding: 10px 20px; 
                  text-decoration: none; border-radius: 5px; display: inline-block;">
            Join SearcherList
        </a>
    </div>
    
    <p>Or copy and paste this link in your browser:</p>
    <p><a href="{invitation_link}">{invitation_link}</a></p>
    
    <p><strong>Note:</strong> This link will expire in 24 hours.</p>
    
    <p>Best regards,<br>SearcherList Team</p>
</body>
</html>
        """
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[signed_link.email],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as e:
            print(f"Failed to send email to {signed_link.email}: {str(e)}")
            # You might want to log this error or handle it differently


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    """
    Admin interface for OTP Verification codes
    """
    list_display = ['email', 'otp_code', 'used', 'is_valid_display', 'created_at', 'expires_at', 'signed_link']
    list_filter = ['used', 'created_at', 'expires_at']
    search_fields = ['email', 'otp_code']
    readonly_fields = ['otp_code', 'created_at', 'expires_at', 'used_at']
    ordering = ['-created_at']
    
    def is_valid_display(self, obj):
        """Display if the OTP is currently valid"""
        if obj.is_valid():
            return format_html('<span style="color: green;">✓ Valid</span>')
        elif obj.used:
            return format_html('<span style="color: red;">✗ Used</span>')
        else:
            return format_html('<span style="color: orange;">✗ Expired</span>')
    is_valid_display.short_description = 'Status'
    
    fieldsets = (
        ('OTP Information', {
            'fields': ('email', 'otp_code', 'signed_link')
        }),
        ('Status', {
            'fields': ('used', 'used_at')
        }),
        ('Timing', {
            'fields': ('created_at', 'expires_at')
        })
    )
