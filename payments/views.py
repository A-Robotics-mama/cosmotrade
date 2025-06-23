# /app/payments/views.py
from django.http import JsonResponse
from suppliers.models import Suppliers
from customers.models import CustomersGroups
from imports.models import Imports
from purchases.models import Purchases
from payments.models import PaymentCode 
from sales.models import SalesInvoice
from leasing.models import Leasing
from rent.models import Rent
from django.db.models import Q
from base.models import Countries  
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger(__name__)

def payment_code_autocomplete(request):
    if 'term' in request.GET:
        term = request.GET.get('term')
        print(f"Payment Code autocomplete term: {term}")
        qs = PaymentCode.objects.filter(description__icontains=term)
        codes = [
            {
                'label': item.description,
                'value': item.code
            }
            for item in qs
        ]
        print(f"Payment Code autocomplete results: {codes}")
        return JsonResponse(codes, safe=False)
    print("Payment Code autocomplete: No term provided")
    return JsonResponse([], safe=False)
