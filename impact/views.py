import csv
from datetime import date

from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, BasePermission, SAFE_METHODS
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle
from .models import ImpactMetric, ImpactEntry, CollectionZone, Event, EventRegistration, NewsletterSubscription, BulkRFQ, Sponsorship, VolunteerOpportunity
from staff.access import has_any_permission, require
from .services import compute_summary, customer_impact, rebuild_sales_impact, sponsorship_stats, user_from_share_token
from .constants import SPONSORSHIP_ITEMS


def _parse_date(value, field):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f'{field} must be a date in YYYY-MM-DD format')

class IsAuthenticatedOrCreateOnly(BasePermission):
    """Allow unauthenticated create, but require auth for other operations"""
    def has_permission(self, request, view):
        if request.method == 'POST' and view.action == 'create':
            return True
        return request.user and request.user.is_authenticated
from .serializers import (ImpactMetricSerializer, ImpactEntrySerializer, CollectionZoneSerializer, EventSerializer, EventRegistrationSerializer,
                          NewsletterSubscriptionSerializer, BulkRFQSerializer, SponsorshipSerializer,
                          SponsorshipAdminSerializer, VolunteerOpportunitySerializer)

class ImpactMetricViewSet(viewsets.ModelViewSet):
    """Headline metrics: public read (active only), staff write."""
    serializer_class = ImpactMetricSerializer
    permission_classes = [require('create_reports', 'manage_content', read_public=True)]
    pagination_class = None

    def get_queryset(self):
        qs = ImpactMetric.objects.all()
        if not has_any_permission(self.request.user, 'create_reports', 'manage_content', 'view_analytics'):
            qs = qs.filter(is_active=True)
        return qs


class CollectionZoneViewSet(viewsets.ModelViewSet):
    serializer_class = CollectionZoneSerializer
    permission_classes = [require('create_reports', read_public=True)]

    def get_queryset(self):
        qs = CollectionZone.objects.all().order_by('name')
        if not has_any_permission(self.request.user, 'create_reports', 'view_analytics'):
            qs = qs.filter(active=True)
        return qs


class ImpactEntryViewSet(viewsets.ModelViewSet):
    """The business impact log. Sale entries created from orders are read-only here."""
    serializer_class = ImpactEntrySerializer
    permission_classes = [require('create_reports')]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['source', 'product', 'zone', 'plastic_type']
    search_fields = ['title', 'notes', 'product__name']
    ordering_fields = ['date', 'plastic_kg', 'co2_saved_kg', 'created_at']
    ordering = ['-date', '-created_at']

    def get_permissions(self):
        # Analysts can read and export the log; recording or changing entries needs Create Reports
        if self.request.method in SAFE_METHODS:
            return [require('create_reports', 'view_analytics')()]
        return [require('create_reports')()]

    def get_queryset(self):
        qs = ImpactEntry.objects.select_related('product', 'zone', 'created_by')
        try:
            start = _parse_date(self.request.query_params.get('start'), 'start')
            end = _parse_date(self.request.query_params.get('end'), 'end')
        except ValueError:
            return qs.none()
        if start:
            qs = qs.filter(date__gte=start)
        if end:
            qs = qs.filter(date__lte=end)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def _automatic_entry_error(self):
        return Response(
            {'error': 'This entry was recorded automatically from an order or sponsorship. Change its status instead.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def update(self, request, *args, **kwargs):
        entry = self.get_object()
        if entry.order_item_id or entry.sponsorship_id:
            return self._automatic_entry_error()
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        entry = self.get_object()
        if entry.order_item_id or entry.sponsorship_id:
            return self._automatic_entry_error()
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['post'])
    def recalculate_sales(self, request):
        """Rebuild sale entries from confirmed orders. Pass {"refresh": true} to apply current product values."""
        refresh = str(request.data.get('refresh', '')).lower() in ('1', 'true', 'yes')
        return Response(rebuild_sales_impact(refresh=refresh))

    @action(detail=False, methods=['get'])
    def export(self, request):
        """Download the (filtered) log as CSV."""
        qs = self.filter_queryset(self.get_queryset())
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="impact-log.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date', 'Source', 'Title', 'Plastic type', 'Plastic (kg)', 'CO2 saved (kg)',
                         'Water saved (L)', 'Items', 'People engaged', 'Product', 'Zone', 'Notes'])
        for e in qs:
            writer.writerow([e.date, e.get_source_display(), e.title, e.get_plastic_type_display(),
                             e.plastic_kg, e.co2_saved_kg, e.water_saved_liters, e.items_count,
                             e.people_engaged, e.product.name if e.product else '',
                             e.zone.name if e.zone else '', e.notes])
        return response


class ImpactSummaryView(APIView):
    """Aggregated impact for a period. Public; staff also get sales breakdowns."""
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            start = _parse_date(request.query_params.get('start'), 'start')
            end = _parse_date(request.query_params.get('end'), 'end')
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        if start and end and start > end:
            return Response({'error': 'start must be before end'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(compute_summary(start, end, include_private=has_any_permission(request.user, 'view_analytics', 'create_reports', 'view_reports')))

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all().order_by('date')
    serializer_class = EventSerializer
    permission_classes = [require('manage_community')]

    def get_permissions(self):
        # Visitors can browse events and register; managing events is staff-only
        if self.action in ('list', 'retrieve', 'register'):
            return [AllowAny()]
        return [require('manage_community')()]

    def get_queryset(self):
        qs = Event.objects.all().order_by('date')
        if not has_any_permission(self.request.user, 'manage_community'):
            qs = qs.filter(is_active=True)
        return qs

    @action(detail=True, methods=['post'])
    def register(self, request, pk=None):
        event = self.get_object()
        serializer = EventRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            # Check if spots are available
            if event.spots_filled >= event.spots_available:
                return Response({'error': 'No spots available'}, status=status.HTTP_400_BAD_REQUEST)

            # Create registration
            serializer.save(event=event, user=request.user if request.user.is_authenticated else None)

            # Update spots filled
            event.spots_filled += 1
            event.save()

            return Response({'message': 'Registered successfully', 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], permission_classes=[require('manage_community')])
    def registrations(self, request, pk=None):
        event = self.get_object()
        registrations = EventRegistration.objects.filter(event=event)
        serializer = EventRegistrationSerializer(registrations, many=True)
        return Response(serializer.data)

class NewsletterViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def subscribe(self, request):
        serializer = NewsletterSubscriptionSerializer(data=request.data)
        if serializer.is_valid():
            NewsletterSubscription.objects.get_or_create(email=serializer.validated_data['email'])
            return Response({'message': 'Subscribed successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BulkRFQViewSet(viewsets.ModelViewSet):
    queryset = BulkRFQ.objects.all()
    serializer_class = BulkRFQSerializer
    permission_classes = [IsAuthenticatedOrCreateOnly]

    def get_permissions(self):
        # Anyone can send a bulk request; reviewing them is for community staff
        if self.action == 'create':
            return [AllowAny()]
        return [require('manage_community')()]

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'RFQ submitted successfully', 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EventRegistrationViewSet(viewsets.ModelViewSet):
    queryset = EventRegistration.objects.all()
    serializer_class = EventRegistrationSerializer
    permission_classes = [require('manage_community')]

class SponsorshipSubmitThrottle(AnonRateThrottle):
    rate = '20/hour'


class SponsorshipViewSet(viewsets.ModelViewSet):
    """Anyone can submit a sponsorship pledge; only staff can see and manage them."""
    queryset = Sponsorship.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'item_type', 'sponsor_type']
    search_fields = ['reference', 'sponsor_name', 'organization_name', 'sponsor_email', 'sponsor_phone']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ('create', 'options_info'):
            return [AllowAny()]
        return [require('manage_community', 'manage_payments')()]

    def get_throttles(self):
        if self.action == 'create':
            return [SponsorshipSubmitThrottle()]
        return super().get_throttles()

    def get_authenticators(self):
        # The public form must work even if the browser holds an expired token.
        # self.action isn't set yet when DRF asks for authenticators, so read it from the action map.
        action_map = getattr(self, 'action_map', None) or {}
        request = getattr(self, 'request', None)
        action = action_map.get(request.method.lower()) if request is not None else None
        if action in ('create', 'options_info'):
            return []
        return super().get_authenticators()

    def get_serializer_class(self):
        if self.action == 'create':
            return SponsorshipSerializer
        return SponsorshipAdminSerializer

    @action(detail=False, methods=['get'], url_path='options')
    def options_info(self, request):
        """What can be sponsored and for how much, so the form never hardcodes prices."""
        return Response({
            'items': [
                {
                    'item_type': key,
                    'unit_price': float(cfg['unit_price']),
                    'currency': cfg['currency'],
                    'plastic_kg': float(cfg['plastic_kg']),
                    'description': cfg['description'],
                }
                for key, cfg in SPONSORSHIP_ITEMS.items()
            ],
        })

    @action(detail=False, methods=['get'])
    def stats(self, request):
        return Response(sponsorship_stats())


class CustomerImpactView(APIView):
    """The signed-in customer's own impact, with a share token for their public impact card."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(customer_impact(request.user, include_private=True))


class SharedImpactView(APIView):
    """Public impact card for a share link. Shows only first name + last initial and totals."""
    permission_classes = [AllowAny]
    authentication_classes = []  # a stale token in the browser must not turn this into a 401

    def get(self, request, token):
        user = user_from_share_token(token)
        if user is None:
            return Response({'error': 'Impact card not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(customer_impact(user, include_private=False))


class VolunteerOpportunityViewSet(viewsets.ModelViewSet):
    """'Ways to volunteer' cards on the Get Involved page. Public read; Manage Community staff edit."""
    serializer_class = VolunteerOpportunitySerializer
    permission_classes = [require('manage_community', read_public=True)]
    pagination_class = None

    def get_queryset(self):
        qs = VolunteerOpportunity.objects.all()
        if not has_any_permission(self.request.user, 'manage_community'):
            qs = qs.filter(is_active=True)
        return qs
