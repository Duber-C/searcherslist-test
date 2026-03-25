import json
import re
import secrets

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from users.views.profile import map_frontend_fields
from users.serializers.user import UserUpdateSerializer, UserSerializer


User = get_user_model()


@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_basic_info(request):
    """Update basic information section"""
    email = request.data.get('email')
    if not email:
        return Response({'message': 'Email is required', 'status': 'error'}, 
                       status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)

        update_data = {}
        if 'firstName' in request.data and request.data['firstName']:
            update_data['first_name'] = request.data['firstName']
        if 'lastName' in request.data and request.data['lastName']:
            update_data['last_name'] = request.data['lastName']
        if 'phoneNumber' in request.data and request.data['phoneNumber']:
            update_data['phone_number'] = request.data['phoneNumber']
        if 'linkedinUrl' in request.data:
            linkedin_url = request.data['linkedinUrl'].strip() if request.data['linkedinUrl'] else ''
            update_data['linkedin_url'] = linkedin_url
        if 'website' in request.data:
            website = request.data['website'].strip() if request.data['website'] else ''
            update_data['website'] = website
        if 'languages' in request.data:
            update_data['languages'] = request.data['languages']

        serializer = UserUpdateSerializer(user, data=update_data, partial=True)
        if serializer.is_valid():
            serializer.save()
        else:
            return Response({
                'message': 'Validation failed',
                'errors': serializer.errors,
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Basic information updated successfully!', 'status': 'success'}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'message': 'User not found', 'status': 'error'}, 
                       status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        print(f"DEBUG: Error in update_basic_info: {str(e)}")
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        return Response({'message': f'Update failed: {str(e)}', 'status': 'error'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_location(request):
    """Update location information section"""
    email = request.data.get('email')
    if not email:
        return Response({'message': 'Email is required', 'status': 'error'}, 
                       status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
        if 'country' in request.data:
            user.country = request.data['country']
        if 'state' in request.data:
            user.state = request.data['state']
        if 'city' in request.data:
            user.city = request.data['city']
        user.save()
        return Response({'message': 'Location updated successfully!', 'status': 'success'}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'message': 'User not found', 'status': 'error'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'message': str(e), 'status': 'error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["PATCH", "POST"])
@permission_classes([AllowAny])
def update_target_statement(request):
    print("🔥 update_target_statement called with method:", request.method)
    print("   request.data keys:", list(request.data.keys()))
    """
    Update target_statement for a user identified by email.

    Accepts any of these payload keys for safety/migrations:
      - target_statement (preferred)
      - targetStatement
      - acquisition_target / acquisitionTarget (fallback)

    Body can be JSON or form-data.

    Returns the saved value so you can verify immediately.
    """
    try:
        # --- lightweight request debug (won't dump long text) ---
        content_type = getattr(request, "content_type", None)
        keys = list(getattr(request, "data", {}).keys())
        print("🛠️ update_target_statement called")
        print(f"   method={request.method} content_type={content_type} keys={keys}")

        email = (request.data.get("email") or "").strip()
        if not email:
            print("   ❌ missing email")
            return Response(
                {"success": False, "message": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Accept multiple keys (so frontend/backend refactors don't break saves)
        incoming = (
            request.data.get("target_statement")
            or request.data.get("targetStatement")
            or request.data.get("acquisition_target")
            or request.data.get("acquisitionTarget")
        )

        if incoming is None:
            print("   ❌ missing target statement field in request.data")
            return Response(
                {
                    "success": False,
                    "message": "target_statement is required",
                    "received_keys": keys,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Normalize to string (avoid None / non-string)
        new_value = str(incoming)

        # Don't spam logs: show length + preview
        preview = new_value.replace("\n", "\\n")
        preview = (preview[:120] + "...") if len(preview) > 120 else preview
        print(f"   email={email}")
        print(f"   new_value_len={len(new_value)} preview='{preview}'")

        user = User.objects.filter(email=email).first()
        if not user:
            print("   ❌ user not found")
            return Response(
                {"success": False, "message": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        before = getattr(user, "target_statement", None)
        before_preview = (str(before)[:120] + "...") if before and len(str(before)) > 120 else before
        print(f"   before_target_statement_preview='{before_preview}'")

        # --- ACTUAL SAVE ---
        user.target_statement = new_value
        user.save(update_fields=["target_statement"])

        # reload to confirm it really persisted
        user.refresh_from_db(fields=["target_statement"])
        after = getattr(user, "target_statement", None)
        after_preview = (str(after)[:120] + "...") if after and len(str(after)) > 120 else after
        print(f"   ✅ saved_target_statement_preview='{after_preview}'")

        return Response(
            {
                "success": True,
                "message": "Target statement updated",
                "email": user.email,
                "saved": {
                    "target_statement": user.target_statement,
                    "length": len(user.target_statement or ""),
                },
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        # Print full traceback in dev
        import traceback

        print("💥 update_target_statement exception:", str(e))
        print(traceback.format_exc())
        return Response(
            {"success": False, "message": "Server error", "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    

@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_value_proposition(request):
    """Update value proposition section"""
    email = request.data.get('email')
    if not email:
        return Response({'message': 'Email is required', 'status': 'error'}, 
                       status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
        if 'valueProposition' in request.data:
            user.value_proposition = request.data['valueProposition']
        user.save()
        return Response({'message': 'Value proposition updated successfully!', 'status': 'success'}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'message': 'User not found', 'status': 'error'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'message': str(e), 'status': 'error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_expertise(request):
    """Update areas of expertise section"""
    email = request.data.get('email')
    if not email:
        return Response({'message': 'Email is required', 'status': 'error'}, 
                       status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
        if 'areasOfExpertise' in request.data:
            user.areas_of_expertise = request.data['areasOfExpertise']
        if 'skills' in request.data:
            user.skills = request.data['skills']
        user.save()
        return Response({'message': 'Areas of expertise updated successfully!', 'status': 'success'}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'message': 'User not found', 'status': 'error'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'message': str(e), 'status': 'error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_professional_experience(request):
    """Update professional experience section"""
    email = request.data.get('email')
    if not email:
        return Response({'message': 'Email is required', 'status': 'error'}, 
                       status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
        # Update straightforward fields
        if 'currentRole' in request.data:
            user.current_role = request.data['currentRole']
        if 'company' in request.data:
            user.company = request.data['company']
        if 'yearsExperience' in request.data:
            user.years_experience = request.data['yearsExperience']
        if 'bio' in request.data:
            user.bio = request.data['bio']
        if 'investmentExperience' in request.data:
            user.investment_experience = request.data['investmentExperience']
        if 'dealSizePreference' in request.data:
            user.deal_size_preference = request.data['dealSizePreference']
        if 'industryFocus' in request.data:
            user.industry_focus = request.data['industryFocus']
        if 'geographicFocus' in request.data:
            user.geographic_focus = request.data['geographicFocus']

        # professionalExperience parsing (string -> structured) or accept list
        if 'professionalExperience' in request.data:
            prof_exp_data = request.data['professionalExperience']
            if isinstance(prof_exp_data, str) and prof_exp_data.strip():
                experiences = []
                lines = prof_exp_data.split('\n\n')
                for i, line in enumerate(lines):
                    if line.strip():
                        clean_line = line.strip()
                        if clean_line.split('.')[0].strip().isdigit():
                            clean_line = '.'.join(clean_line.split('.')[1:]).strip()
                        experience_entry = {'id': i+1, 'company': '', 'title': '', 'duration': '', 'description': clean_line}
                        if ' at ' in clean_line:
                            parts = clean_line.split(' at ', 1)
                            experience_entry['title'] = parts[0].strip()
                            remaining = parts[1]
                            date_pattern = r'\((.*?)\)'
                            date_match = re.search(date_pattern, remaining)
                            if date_match:
                                experience_entry['duration'] = date_match.group(1)
                                experience_entry['company'] = remaining[:date_match.start()].strip()
                                desc_start = date_match.end()
                                if desc_start < len(remaining):
                                    experience_entry['description'] = remaining[desc_start:].strip()
                            else:
                                experience_entry['company'] = remaining.strip()
                        experiences.append(experience_entry)
                user.professional_experience = experiences
            elif isinstance(prof_exp_data, list):
                user.professional_experience = prof_exp_data

        elif 'professional_experience' in request.data:
            prof_exp_data = request.data['professional_experience']
            if isinstance(prof_exp_data, (list, dict)):
                user.professional_experience = prof_exp_data
            elif isinstance(prof_exp_data, str) and prof_exp_data.strip():
                try:
                    user.professional_experience = json.loads(prof_exp_data)
                except json.JSONDecodeError:
                    user.professional_experience = [{'id': 1, 'company': '', 'title': '', 'duration': '', 'description': prof_exp_data}]

        user.save()
        return Response({'message': 'Professional experience updated successfully!', 'status': 'success'}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'message': 'User not found', 'status': 'error'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'message': str(e), 'status': 'error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_education(request):
    """Update education and certifications section"""
    email = request.data.get('email')
    if not email:
        return Response({'message': 'Email is required', 'status': 'error'}, 
                       status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
        if 'education' in request.data:
            edu_data = request.data['education']
            if isinstance(edu_data, str) and edu_data.strip():
                try:
                    user.education = json.loads(edu_data)
                except json.JSONDecodeError:
                    education_entries = []
                    lines = edu_data.strip().split('\n')
                    current_entry = None
                    for i, line in enumerate(lines):
                        line = line.strip()
                        if not line:
                            if current_entry:
                                education_entries.append(current_entry)
                                current_entry = None
                            continue
                        if line.split('.')[0].strip().isdigit():
                            if current_entry:
                                education_entries.append(current_entry)
                            line_without_number = '.'.join(line.split('.')[1:]).strip()
                            entry = {'id': len(education_entries)+1, 'school': '', 'degree': '', 'field': '', 'years': '', 'description': line_without_number}
                            pattern1 = r'(.+?)\s+in\s+(.+?)\s+from\s+(.+?)\s*\(([^)]+)\)'
                            match = re.search(pattern1, line_without_number)
                            if match:
                                entry.update({'degree': match.group(1).strip(), 'field': match.group(2).strip(), 'school': match.group(3).strip(), 'years': match.group(4).strip()})
                            else:
                                pattern2 = r'(.+?)\s+from\s+(.+?)\s*\(([^)]+)\)'
                                match2 = re.search(pattern2, line_without_number)
                                if match2:
                                    degree_part = match2.group(1).strip()
                                    entry.update({'degree': degree_part, 'field': '', 'school': match2.group(2).strip(), 'years': match2.group(3).strip()})
                            current_entry = entry
                        elif current_entry and line:
                            if current_entry['description'] != current_entry.get('degree', '') + ' in ' + current_entry.get('field', ''):
                                current_entry['description'] += '\n' + line
                            else:
                                current_entry['description'] = line
                    if current_entry:
                        education_entries.append(current_entry)
                    user.education = education_entries
            elif isinstance(edu_data, list):
                user.education = edu_data

        if 'certifications' in request.data:
            user.certifications = request.data['certifications']
        if 'achievements' in request.data:
            user.achievements = request.data['achievements']
        user.save()
        return Response({'message': 'Education and certifications updated successfully!', 'status': 'success'}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'message': 'User not found', 'status': 'error'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'message': str(e), 'status': 'error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_profile_section(request, section_name):
    """Update individual profile sections"""
    try:
        if hasattr(request.data, 'dict'):
            data_dict = dict(request.data)
            processed_data = {}
            for key, value_list in data_dict.items():
                processed_data[key] = value_list[0] if isinstance(value_list, list) and value_list else value_list
        else:
            processed_data = dict(request.data)

        mapped_data = map_frontend_fields(processed_data)
        email = mapped_data.get('email')
        if not email:
            return Response({'status': 'error', 'message': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            first_name = mapped_data.get('first_name', '')
            last_name = mapped_data.get('last_name', '')
            user, created = User.objects.get_or_create(email=email, defaults={'username': email, 'first_name': first_name, 'last_name': last_name, 'is_active': True, 'profile_completed': False})
            if created:
                temp_password = secrets.token_urlsafe(16)
                user.password = make_password(temp_password)
                user.save()

        section_mappings = {
            'basic-info': ['first_name', 'last_name', 'phone_number', 'linkedin_url', 'website', 'languages'],
            'location': ['country', 'state', 'city'],
            'target-statement': ['background'],
            'value-proposition': ['value_proposition'],
            'expertise': ['areas_of_expertise', 'skills', 'investment_experience', 'deal_size_preference', 'geographic_focus', 'industry_focus', 'value_proposition'],
            'professional-experience': ['current_role', 'company', 'years_experience', 'bio', 'professional_experience'],
            'experience': ['current_role', 'company', 'years_experience', 'bio', 'professional_experience'],
            'education': ['education', 'certifications', 'achievements'],
            'certifications': ['certifications', 'achievements']
        }

        if section_name not in section_mappings:
            return Response({'status': 'error', 'message': f'Invalid section: {section_name}'}, status=status.HTTP_400_BAD_REQUEST)

        section_fields = section_mappings[section_name]
        update_data = {field: mapped_data.get(field) for field in section_fields if field in mapped_data}

        # parsing for professional_experience and education handled similarly as above
        if 'professional_experience' in update_data and isinstance(update_data['professional_experience'], str):
            prof_exp_text = update_data['professional_experience']
            experiences = []
            lines = prof_exp_text.strip().split('\n')
            current_experience = None
            for line in lines:
                line = line.strip()
                if not line:
                    if current_experience:
                        experiences.append(current_experience)
                        current_experience = None
                    continue
                if line.split('.')[0].strip().isdigit():
                    if current_experience:
                        experiences.append(current_experience)
                    line_without_number = '.'.join(line.split('.')[1:]).strip()
                    experience = {'id': len(experiences)+1, 'title': '', 'company': '', 'duration': '', 'description': line_without_number}
                    if ' at ' in line_without_number:
                        parts = line_without_number.split(' at ', 1)
                        experience['title'] = parts[0].strip()
                        remaining = parts[1].strip()
                        date_pattern = r'\(([^)]+)\)'
                        date_match = re.search(date_pattern, remaining)
                        if date_match:
                            experience['duration'] = date_match.group(1)
                            experience['company'] = remaining[:date_match.start()].strip()
                            desc_start = date_match.end()
                            if desc_start < len(remaining):
                                desc_text = remaining[desc_start:].strip()
                                if desc_text:
                                    experience['description'] = desc_text
                    current_experience = experience
                elif current_experience and line:
                    if current_experience['description'] and current_experience['description'] != (current_experience['title'] + ' at ' + current_experience['company']):
                        current_experience['description'] += '\n' + line
                    else:
                        current_experience['description'] = line
            if current_experience:
                experiences.append(current_experience)
            update_data['professional_experience'] = experiences

        if 'education' in update_data and isinstance(update_data['education'], str):
            edu_text = update_data['education']
            education_entries = []
            lines = edu_text.strip().split('\n')
            current_entry = None
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    if current_entry:
                        education_entries.append(current_entry)
                        current_entry = None
                    continue
                if line.split('.')[0].strip().isdigit():
                    if current_entry:
                        education_entries.append(current_entry)
                    line_without_number = '.'.join(line.split('.')[1:]).strip()
                    entry = {'id': len(education_entries)+1, 'school': '', 'degree': '', 'field': '', 'years': '', 'description': line_without_number}
                    pattern1 = r'(.+?)\s+in\s+(.+?)\s+from\s+(.+?)\s*\(([^)]+)\)'
                    match = re.search(pattern1, line_without_number)
                    if match:
                        entry.update({'degree': match.group(1).strip(), 'field': match.group(2).strip(), 'school': match.group(3).strip(), 'years': match.group(4).strip()})
                    else:
                        pattern2 = r'(.+?)\s+from\s+(.+?)\s*\(([^)]+)\)'
                        match2 = re.search(pattern2, line_without_number)
                        if match2:
                            degree_part = match2.group(1).strip()
                            entry.update({'degree': degree_part, 'field': '', 'school': match2.group(2).strip(), 'years': match2.group(3).strip()})
                    current_entry = entry
                elif current_entry and line:
                    if current_entry['description'] != current_entry.get('degree', '') + ' in ' + current_entry.get('field', ''):
                        current_entry['description'] += '\n' + line
                    else:
                        current_entry['description'] = line
            if current_entry:
                education_entries.append(current_entry)
            update_data['education'] = education_entries

        serializer = UserUpdateSerializer(user, data=update_data, partial=True)
        if serializer.is_valid():
            updated_user = serializer.save()
            is_autosave = False
            autosave_val = mapped_data.get('autosave')
            if autosave_val is not None:
                try:
                    if isinstance(autosave_val, str):
                        is_autosave = autosave_val.lower() in ['true', '1', 'yes', 'on']
                    else:
                        is_autosave = bool(autosave_val)
                except Exception:
                    is_autosave = False
            if not is_autosave:
                profile_was_completed = updated_user.profile_completed
                force_profile_complete = updated_user.mark_profile_complete()
            return Response({'status': 'success', 'message': f'{section_name.replace("-", " ").title()} updated successfully!', 'user': UserSerializer(updated_user).data}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'error', 'message': 'Validation failed', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        import traceback
        print(f"DEBUG: Exception in update_profile_section: {str(e)}")
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        return Response({'status': 'error', 'message': f'Server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([AllowAny])
def save_professional_experience_data(request):
    """
    Endpoint to save professional experience data directly to the database
    """
    try:
        email = request.data.get("email")
        experience_data = request.data.get("experience_data")

        if not email:
            return Response(
                {"status": "error", "message": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not experience_data:
            return Response(
                {"status": "error", "message": "Experience data is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        print(f"DEBUG: Saving professional experience for {email}")
        print(f"DEBUG: Experience data type: {type(experience_data)}")

        try:
            user = User.objects.get(email=email)
            print(f"DEBUG: Found existing user: {user.email}")
        except User.DoesNotExist:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": email,
                    "is_active": True,
                    "profile_completed": False,
                },
            )
            print(f"DEBUG: {'Created' if created else 'Retrieved'} user: {user.email}")

        if isinstance(experience_data, list):
            user.professional_experience = experience_data
            print(f"DEBUG: Saved {len(experience_data)} structured experiences")
        elif isinstance(experience_data, str):
            experiences = []
            lines = experience_data.strip().split("\n")
            current_experience = None
            for line in lines:
                line = line.strip()
                if not line:
                    if current_experience:
                        experiences.append(current_experience)
                        current_experience = None
                    continue
                if line.split(".")[0].strip().isdigit():
                    if current_experience:
                        experiences.append(current_experience)
                    line_without_number = ".".join(line.split(".")[1:]).strip()
                    experience = {
                        "id": len(experiences) + 1,
                        "title": "",
                        "company": "",
                        "duration": "",
                        "description": line_without_number,
                    }
                    if " at " in line_without_number:
                        parts = line_without_number.split(" at ", 1)
                        experience["title"] = parts[0].strip()
                        remaining = parts[1].strip()
                        date_pattern = r"\(([^)]+)\)"
                        date_match = re.search(date_pattern, remaining)
                        if date_match:
                            experience["duration"] = date_match.group(1)
                            experience["company"] = remaining[: date_match.start()].strip()
                            desc_start = date_match.end()
                            if desc_start < len(remaining):
                                desc_text = remaining[desc_start:].strip()
                                if desc_text:
                                    experience["description"] = desc_text
                        else:
                            experience["company"] = remaining
                    current_experience = experience
                elif current_experience and line:
                    if current_experience["description"] and current_experience[
                        "description"
                    ] != (current_experience["title"] + " at " + current_experience["company"]):
                        current_experience["description"] += "\n" + line
                    else:
                        current_experience["description"] = line
            if current_experience:
                experiences.append(current_experience)
            user.professional_experience = experiences
            print(f"DEBUG: Parsed and saved {len(experiences)} experiences from text")

        user.save()

        return Response(
            {
                "status": "success",
                "message": f"Successfully saved {len(user.professional_experience)} professional experiences",
                "experiences_count": len(user.professional_experience),
                "experiences": user.professional_experience,
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        print(f"DEBUG: Error saving professional experience: {str(e)}")
        import traceback
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        return Response(
            {
                "status": "error",
                "message": f"Failed to save professional experience: {str(e)}",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
