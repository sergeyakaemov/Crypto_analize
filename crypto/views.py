from rest_framework import viewsets
from .models import Snapshot
from .serializers import SnapshotSerializer, SnapshotDetailSerializer


class SnapshotViewSet(viewsets.ModelViewSet):
    queryset = Snapshot.objects.all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SnapshotDetailSerializer
        return SnapshotSerializer
