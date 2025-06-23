# /app/rent/views.py

from io import BytesIO
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.core.mail import EmailMessage
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.db import transaction
from django.urls import reverse
from django.contrib import messages
from .models import Rent
from customers.models import Customers, CustomerPayments, CustomerBalance
from devices.models import Devices
from base.models import Countries
from imports.models import Imports
from products.models import Products
from purchases.models import Purchases
from stock.models import Stock
from urllib.parse import urlencode
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from decimal import Decimal, InvalidOperation
from sales.utils  import generate_quotation_number
import logging
import base64
import random

def rent_new(request):
    if request.method == 'POST':
        serial_number = request.POST.get('serial_number')
        current_hours = Decimal(request.POST.get('current_hours', '0'))
        last_reported_hours = Decimal(request.POST.get('last_reported_hours', '0'))
        last_report_date = request.POST.get('last_report_date')
        hourly_rate = Decimal(request.POST.get('hourly_rate', '0'))
        rental_percentage = Decimal(request.POST.get('rental_percentage', '0'))
        total_amount_due = Decimal(request.POST.get('total_amount_due', '0'))

        rent = Rent(
            serial_number=serial_number,
            current_hours=current_hours,
            last_reported_hours=last_reported_hours,
            last_report_date=last_report_date if last_report_date else None,
            hourly_rate=hourly_rate,
            rental_percentage=rental_percentage,
            total_amount_due=total_amount_due
        )
        rent.save()

        return redirect('sales:rent_list')

    return render(request, 'rent_new.html', {})

def rent_update(request, rent_id):
    try:
        rent = Rent.objects.get(rent_id=rent_id)
    except Rent.DoesNotExist:
        return render(request, 'rent_update.html', {
            'error': 'Rent record not found.'
        })

    if request.method == 'POST':
        serial_number = request.POST.get('serial_number')
        current_hours = Decimal(request.POST.get('current_hours', '0'))
        last_reported_hours = Decimal(request.POST.get('last_reported_hours', '0'))
        last_report_date = request.POST.get('last_report_date')
        hourly_rate = Decimal(request.POST.get('hourly_rate', '0'))
        rental_percentage = Decimal(request.POST.get('rental_percentage', '0'))
        total_amount_due = Decimal(request.POST.get('total_amount_due', '0'))

        rent.serial_number = serial_number
        rent.current_hours = current_hours
        rent.last_reported_hours = last_reported_hours
        rent.last_report_date = last_report_date if last_report_date else None
        rent.hourly_rate = hourly_rate
        rent.rental_percentage = rental_percentage
        rent.total_amount_due = total_amount_due
        rent.save()

        return redirect('sales:rent_list')

    return render(request, 'rent_update.html', {'rent': rent})

def rent_list(request):
    rents = Rent.objects.all()
    return render(request, 'rent_list.html', {
        'rents': rents
    })

def rent_edit(request):
    if request.method == 'POST':
        if 'update_rent' in request.POST:
            rent_id = request.POST.get('rent_id')
            serial_number = request.POST.get('serial_number')
            current_hours = Decimal(request.POST.get('current_hours', '0'))
            last_reported_hours = Decimal(request.POST.get('last_reported_hours', '0'))
            last_report_date = request.POST.get('last_report_date')
            hourly_rate = Decimal(request.POST.get('hourly_rate', '0'))
            rental_percentage = Decimal(request.POST.get('rental_percentage', '0'))
            total_amount_due = Decimal(request.POST.get('total_amount_due', '0'))

            try:
                rent = Rent.objects.get(rent_id=rent_id)
            except Rent.DoesNotExist:
                return render(request, 'rent_edit.html', {
                    'error': 'Rent contract not found.',
                    'rents': Rent.objects.all()
                })

            rent.serial_number = serial_number
            rent.current_hours = current_hours
            rent.last_reported_hours = last_reported_hours
            rent.last_report_date = last_report_date if last_report_date else None
            rent.hourly_rate = hourly_rate
            rent.rental_percentage = rental_percentage
            rent.total_amount_due = total_amount_due
            rent.save()

            return redirect('sales:rent_list')

        elif 'delete_rent' in request.POST:
            rent_id = request.POST.get('rent_id')
            try:
                rent = Rent.objects.get(rent_id=rent_id)
                rent.delete()
            except Rent.DoesNotExist:
                return render(request, 'rent_edit.html', {
                    'error': 'Rent contract not found.',
                    'rents': Rent.objects.all()
                })
            return redirect('sales:rent_list')

    rent_id = request.GET.get('rent_id')
    if not rent_id:
        return render(request, 'rent_edit.html', {
            'error': 'Please select a rent contract to edit.',
            'rents': Rent.objects.all()
        })

    try:
        rent = Rent.objects.get(rent_id=rent_id)
    except Rent.DoesNotExist:
        return render(request, 'rent_edit.html', {
            'error': 'Rent contract not found.',
            'rents': Rent.objects.all()
        })

    return render(request, 'rent_edit.html', {
        'rent': rent,
        'rents': Rent.objects.all()
    })

