from rest_framework import serializers
from .models import CoinPrice, Snapshot


class CoinPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoinPrice
        fields = [
            'name',
            'symbol',
            'price',
            'price_change_24h',
            'market_cap',
            'total_volume'
        ]


class SnapshotSerializer(serializers.ModelSerializer):
    prices_count = serializers.SerializerMethodField()

    def get_prices_count(self, obj):
        return obj.prices.count()

    class Meta:
        model = Snapshot
        fields = ['id', 'created_at', 'source', 'prices_count']


class SnapshotDetailSerializer(SnapshotSerializer):
    prices = CoinPriceSerializer(many=True, read_only=True)

    class Meta(SnapshotSerializer.Meta):
        fields = SnapshotSerializer.Meta.fields + ['prices']


class CoinHistorySerializer(CoinPriceSerializer):
    snapshot_source = serializers.CharField(source='snapshot.source', read_only=True)
    snapshot_created_at = serializers.DateTimeField(source='snapshot.created_at', read_only=True)

    class Meta(CoinPriceSerializer.Meta):
        fields = CoinPriceSerializer.Meta.fields + ['snapshot_source',
                                                    'snapshot_created_at']