# /app/leasing/views.py

from io import BytesIO
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.core.mail import EmailMessage
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.db import transaction
from django.urls import reverse
from django.contrib import messages
from .models import Leasing
from customers.models import Customers, CustomerPayments, CustomerBalance
from devices.models import Devices
from payments.models import PaymentCode 
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


def leasing_new(request):
    if request.method == 'POST':
        # Извлечение данных из формы
        customer_id = request.POST.get('customer_id', '').strip()
        contract_no = request.POST.get('contract_no', '').strip()
        product_id = request.POST.get('product_id', '').strip()
        serial_number = request.POST.get('serial_number', '').strip()
        start_date = request.POST.get('start_date', '').strip()
        sell_price = Decimal(request.POST.get('sell_price', '0'))
        vat_rate = Decimal(request.POST.get('vat_rate', '19'))
        sale_vat = Decimal(request.POST.get('sale_vat', '0'))
        purchase_vat = Decimal(request.POST.get('purchase_vat', '0'))
        vat_to_pay = Decimal(request.POST.get('vat_to_pay', '0'))
        first_installment = Decimal(request.POST.get('first_installment', '0'))
        number_of_installments = int(request.POST.get('number_of_installments', 1))
        installment_amount = Decimal(request.POST.get('installment_amount', '0'))
        already_paid = Decimal(request.POST.get('already_paid', '0'))
        balance_to_pay = Decimal(request.POST.get('balance_to_pay', '0'))
        agent_commission_rate = Decimal(request.POST.get('agent_commission_rate', '0'))
        agent_commission = Decimal(request.POST.get('agent_commission', '0'))
        profit_wo_vat = Decimal(request.POST.get('profit_wo_vat', '0'))

        # Проверка обязательных полей
        if not all([customer_id, contract_no, product_id, start_date]):
            return render(request, 'leasing_new.html', {
                'error': 'Все обязательные поля (Клиент, Номер контракта, Продукт, Дата начала) должны быть заполнены.',
                'customers': Customers.objects.all()
            })

        # Проверяем customer_id и product_id
        if not customer_id or not product_id:
            return render(request, 'leasing_new.html', {
                'error': 'Пожалуйста, выберите клиента и продукт через автозаполнение.',
                'customers': Customers.objects.all()
            })

        # Проверка уникальности contract_no
        if Leasing.objects.filter(contract_no=contract_no).exists():
            return render(request, 'leasing_new.html', {
                'error': f'Контракт с номером {contract_no} уже существует.',
                'customers': Customers.objects.all()
            })

        # Получение объектов customer и product
        try:
            customer = Customers.objects.get(customer_id=customer_id)
            product = Products.objects.get(id=product_id)
        except Customers.DoesNotExist:
            return render(request, 'leasing_new.html', {
                'error': 'Клиент не найден.',
                'customers': Customers.objects.all()
            })
        except Products.DoesNotExist:
            return render(request, 'leasing_new.html', {
                'error': 'Продукт не найден.',
                'customers': Customers.objects.all()
            })

        # Расчёт stock_price для profit_wo_vat
        stock_price = Decimal('0')
        if serial_number:
            try:
                purchase = Purchases.objects.get(serial_number=serial_number)
                import_obj = Imports.objects.get(invoice=purchase.invoice)
                stock = Stock.objects.get(product_id=product.id, import_id=import_obj.import_id)
                stock_price = stock.stock_price
            except (Purchases.DoesNotExist, Imports.DoesNotExist, Stock.DoesNotExist):
                return render(request, 'leasing_new.html', {
                    'error': 'Не удалось рассчитать прибыль: информация о запасах не найдена.',
                    'customers': Customers.objects.all()
                })

        profit_wo_vat = sell_price - stock_price - agent_commission

        # Рассчитываем sale_vat на основе фиксированного vat_rate
        sale_vat = sell_price * (vat_rate / 100)

        # Создание объекта Leasing
        try:
            leasing = Leasing(
                contract_no=contract_no,
                customer=customer,
                product=product,
                serial_number=serial_number if serial_number else None,
                start_date=start_date,
                sell_price=sell_price,
                vat_rate=vat_rate,
                sale_vat=sale_vat,
                purchase_vat=purchase_vat,
                vat_to_pay=vat_to_pay,
                first_installment=first_installment,
                number_of_installments=number_of_installments,
                installment_amount=installment_amount,
                already_paid=already_paid,
                balance_to_pay=balance_to_pay,
                agent_commission_rate=agent_commission_rate,
                agent_commission=agent_commission,
                profit_wo_vat=profit_wo_vat,
                last_installment_number=0
            )
            leasing.date_of_payment = timezone.now().date()
            leasing.paid = first_installment
            leasing.contract_file = ""
            leasing.save()
        except Exception as e:
            return render(request, 'leasing_new.html', {
                'error': f'Ошибка при создании лизинга: {str(e)}',
                'customers': Customers.objects.all()
            })

        # Создание записи в CustomerPayments
        try:
            CustomerPayments.objects.create(
                customer=customer,
                amount_paid=first_installment,
                vat_amount=sale_vat * (first_installment / (sell_price + sale_vat)),
                payment_date=timezone.now(),
                payment_details=f"Первый взнос по лизинговому контракту {contract_no}",
                transaction_type='LEASING',
                transaction_id=contract_no,
                installment_number=0,
                product_type='DEVICE'
            )
        except Exception as e:
            leasing.delete()
            return render(request, 'leasing_new.html', {
                'error': f'Ошибка при создании платежа клиента: {str(e)}',
                'customers': Customers.objects.all()
            })

        # Создание или обновление CustomerBalance
        try:
            CustomerBalance.objects.update_or_create(
                customer=customer,
                transaction_type='LEASING',
                transaction_id=contract_no,
                defaults={
                    'total_amount': sell_price + sale_vat,
                    'already_paid': already_paid,
                    'balance_to_pay': balance_to_pay,
                    'vat_amount': sale_vat,
                    'created_at': timezone.now(),
                    'description': f"Баланс лизинга по контракту {contract_no}",
                    'product_type': 'DEVICE'
                }
            )
        except Exception as e:
            leasing.delete()
            CustomerPayments.objects.filter(transaction_type='LEASING', transaction_id=contract_no).delete()
            return render(request, 'leasing_new.html', {
                'error': f'Ошибка при обновлении баланса клиента: {str(e)}',
                'customers': Customers.objects.all()
            })

        # Обновление устройства, если указан serial_number
        if serial_number:
            try:
                device = Devices.objects.get(serial_number=serial_number)
                Devices.objects.filter(serial_number=serial_number).update(
                    customer_id=customer,
                    sale_date=start_date
                )
            except Devices.DoesNotExist:
                leasing.delete()
                CustomerPayments.objects.filter(transaction_type='LEASING', transaction_id=contract_no).delete()
                CustomerBalance.objects.filter(transaction_type='LEASING', transaction_id=contract_no).delete()
                return render(request, 'leasing_new.html', {
                    'error': f'Устройство с серийным номером {serial_number} не найдено.',
                    'customers': Customers.objects.all()
                })

        return redirect('sales:leasing_list')

    customers = Customers.objects.all()
    return render(request, 'leasing_new.html', {
        'customers': customers
    })

def leasing_list(request):
    customer_id = request.GET.get('customer_hidden', '')
    customer_name = request.GET.get('customer', '')

    leasings = Leasing.objects.all().select_related('customer')
    if customer_id:
        try:
            customer_id = int(customer_id)
            leasings = leasings.filter(customer_id=customer_id)
        except ValueError:
            leasings = Leasing.objects.none()

    return render(request, 'leasing_list.html', {
        'leasings': leasings,
        'customer': customer_name,
        'customer_hidden': customer_id
    })

def leasing_delete(request, contract_no):
    if request.method == 'POST':
        try:
            leasing = Leasing.objects.get(contract_no=contract_no)
            CustomerPayments.objects.filter(transaction_type='LEASING', transaction_id=contract_no).delete()
            CustomerBalance.objects.filter(transaction_type='LEASING', transaction_id=contract_no).delete()
            leasing.delete()
            if leasing.serial_number:
                Devices.objects.filter(serial_number=leasing.serial_number).update(
                    customer_id=None,
                    sale_date=None
                )
        except Leasing.DoesNotExist:
            pass
    return redirect('sales:leasing_list')

def leasing_edit(request):
    leasings = Leasing.objects.all().select_related('customer')
    customers = Customers.objects.all()

    selected_contract_no = request.GET.get('contract_no', '')
    leasing = None
    if selected_contract_no:
        try:
            leasing = Leasing.objects.get(contract_no=selected_contract_no)
        except Leasing.DoesNotExist:
            pass

    if request.method == 'POST':
        if 'update_leasing' in request.POST:
            contract_no = request.POST.get('contract_no')
            customer_id = request.POST.get('customer_id')
            serial_number = request.POST.get('serial_number', '').strip()
            start_date = request.POST.get('start_date')
            sell_price = Decimal(request.POST.get('sell_price', '0'))
            vat_rate = Decimal('19')
            sale_vat = Decimal(request.POST.get('sale_vat', '0'))
            purchase_vat = Decimal(request.POST.get('purchase_vat', '0'))
            vat_to_pay = Decimal(request.POST.get('vat_to_pay', '0'))
            first_installment = Decimal(request.POST.get('first_installment', '0'))
            number_of_installments = int(request.POST.get('number_of_installments', 1))
            installment_amount = Decimal(request.POST.get('installment_amount', '0'))
            already_paid = Decimal(request.POST.get('already_paid', '0'))
            balance_to_pay = Decimal(request.POST.get('balance_to_pay', '0'))
            agent_commission_rate = Decimal(request.POST.get('agent_commission_rate', '0'))
            agent_commission = Decimal(request.POST.get('agent_commission', '0'))
            profit_wo_vat = Decimal(request.POST.get('profit_wo_vat', '0'))

            # Проверка обязательных полей
            if not all([customer_id, contract_no, start_date]):
                return render(request, 'leasing_edit.html', {
                    'error': 'Все обязательные поля должны быть заполнены.',
                    'leasings': leasings,
                    'customers': customers,
                    'selected_contract_no': selected_contract_no,
                    'leasing': leasing
                })

            try:
                customer = Customers.objects.get(customer_id=customer_id)
            except Customers.DoesNotExist:
                return render(request, 'leasing_edit.html', {
                    'error': 'Клиент не найден.',
                    'leasings': leasings,
                    'customers': customers,
                    'selected_contract_no': selected_contract_no,
                    'leasing': leasing
                })

            try:
                leasing = Leasing.objects.get(contract_no=selected_contract_no)
                leasing.contract_no = contract_no
                leasing.customer = customer
                leasing.serial_number = serial_number if serial_number else None
                leasing.start_date = start_date
                leasing.sell_price = sell_price
                leasing.vat_rate = vat_rate
                leasing.sale_vat = sale_vat
                leasing.purchase_vat = purchase_vat
                leasing.vat_to_pay = vat_to_pay
                leasing.first_installment = first_installment
                leasing.number_of_installments = number_of_installments
                leasing.installment_amount = installment_amount
                leasing.already_paid = already_paid
                leasing.balance_to_pay = balance_to_pay
                leasing.agent_commission_rate = agent_commission_rate
                leasing.agent_commission = agent_commission
                leasing.profit_wo_vat = profit_wo_vat
                leasing.save()

                # Обновляем связанные записи
                CustomerBalance.objects.filter(transaction_type='LEASING', transaction_id=selected_contract_no).update(
                    customer=customer,
                    total_amount=sell_price + sale_vat,
                    already_paid=already_paid,
                    balance_to_pay=balance_to_pay,
                    vat_amount=sale_vat,
                    description=f"Баланс лизинга по контракту {contract_no}",
                    product_type='DEVICE'
                )

                if serial_number:
                    try:
                        device = Devices.objects.get(serial_number=serial_number)
                        Devices.objects.filter(serial_number=serial_number).update(
                            customer_id=customer,
                            sale_date=start_date
                        )
                    except Devices.DoesNotExist:
                        return render(request, 'leasing_edit.html', {
                            'error': f'Устройство с серийным номером {serial_number} не найдено.',
                            'leasings': leasings,
                            'customers': customers,
                            'selected_contract_no': selected_contract_no,
                            'leasing': leasing
                        })

                return redirect('sales:leasing_list')
            except Leasing.DoesNotExist:
                return render(request, 'leasing_edit.html', {
                    'error': 'Лизинг не найден.',
                    'leasings': leasings,
                    'customers': customers,
                    'selected_contract_no': selected_contract_no,
                    'leasing': leasing
                })

        elif 'delete_leasing' in request.POST:
            try:
                leasing = Leasing.objects.get(contract_no=selected_contract_no)
                CustomerPayments.objects.filter(transaction_type='LEASING', transaction_id=selected_contract_no).delete()
                CustomerBalance.objects.filter(transaction_type='LEASING', transaction_id=selected_contract_no).delete()
                if leasing.serial_number:
                    Devices.objects.filter(serial_number=leasing.serial_number).update(
                        customer_id=None,
                        sale_date=None
                    )
                leasing.delete()
                return redirect('sales:leasing_list')
            except Leasing.DoesNotExist:
                return render(request, 'leasing_edit.html', {
                    'error': 'Лизинг не найден.',
                    'leasings': leasings,
                    'customers': customers,
                    'selected_contract_no': selected_contract_no,
                    'leasing': leasing
                })

    return render(request, 'leasing_edit.html', {
        'leasings': leasings,
        'customers': customers,
        'selected_contract_no': selected_contract_no,
        'leasing': leasing
    })

def leasing_pay(request):
    leasings = Leasing.objects.all().select_related('customer')
    contract_no = request.GET.get('contract_no', '')
    leasing = None
    payment_history = None

    if contract_no:
        try:
            leasing = Leasing.objects.get(contract_no=contract_no)
            payment_history = CustomerPayments.objects.filter(
                transaction_type='LEASING',
                transaction_id=contract_no
            ).order_by('-payment_date')
        except Leasing.DoesNotExist:
            pass

    if request.method == 'POST':
        payment_amount = Decimal(request.POST.get('payment_amount', '0'))
        contract_no = request.POST.get('contract_no')

        try:
            leasing = Leasing.objects.get(contract_no=contract_no)
        except Leasing.DoesNotExist:
            return render(request, 'leasing_pay.html', {
                'error': 'Лизинг не найден.',
                'leasings': leasings,
                'contract_no': contract_no,
                'leasing': leasing,
                'payment_history': payment_history
            })

        leasing.already_paid += payment_amount
        leasing.balance_to_pay -= payment_amount
        leasing.last_installment_number += 1
        leasing.save()

        CustomerPayments.objects.create(
            customer=leasing.customer,
            amount_paid=payment_amount,
            vat_amount=leasing.sale_vat * (payment_amount / (leasing.sell_price + leasing.sale_vat)),
            payment_date=timezone.now(),
            payment_details=f"Платёж по лизинговому контракту {contract_no}, взнос #{leasing.last_installment_number}",
            transaction_type='LEASING',
            transaction_id=contract_no,
            installment_number=leasing.last_installment_number,
            product_type='DEVICE'
        )

        CustomerBalance.objects.update_or_create(
            customer=leasing.customer,
            transaction_type='LEASING',
            transaction_id=contract_no,
            defaults={
                'total_amount': leasing.sell_price + leasing.sale_vat,
                'already_paid': leasing.already_paid,
                'balance_to_pay': leasing.balance_to_pay,
                'vat_amount': leasing.sale_vat,
                'created_at': timezone.now(),
                'description': f"Баланс лизинга по контракту {contract_no}",
                'product_type': 'DEVICE'
            }
        )

        return redirect('sales:leasing_list')

    return render(request, 'leasing_pay.html', {
        'leasings': leasings,
        'contract_no': contract_no,
        'leasing': leasing,
        'payment_history': payment_history
    })