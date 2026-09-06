from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.files.storage import default_storage
import cloudinary
import cloudinary.uploader
from django.conf import settings

@api_view(['POST'])
def upload_image(request):
    """Upload image to Cloudinary"""
    if 'image' not in request.FILES:
        return Response(
            {'error': 'No image file provided'},
            status=status.HTTP_400_BAD_REQUEST
        )

    image_file = request.FILES['image']

    # Validate file size (max 5MB)
    if image_file.size > 5 * 1024 * 1024:
        return Response(
            {'error': 'Image size exceeds 5MB limit'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate file type
    allowed_types = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}
    if image_file.content_type not in allowed_types:
        return Response(
            {'error': 'Invalid image format. Allowed: JPEG, PNG, WebP, GIF'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            image_file,
            folder='plasticprecious/',
            resource_type='auto',
            quality='auto',
            fetch_format='auto'
        )

        return Response({
            'success': True,
            'image_url': result['secure_url'],
            'public_id': result['public_id'],
            'size': result['bytes'],
            'width': result['width'],
            'height': result['height']
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Image upload failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
def delete_image(request):
    """Delete image from Cloudinary"""
    public_id = request.data.get('public_id')

    if not public_id:
        return Response(
            {'error': 'public_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        result = cloudinary.uploader.destroy(public_id)

        if result.get('result') == 'ok':
            return Response(
                {'success': True, 'message': 'Image deleted successfully'},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': 'Image not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        return Response(
            {'error': f'Image deletion failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
