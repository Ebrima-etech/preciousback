from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import ImpactMetric, CollectionZone, Event, EventRegistration, NewsletterSubscription, BulkRFQ, Sponsorship
from .serializers import (ImpactMetricSerializer, CollectionZoneSerializer, EventSerializer, EventRegistrationSerializer,
                          NewsletterSubscriptionSerializer, BulkRFQSerializer, SponsorshipSerializer)

class ImpactMetricViewSet(viewsets.ModelViewSet):
    queryset = ImpactMetric.objects.all()
    serializer_class = ImpactMetricSerializer
    permission_classes = [IsAuthenticated]

class CollectionZoneViewSet(viewsets.ModelViewSet):
    queryset = CollectionZone.objects.all()
    serializer_class = CollectionZoneSerializer
    permission_classes = [IsAuthenticated]

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all().order_by('date')
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

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

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
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
    permission_classes = [AllowAny]

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'RFQ submitted successfully', 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EventRegistrationViewSet(viewsets.ModelViewSet):
    queryset = EventRegistration.objects.all()
    serializer_class = EventRegistrationSerializer
    permission_classes = [IsAuthenticated]

class SponsorshipViewSet(viewsets.ModelViewSet):
    queryset = Sponsorship.objects.all()
    serializer_class = SponsorshipSerializer
    permission_classes = [AllowAny]
