import tempfile
import os
import json
import traceback

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from users.models.user import User
from ai_profile_creation.chatGpt import (
    extract_profile_from_text,
    extract_text_from_docx,
    extract_profile_from_multiple_sources,
)


@api_view(['POST'])
@permission_classes([AllowAny])
def ai_profile_extraction(request):
    """
    AI-powered profile extraction endpoint
    Accepts file upload for AI processing and stores file content
    """
    try:
        print("DEBUG: Starting AI profile extraction...")
        print(f"DEBUG: Request FILES: {request.FILES.keys()}")
        print(f"DEBUG: Request data: {request.data.keys()}")

        text_to_process = None
        file_type = None
        user_email = request.data.get('email')

        if request.data.get('process_existing_file'):
            file_type = request.data.get('file_type', 'resume')
            if not user_email:
                return Response({'status': 'error', 'message': 'Email is required when processing existing file'}, status=400)

            try:
                user = User.objects.get(email=user_email)
            except User.DoesNotExist:
                return Response({'status': 'error', 'message': 'User not found'}, status=404)

            file_obj = None
            if file_type == 'resume' and user.resume:
                file_obj = user.resume
            elif file_type == 'buyer_profile' and user.buyer_profile:
                file_obj = user.buyer_profile

            if not file_obj:
                return Response({'status': 'error', 'message': f'No {file_type} file found for user'}, status=404)

            file_path = file_obj.path
            file_extension = os.path.splitext(file_path)[1].lower()
            if file_extension not in ['.pdf', '.doc', '.docx']:
                return Response({'status': 'error', 'message': 'Unsupported file format. Only PDF, DOC, and DOCX files are supported.'}, status=400)

            try:
                if file_extension == '.pdf':
                    return Response({'status': 'error', 'message': 'PDF processing not yet implemented. Please use DOC or DOCX files.'}, status=400)
                else:
                    text_to_process = extract_text_from_docx(file_path)
            except Exception as e:
                print(f"DEBUG: Error extracting text from existing file: {e}")
                print(traceback.format_exc())
                return Response({'status': 'error', 'message': f'Failed to extract text from existing file: {str(e)}'}, status=500)

        elif 'file' in request.FILES:
            uploaded_file = request.FILES['file']
            file_name = uploaded_file.name.lower()
            if 'resume' in file_name or 'cv' in file_name:
                file_type = 'resume'
            elif 'buyer' in file_name or 'profile' in file_name:
                file_type = 'buyer_profile'
            else:
                file_type = 'resume'

            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            if file_extension not in ['.pdf', '.doc', '.docx']:
                return Response({'status': 'error', 'message': 'Unsupported file format. Please upload PDF, DOC, or DOCX files only.'}, status=400)

            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            try:
                if file_extension == '.pdf':
                    return Response({'status': 'error', 'message': 'PDF processing not yet implemented. Please use DOC or DOCX files.'}, status=400)
                else:
                    text_to_process = extract_text_from_docx(temp_file_path)
            finally:
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass

        elif 'text' in request.data:
            text_to_process = request.data['text']

        else:
            sample_text = """
            John Smith
            Senior Investment Analyst
            ABC Capital Partners
            """
            text_to_process = sample_text

        if not text_to_process or len(text_to_process.strip()) < 50:
            return Response({'status': 'error', 'message': 'Insufficient text content for AI processing. Please provide a document with more content.'}, status=400)

        try:
            user_obj = User.objects.get(email=user_email) if user_email else None
        except User.DoesNotExist:
            user_obj = None

        if user_obj:
            buyer_profile_text = user_obj.existing_buyer_profile if getattr(user_obj, 'existing_buyer_profile', None) else None
            resume_text = user_obj.resume_upload if getattr(user_obj, 'resume_upload', None) else None
            linkedin_data = user_obj.linkedin_data if getattr(user_obj, 'linkedin_data', None) else None

            if text_to_process:
                if file_type == 'buyer_profile':
                    buyer_profile_text = text_to_process
                elif file_type == 'resume':
                    resume_text = text_to_process

            available_sources = []
            if buyer_profile_text and len(buyer_profile_text) > 100:
                available_sources.append('buyer_profile')
            if resume_text and len(resume_text) > 100:
                available_sources.append('resume')
            if linkedin_data:
                available_sources.append('linkedin')

            if len(available_sources) > 1:
                extracted_data = extract_profile_from_multiple_sources(
                    buyer_profile_text=buyer_profile_text,
                    resume_text=resume_text,
                    linkedin_data=linkedin_data,
                    agent_name='Profile Extraction Agent',
                    user=user_obj,
                    session_id=f"multi_source_extraction_{user_email}"
                )
            else:
                extracted_data = extract_profile_from_text(
                    text_to_process,
                    agent_name='Profile Extraction Agent',
                    user=user_obj,
                    session_id=f"profile_extraction_{user_email}"
                )
        else:
            extracted_data = extract_profile_from_text(text_to_process, agent_name='Profile Extraction Agent', user=None, session_id='profile_extraction_anonymous')

        if user_email and file_type:
            try:
                user = User.objects.get(email=user_email)
                if file_type == 'resume':
                    user.resume_upload = text_to_process
                elif file_type == 'buyer_profile':
                    user.existing_buyer_profile = text_to_process
                user.save()
            except User.DoesNotExist:
                pass

        response_data = {
            'status': 'success',
            'message': 'AI profile extraction completed successfully',
            'extracted_data': extracted_data,
            'file_type': file_type,
            'text_processed': len(text_to_process) > 1000,
            'content_stored': bool(user_email and file_type)
        }

        return Response(response_data, status=200)

    except ImportError as e:
        return Response({'status': 'error', 'message': f'Failed to import AI extraction modules: {str(e)}', 'debug_info': 'Make sure the chatGpt.py file is in the ai_profile_creation directory'}, status=500)
    except Exception as e:
        print(f"DEBUG: Error in AI profile extraction: {e}")
        print(traceback.format_exc())
        return Response({'status': 'error', 'message': f'AI profile extraction failed: {str(e)}', 'error_type': type(e).__name__}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def linkedin_import(request):
    try:
        user_email = request.data.get('email')
        linkedin_data = request.data.get('linkedin_data')

        if not user_email:
            return Response({'status': 'error', 'message': 'Email is required'}, status=400)
        if not linkedin_data:
            return Response({'status': 'error', 'message': 'LinkedIn data is required'}, status=400)

        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return Response({'status': 'error', 'message': 'User not found. Please create a profile first.'}, status=404)

        user.linkedin_data = linkedin_data
        user.save()

        return Response({'status': 'success', 'message': 'LinkedIn data imported successfully', 'user_email': user_email, 'data_fields': list(linkedin_data.keys()) if isinstance(linkedin_data, dict) else []}, status=200)

    except Exception as e:
        print(f"DEBUG: Error in linkedin_import: {e}")
        print(traceback.format_exc())
        return Response({'status': 'error', 'message': f'Error importing LinkedIn data: {str(e)}'}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def multi_source_extraction(request):
    try:
        print("DEBUG: Starting multi-source AI profile extraction...")
        print("payload keys content", request.data)
        print("questionnaire_answers", request.data.get("questionnaire_answers"))
        from ai_profile_creation.chatGpt import extract_profile_from_multiple_sources, extract_text_from_docx
        import tempfile
        import os

        def save_upload_to_temp(uploaded_file, suffix: str) -> str:
            fd, path = tempfile.mkstemp(suffix=suffix)
            try:
                with os.fdopen(fd, "wb") as f:
                    for chunk in uploaded_file.chunks():
                        f.write(chunk)
                return path
            except Exception:
                try:
                    os.unlink(path)
                except Exception:
                    pass
                raise

        def extract_text_from_pdf(pdf_path: str) -> str:
            import PyPDF2
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                pages_text = []
                for pg in reader.pages:
                    try:
                        pages_text.append(pg.extract_text() or "")
                    except Exception:
                        pages_text.append("")
            return "\n".join(pages_text).strip()

        def extract_text_from_uploaded_file(uploaded_file, label: str) -> str:
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext not in [".pdf", ".docx", ".doc"]:
                raise ValueError(f"{label}: Unsupported file format. Please upload PDF or DOCX.")
            if ext == ".doc":
                raise ValueError(f"{label}: Legacy .doc is not supported. Please upload .docx or .pdf instead.")
            temp_path = save_upload_to_temp(uploaded_file, ext)
            try:
                if ext == ".pdf":
                    text = extract_text_from_pdf(temp_path)
                    if not text:
                        raise ValueError(f"{label}: Failed to extract text from PDF. Try a different PDF or upload DOCX.")
                    return text
                text = extract_text_from_docx(temp_path)
                if not text:
                    raise ValueError(f"{label}: Extracted empty text from DOCX. Try a different DOCX.")
                return text
            finally:
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass

        buyer_profile_text = None
        resume_text = None
        linkedin_data = None
        questionnaire_answers = None

        if "buyer_profile" in request.FILES:
            buyer_profile_file = request.FILES["buyer_profile"]
            try:
                buyer_profile_text = extract_text_from_uploaded_file(buyer_profile_file, "Buyer profile")
            except ValueError as ve:
                return Response({"status": "error", "message": str(ve)}, status=400)

        if "resume" in request.FILES:
            resume_file = request.FILES["resume"]
            try:
                resume_text = extract_text_from_uploaded_file(resume_file, "Resume")
            except ValueError as ve:
                return Response({"status": "error", "message": str(ve)}, status=400)

        if "linkedin_url" in request.data:
            linkedin_url = (request.data.get("linkedin_url") or "").strip()
            if linkedin_url:
                try:
                    from linkedIn_extraction import run_linkedin_extraction
                    linkedin_data = run_linkedin_extraction(linkedin_url)
                except Exception:
                    linkedin_data = {"linkedin_url": linkedin_url, "source": "manual_url_fallback"}

        if "questionnaire_answers" in request.data:
            try:
                questionnaire_answers = json.loads(request.data["questionnaire_answers"])
            except Exception:
                questionnaire_answers = None

        # Normalize questionnaire answers so downstream extractor receives plain strings
        questionnaire_answers_normalized = None
        if questionnaire_answers:
            def _norm_value(v):
                if isinstance(v, dict):
                    # composite radio + from/to pattern
                    if any(k in v for k in ("radio", "from", "to")):
                        parts = []
                        if v.get("radio"):
                            parts.append(str(v.get("radio")))
                        f = v.get("from")
                        t = v.get("to")
                        if f and t:
                            parts.append(f"{f}-{t}")
                        elif f:
                            parts.append(str(f))
                        elif t:
                            parts.append(str(t))
                        return " ".join(parts) if parts else json.dumps(v)
                    if "value" in v:
                        return str(v["value"])
                    if "title" in v:
                        return str(v["title"])
                    return json.dumps(v)
                if isinstance(v, list):
                    items = []
                    for it in v:
                        if isinstance(it, dict):
                            if "value" in it:
                                items.append(str(it["value"]))
                            elif "title" in it:
                                items.append(str(it["title"]))
                            else:
                                items.append(json.dumps(it))
                        else:
                            items.append(str(it))
                    return ", ".join(items)
                return str(v)

            questionnaire_answers_normalized = {k: _norm_value(v) for k, v in questionnaire_answers.items()}
            try: print("DEBUG: questionnaire_answers_normalized", questionnaire_answers_normalized)
            except Exception: pass
        else:
            questionnaire_answers_normalized = None

        available_sources = []
        if buyer_profile_text and len(buyer_profile_text) > 100:
            available_sources.append("buyer_profile")
        if resume_text and len(resume_text) > 100:
            available_sources.append("resume")
        if linkedin_data:
            available_sources.append("linkedin")
        if questionnaire_answers_normalized:
            available_sources.append("questionnaire")

        if not available_sources:
            return Response({"status": "error", "message": "No valid data sources provided. Please upload at least one DOCX/PDF, provide LinkedIn, or include questionnaire answers."}, status=400)

        extracted_data = extract_profile_from_multiple_sources(
            buyer_profile_text=buyer_profile_text,
            resume_text=resume_text,
            linkedin_data=linkedin_data,
            questionnaire_answers=questionnaire_answers_normalized or questionnaire_answers,
            agent_name="Profile Extraction Agent",
            user=None,
            session_id=f"multi_source_upload_{hash(str(available_sources))}",
        )

        if isinstance(extracted_data, dict):
            for key, val in list(extracted_data.items()):
                if isinstance(val, dict) and 'value' in val:
                    extracted_data[key] = val['value']
            for key in ["education", "professional_experience"]:
                if key in extracted_data and isinstance(extracted_data[key], str):
                    try:
                        extracted_data[key] = json.loads(extracted_data[key])
                    except Exception:
                        pass
        # Persist raw questionnaire answers on the user record if possible
        if questionnaire_answers and 'email' in request.data:
            try:
                user_email = request.data.get('email')
                user = User.objects.filter(email=user_email).first()
                if user:
                    # store normalized answers for easier inspection later
                    user.questionnaire_answers = questionnaire_answers_normalized or questionnaire_answers
                    user.save(update_fields=['questionnaire_answers'])
            except Exception as e:
                print(f"Failed to save questionnaire_answers to user record: {e}")

        response_data = {"status": "success", "message": f"Multi-source AI extraction completed using {len(available_sources)} sources", "extracted_data": extracted_data, "sources_processed": available_sources, "sources_count": len(available_sources)}

        return Response(response_data, status=200)

    except ImportError as e:
        return Response({"status": "error", "message": f"Failed to import AI extraction modules: {str(e)}", "debug_info": "Make sure the chatGpt.py file is in the ai_profile_creation directory"}, status=500)
    except Exception as e:
        print(f"DEBUG: Error in multi-source AI profile extraction: {e}")
        print(traceback.format_exc())
        return Response({"status": "error", "message": f"Multi-source AI profile extraction failed: {str(e)}", "error_type": type(e).__name__}, status=500)
