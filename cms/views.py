from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from staff.access import has_any_permission, require
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    Page, Testimonial, Banner, FAQ, BlogPost, Service,
    ContactInformation, Newsletter, ContactMessage, Feature, SiteSettings,
    HeroSlide, TeamMember, Partner
)
from .serializers import (
    PageSerializer, TestimonialSerializer, BannerSerializer, FAQSerializer,
    BlogPostSerializer, BlogPostDetailSerializer, ServiceSerializer,
    ContactInformationSerializer, NewsletterSerializer, ContactMessageSerializer,
    ContactMessageCreateSerializer, FeatureSerializer, SiteSettingsSerializer,
    HeroSlideSerializer, TeamMemberSerializer, PartnerSerializer
)

class ContentPermissionsMixin:
    """Anyone can read published content; Manage Content staff can edit it and also see unpublished/inactive items."""

    def get_permissions(self):
        return [require('manage_content', read_public=True)()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if has_any_permission(self.request.user, 'manage_content'):
            return queryset.model.objects.all()
        return queryset


class PageViewSet(ContentPermissionsMixin, viewsets.ModelViewSet):
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

class TestimonialViewSet(ContentPermissionsMixin, viewsets.ModelViewSet):
    queryset = Testimonial.objects.all()
    serializer_class = TestimonialSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_featured']
    ordering = ['-created_at']

class BannerViewSet(ContentPermissionsMixin, viewsets.ModelViewSet):
    queryset = Banner.objects.filter(is_active=True)
    serializer_class = BannerSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['banner_type', 'is_active']
    ordering = ['order', '-created_at']

class FAQViewSet(ContentPermissionsMixin, viewsets.ModelViewSet):
    queryset = FAQ.objects.filter(is_published=True)
    serializer_class = FAQSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category']
    search_fields = ['question', 'answer']
    ordering = ['order', '-created_at']

class BlogPostViewSet(ContentPermissionsMixin, viewsets.ModelViewSet):
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

class ServiceViewSet(ContentPermissionsMixin, viewsets.ModelViewSet):
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

    def get_permissions(self):
        # Anyone can subscribe; the subscriber list is for content staff
        if self.action == 'create':
            return [AllowAny()]
        return [require('manage_content')()]

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

    def get_permissions(self):
        # Anyone can send a message; reading and answering them is for community staff
        if self.action == 'create':
            return [AllowAny()]
        return [require('manage_community')()]

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

class FeatureViewSet(ContentPermissionsMixin, viewsets.ModelViewSet):
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


class HeroSlideViewSet(ContentPermissionsMixin, viewsets.ModelViewSet):
    queryset = HeroSlide.objects.all()
    serializer_class = HeroSlideSerializer
    ordering = ['order']

    def get_queryset(self):
        # Content staff see all slides (to edit inactive ones); visitors only see active slides
        if has_any_permission(self.request.user, 'manage_content'):
            return HeroSlide.objects.all()
        return HeroSlide.objects.filter(is_active=True)


class TeamMemberViewSet(ContentPermissionsMixin, viewsets.ModelViewSet):
    queryset = TeamMember.objects.filter(is_active=True)
    serializer_class = TeamMemberSerializer
    permission_classes = [AllowAny]
    ordering = ['order', 'name']


class PartnerViewSet(ContentPermissionsMixin, viewsets.ModelViewSet):
    queryset = Partner.objects.filter(is_active=True)
    serializer_class = PartnerSerializer
    permission_classes = [AllowAny]
    ordering = ['order', 'name']
