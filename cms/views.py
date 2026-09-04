from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    Page, Testimonial, Banner, FAQ, BlogPost, Service,
    ContactInformation, Newsletter, ContactMessage, Feature, SiteSettings
)
from .serializers import (
    PageSerializer, TestimonialSerializer, BannerSerializer, FAQSerializer,
    BlogPostSerializer, BlogPostDetailSerializer, ServiceSerializer,
    ContactInformationSerializer, NewsletterSerializer, ContactMessageSerializer,
    ContactMessageCreateSerializer, FeatureSerializer, SiteSettingsSerializer
)

class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.filter(is_published=True)
    serializer_class = PageSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

    @action(detail=False, methods=['get'])
    def about(self, request):
        try:
            page = Page.objects.get(slug='about', is_published=True)
            serializer = self.get_serializer(page)
            return Response(serializer.data)
        except Page.DoesNotExist:
            return Response({'detail': 'Page not found'}, status=status.HTTP_404_NOT_FOUND)

class TestimonialViewSet(viewsets.ModelViewSet):
    queryset = Testimonial.objects.all()
    serializer_class = TestimonialSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_featured']
    ordering = ['-created_at']

class BannerViewSet(viewsets.ModelViewSet):
    queryset = Banner.objects.filter(is_active=True)
    serializer_class = BannerSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['banner_type', 'is_active']
    ordering = ['order', '-created_at']

class FAQViewSet(viewsets.ModelViewSet):
    queryset = FAQ.objects.filter(is_published=True)
    serializer_class = FAQSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category']
    search_fields = ['question', 'answer']
    ordering = ['order', '-created_at']

class BlogPostViewSet(viewsets.ModelViewSet):
    queryset = BlogPost.objects.filter(is_published=True)
    serializer_class = BlogPostSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['title', 'content']
    ordering = ['-published_at', '-created_at']
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BlogPostDetailSerializer
        return BlogPostSerializer

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]
    ordering = ['order', 'name']

class ContactInformationViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def list(self, request):
        try:
            contact_info = ContactInformation.objects.latest('updated_at')
            serializer = ContactInformationSerializer(contact_info)
            return Response(serializer.data)
        except ContactInformation.DoesNotExist:
            return Response({'detail': 'Contact information not found'}, status=status.HTTP_404_NOT_FOUND)

class NewsletterViewSet(viewsets.ModelViewSet):
    queryset = Newsletter.objects.all()
    serializer_class = NewsletterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        email = request.data.get('email')
        if not email:
            return Response({'email': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        newsletter, created = Newsletter.objects.get_or_create(email=email)
        if not created and not newsletter.is_subscribed:
            newsletter.is_subscribed = True
            newsletter.save()

        serializer = self.get_serializer(newsletter)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ContactMessageViewSet(viewsets.ModelViewSet):
    queryset = ContactMessage.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return ContactMessageCreateSerializer
        return ContactMessageSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], permission_classes=[IsAdminUser])
    def mark_as_read(self, request, pk=None):
        message = self.get_object()
        message.status = 'read'
        message.save()
        return Response(ContactMessageSerializer(message).data)

    @action(detail=True, methods=['patch'], permission_classes=[IsAdminUser])
    def reply(self, request, pk=None):
        message = self.get_object()
        reply_text = request.data.get('reply')
        if not reply_text:
            return Response({'reply': 'Reply text is required'}, status=status.HTTP_400_BAD_REQUEST)

        message.reply = reply_text
        message.status = 'replied'
        message.save()
        return Response(ContactMessageSerializer(message).data)

class FeatureViewSet(viewsets.ModelViewSet):
    queryset = Feature.objects.filter(is_active=True)
    serializer_class = FeatureSerializer
    permission_classes = [AllowAny]
    ordering = ['order', 'title']

class SiteSettingsViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def list(self, request):
        try:
            settings = SiteSettings.objects.latest('updated_at')
            serializer = SiteSettingsSerializer(settings)
            return Response(serializer.data)
        except SiteSettings.DoesNotExist:
            return Response({'detail': 'Settings not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['patch'], permission_classes=[IsAdminUser])
    def update_settings(self, request):
        try:
            settings = SiteSettings.objects.latest('updated_at')
        except SiteSettings.DoesNotExist:
            settings = SiteSettings.objects.create()

        serializer = SiteSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
