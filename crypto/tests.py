from rest_framework import status
from rest_framework.test import APITestCase
from .models import Snapshot, CoinPrice


class SnapShotApiTests(APITestCase):
    def setUp(self):
        for _ in range(12):
            Snapshot.objects.create(source='test')

    def test_list_is_paginated(self):
        response = self.client.get('/api/snapshots/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 12)
        self.assertEqual(len(response.data['results']), 10)


class CoinApiTests(APITestCase):

    def setUp(self):
        self.snapshot = Snapshot.objects.create(source='test')
        CoinPrice.objects.create(
            snapshot=self.snapshot,
            name ='Bitcoin',
            symbol='BTC',
            price=1,
            market_cap=1,
            total_volume=1,
            )

        CoinPrice.objects.create(
            snapshot=self.snapshot,
            name='Ethereum',
            symbol='ETH',
            price=1,
            market_cap=1,
            total_volume=1,
            )

    def test_filter_by_symbol(self):
        response = self.client.get('/api/coins/?symbol=BTC')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_filter_is_case_insensitive(self):
        response = self.client.get('/api/coins/?symbol=btc')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_detail_contains_prices(self):
        response = self.client.get(f'/api/snapshots/{self.snapshot.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['prices']), 2)

