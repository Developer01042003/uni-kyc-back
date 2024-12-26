import logging
import boto3
import base64
import io
import uuid
from botocore.exceptions import ClientError
from django.conf import settings  # Import settings from Django
logger = logging.getLogger(__name__)

class AWSRekognition:
    def __init__(self):
        # Access the settings from Django
        self.client = boto3.client(
            'rekognition',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        self.collection_id = 'user_faces'
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        self.ensure_collection_exists()

    def ensure_collection_exists(self):
        """Create collection if it doesn't exist"""
        try:
            self.client.describe_collection(CollectionId=self.collection_id)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                self.client.create_collection(CollectionId=self.collection_id)
            else:
                raise Exception(f"Error checking collection: {str(e)}")

    

    def create_face_liveness_session(self):
     try:
        # Simplified version for testing
        response = self.client.create_face_liveness_session(
            Settings={
                'OutputConfig': {
                    'S3Bucket': self.bucket_name,
                }
            }
        )
        return response['SessionId']
     except Exception as e:
        print(f"Error: {str(e)}")
        raise


    def get_session_results(self, session_id):
        try:
            response = self.client.get_face_liveness_session_results(SessionId=session_id)
            return {
                'confidence': response.get('Confidence', 0),
                'reference_image': response.get('ReferenceImage', {}).get('Bytes')
            }
        except Exception as e:
            raise Exception(f"Error getting session results: {str(e)}")

    def search_faces(self, image_bytes):
        try:
            response = self.client.search_faces_by_image(
                CollectionId=self.collection_id,
                Image={'Bytes': image_bytes},
                MaxFaces=1,
                FaceMatchThreshold=95
            )
            return response['FaceMatches']
        except Exception as e:
            raise Exception(f"Error searching faces: {str(e)}")

    def index_face(self, image_bytes):
        try:
            response = self.client.index_faces(
                CollectionId=self.collection_id,
                Image={'Bytes': image_bytes},
                MaxFaces=1,
                QualityFilter="AUTO"
            )
            return response['FaceRecords'][0]['Face']['FaceId']
        except Exception as e:
            raise Exception(f"Error indexing face: {str(e)}")

    def upload_to_s3(self, image_bytes):
        try:
            file_name = f"kyc_images/{uuid.uuid4()}.jpg"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_name,
                Body=image_bytes,
                ContentType='image/jpeg'
            )
            return f"https://{self.bucket_name}.s3.amazonaws.com/{file_name}"
        except Exception as e:
            raise Exception(f"Error uploading to S3: {str(e)}")
