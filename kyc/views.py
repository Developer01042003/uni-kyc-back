# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from .models import KYC
from rest_framework.permissions import IsAuthenticated
from .serializers import  SessionResultSerializer, UserKYCSerializer
from .aws_helper import AWSRekognition
from django.conf import settings

class CreateSessionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Print request details
            print("Request User:", request.user)
            print("Request Data:", request.data)
            print("Request Headers:", request.headers)

            user_id = request.user.id
            print(f"Processing request for user_id: {user_id}")

            # Verify AWS credentials are loaded
            

            aws_rekognition = AWSRekognition()
            
            # Add more detailed error handling for session creation
            try:
                session_id = aws_rekognition.create_face_liveness_session()
                print(f"Created session ID: {session_id}")
            except Exception as session_error:
                print(f"Session creation error: {str(session_error)}")
                return Response({
                    'error': 'Session creation failed',
                    'detail': str(session_error)
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'session_id': session_id,
                'message': 'Session created successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"General error in CreateSessionView: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return Response({
                'error': 'Request failed',
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class SessionResultView(APIView):
    permission_classes = [IsAuthenticated]  # Added this line
    
    def post(self, request):
        # Add user_id from authenticated user
        data = request.data.copy()
        data['user_id'] = request.user.id  # Added this line
        
        serializer = SessionResultSerializer(data=data)
        if serializer.is_valid():
            try:
                aws_rekognition = AWSRekognition()
                
                # Get session results with reference image
                session_results = aws_rekognition.get_session_results(
                    serializer.validated_data['session_id']
                )
                
                if session_results['confidence'] < 90:
                    return Response({
                        'message': 'Liveness check failed',
                        'confidence': session_results['confidence']
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Get reference image bytes from session results
                reference_image_bytes = session_results['reference_image']
                if not reference_image_bytes:
                    return Response({
                        'error': 'Reference image not found in session results'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Check for duplicate faces
                face_matches = aws_rekognition.search_faces(reference_image_bytes)
                if face_matches:
                    return Response({
                        'message': 'Duplicate face found',
                        'match_confidence': face_matches[0]['Similarity']
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Index face and upload to S3
                face_id = aws_rekognition.index_face(reference_image_bytes)
                s3_url = aws_rekognition.upload_to_s3(reference_image_bytes)

                # Create UserKYC record
                try:
                    user = User.objects.get(id=serializer.validated_data['user_id'])
                except User.DoesNotExist:
                    return Response({
                        'error': 'User not found'
                    }, status=status.HTTP_404_NOT_FOUND)

                kyc = KYC.objects.create(
                    user=user,
                    face_id=face_id,
                    s3_image_url=s3_url,
                    is_verified=True
                )

                return Response({
                    'message': 'KYC completed successfully',
                    'kyc_data': UserKYCSerializer(kyc).data,
                    'confidence': session_results['confidence']
                }, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)