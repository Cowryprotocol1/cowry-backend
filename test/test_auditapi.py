# from rest_framework.test import APITestCase
from rest_framework import status
from model_bakery import baker
from test_setup import TokenTable, TestSetUpClass
from rest_framework.test import APITestCase

from rest_framework import status
from unittest import mock

class AuditProtocolTest(APITestCase):
    @mock.patch('Api.views.protocolAudit')
    @mock.patch('Api.views.protocolAssetTotalSupply')
    def test_audit_protocol(self, mock_protocolAssetTotalSupply, mock_merchants):
        # Set up the mock response for the protocolAssetTotalSupply function
        mock_protocolAssetTotalSupply.return_value = 100000
        mock_merchants.return_value = [{'merchant_id__blockchainAddress': 'GBZGNJFRXS2AQ6GQ2QNSRFTA54W6Z36KMTKSJ35GEWBXH4RWJLULLBVH', 'total_staked_usdc': 200.0, 'exchange_rate': 722.7895855, 'total_mint_right': 130102.12539, 'pending_unclear_amt': 0.0, 'fiat_in_acct': 2900.0, 'allowed_token_left': 133002.12539}]

        # Set up the mock data for the TokenTable model

        # Send the GET request to the endpoint
        response = self.client.get('/audit_protocol')

        # Check the response status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the data in the response
        self.assertEqual(response.data['data'], mock_merchants.return_value)
        self.assertEqual(response.data['protocol_token_totalSupply'], 100000)
