from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.throttling import UserRateThrottle
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from django.shortcuts import get_object_or_404

import stripe

from projects.models import Project
from projects.serializers import ProjectSerializer

from server.settings import get_secret

stripe.api_key = get_secret('STRIPE_KEY', None)

STRIPE_PRODUCTS = {
    'light': get_secret('STRIPE_LIGHT_PLAN', None),
    'light_annual': get_secret('STRIPE_LIGHT_ANNUAL_PLAN', None),
    'production': get_secret('STRIPE_PRODUCTION_PLAN', None),
    'production_annual': get_secret('STRIPE_PRODUCTION_ANNUAL_PLAN', None),
    'professional': get_secret('STRIPE_PROFESSIONAL_PLAN', None),
    'professional_annual': get_secret('STRIPE_PROFESSIONAL_ANNUAL_PLAN', None)
}


class CreateSubscription(APIView):
    throttle_classes = [UserRateThrottle]
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def patch(self, request, project_id):
        plan = request.data.get('plan', False)
        payment_method = request.data.get('payment_method', False)
        project = get_object_or_404(Project, owner=request.user, pk=project_id)

        quantity = 1000
        if request.data.get('quantity', False) and isinstance(request.data.get('quantity', False), int):
            # Add the needed multiplier, if the quantity is under 1000
            quantity = request.data['quantity'] if request.data['quantity'] > 1000 else request.data['quantity'] * 1000

        if not payment_method or not plan:
            return Response(
                {'message': 'You need a payment method and plan!'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            customer = stripe.Customer.create(
                payment_method=payment_method,
                email=request.user.email,
                invoice_settings={'default_payment_method': payment_method},
            )
        except stripe.error.CardError as error:
            message = error.message if error.message else 'We cannot process your C.C. please contact support via chat'
            return Response({'message': message}, status=status.HTTP_400_BAD_REQUEST)

        if project.subscription_id is not None:
            stripe.Subscription.delete(project.subscription_id)

        subscription = stripe.Subscription.create(
            customer=customer['id'],
            items=[{
                'plan': STRIPE_PRODUCTS[plan],
                'quantity': quantity
            }],
            expand=['latest_invoice.payment_intent'],
            default_tax_rates=[get_secret('STRIPE_TAX_RATE', None)],
            promotion_code=get_secret('STRIPE_ANNUAL_PROMO', None) if 'annual' in plan else None,
        )

        try:
            if subscription['latest_invoice']['payment_intent']['charges']['data'][0]['payment_method_details']['card']['checks']['cvc_check'] != 'pass':
                return Response({'message': "Your C.C. info is incorrect!"}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError:
            pass

        project.subscription_id = subscription['id']
        project.monthly_users = quantity
        project.plan_type = plan
        project.apply_plan = True
        project.is_active = True
        project.save()

        return Response(subscription['latest_invoice']['payment_intent'], status=status.HTTP_200_OK)

    def delete(self, request, project_id):
        project = get_object_or_404(Project, owner=request.user, pk=project_id)

        try:
            stripe.Subscription.delete(project.subscription_id)
        except stripe.error.InvalidRequestError as error:
            print('Delete Subscription Error: ' + str(error))

        project.subscription_id = None
        project.plan_type = 'basic'
        project.save()

        serializer = ProjectSerializer(project, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)
