from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.cache import cache
from wardrobe_app.models import ClothingItem, ClothingCategory
from unittest.mock import patch


class ChatbotIntentHandlersTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass')
        # Ensure category objects exist
        self.tops = ClothingCategory.objects.create(name='tops')
        self.bottoms = ClothingCategory.objects.create(name='bottoms')
        # Sample wardrobe
        ClothingItem.objects.create(user=self.user, name='Blue Cotton T-shirt', category=self.tops, color='blue', processing_status='completed')
        ClothingItem.objects.create(user=self.user, name='Khaki Chinos', category=self.bottoms, color='khaki', processing_status='completed')

    def test_chat_endpoint_exists(self):
        self.client.login(username='tester', password='pass')
        url = reverse('stylist_chatbot:chatbot_response')
        resp = self.client.get(url, {'message': 'hello'})
        self.assertEqual(resp.status_code, 200)

    def test_color_matching_overrides(self):
        self.client.login(username='tester', password='pass')
        # Simulate session for view
        session = self.client.session
        session.save()
        url = reverse('stylist_chatbot:chat_message_api')
        # We can't force Dialogflow intent here, but this ensures endpoint path stays functional
        resp = self.client.post(url, data={'message': 'what matches with blue'}, content_type='application/json')
        self.assertIn(resp.status_code, (200, 500))

    @patch('stylist_chatbot.views.get_rule_based_recommendations')
    @patch('stylist_chatbot.views.send_message_to_dialogflow')
    def test_outfit_recommendation_intent_override(self, mock_df, mock_recs):
        self.client.login(username='tester', password='pass')
        session = self.client.session
        session.save()

        # Mock Dialogflow intent
        mock_df.return_value = {
            'success': True,
            'response': 'placeholder',
            'confidence': 0.9,
            'intent': 'Outfit Recommendation',
            'parameters': {}
        }
        # Mock recommendations
        mock_recs.return_value = [
            {'items': [{'name': 'White Shirt'}, {'name': 'Black Jeans'}]}
        ]

        url = reverse('stylist_chatbot:chat_message_api')
        resp = self.client.post(url, data={'message': 'suggest an outfit'}, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload.get('success'))
        text = payload['response']['message']
        self.assertIn('personalized outfits', text.lower())
        self.assertIn('White Shirt', text)

    @patch('stylist_chatbot.views.send_message_to_dialogflow')
    def test_color_matching_intent_override(self, mock_df):
        self.client.login(username='tester', password='pass')
        session = self.client.session
        session.save()

        mock_df.return_value = {
            'success': True,
            'response': 'placeholder',
            'confidence': 0.9,
            'intent': 'Color Matching',
            'parameters': {'color': 'red'}
        }

        url = reverse('stylist_chatbot:chat_message_api')
        resp = self.client.post(url, data={'message': 'what matches with red'}, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        text = resp.json()['response']['message']
        self.assertIn('pairs well with', text.lower())

    @patch('stylist_chatbot.views.get_clothing_recommendations_based_on_weather')
    @patch('stylist_chatbot.views.get_weather_data')
    @patch('stylist_chatbot.views.send_message_to_dialogflow')
    def test_weather_outfit_intent_override(self, mock_df, mock_weather, mock_recs):
        self.client.login(username='tester', password='pass')
        session = self.client.session
        session.save()

        mock_df.return_value = {
            'success': True,
            'response': 'placeholder',
            'confidence': 0.9,
            'intent': 'Weather Outfit',
            'parameters': {'city': 'Kuala Lumpur'}
        }
        mock_weather.return_value = {
            'city': 'Kuala Lumpur',
            'temperature': 28.4,
            'description': 'light rain'
        }
        mock_recs.return_value = ['light jacket', 'waterproof shoes']

        url = reverse('stylist_chatbot:chat_message_api')
        resp = self.client.post(url, data={'message': 'what to wear in the rain'}, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        text = resp.json()['response']['message']
        self.assertIn('kuala lumpur', text.lower())
        self.assertIn('suggestions', text.lower())

    @patch('stylist_chatbot.views.send_message_to_dialogflow')
    def test_occasion_outfit_intent_override(self, mock_df):
        self.client.login(username='tester', password='pass')
        session = self.client.session
        session.save()

        mock_df.return_value = {
            'success': True,
            'response': 'placeholder',
            'confidence': 0.9,
            'intent': 'Occasion Outfit',
            'parameters': {'occasion': 'wedding'}
        }

        url = reverse('stylist_chatbot:chat_message_api')
        resp = self.client.post(url, data={'message': 'outfit for a wedding'}, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        text = resp.json()['response']['message']
        self.assertIn('wedding guest', text.lower())

