# customers/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db import connection
from django.db.models import Q, Sum
from django.utils import timezone
from customers.models import Customers, CustomersGroups, CustomerBalance, CustomerPayments
from sales.models import RetailSale, SalesInvoice
from base.models import Countries
from products.models import Products
from devices.models import Devices
from suppliers.models import Suppliers
from payments.models import PaymentCode
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def customer_new(request):
    if request.method == 'POST':
        try:
            fullname = request.POST.get('fullname')
            legal_name = request.POST.get('legal_name')
            group_id = request.POST.get('group_id')
            country_iso = request.POST.get('country_iso')
            street_address = request.POST.get('street_address')
            postcode = request.POST.get('postcode')
            country_code = request.POST.get('country_code')
            landline = request.POST.get('landline') or None
            mobile = request.POST.get('mobile') or None
            email = request.POST.get('email') or None
            customer_url = request.POST.get('customer_url') or None
            birthday = request.POST.get('birthday') or None
            nameday = request.POST.get('nameday') or None
            notes = request.POST.get('notes') or None
            vat = request.POST.get('vat') or None

            customer = Customers(
                fullname=fullname,
                legal_name=legal_name,
                group_id=group_id,
                country_iso=Countries.objects.get(country_iso=country_iso) if country_iso else None,
                street_address=street_address,
                postcode=postcode,
                landline=landline,
                mobile=mobile,
                email=email,
                web=customer_url,
                birthday=birthday,
                nameday=nameday,
                notes=notes,
                vat=vat,
                credit_rating=0
            )
            customer.save()
            return redirect('customers:customer_list')
        except Exception as e:
            return render(request, 'customer_new.html', {
                'error': f"Error saving customer: {str(e)}",
                'fullname': fullname,
                'legal_name': legal_name,
                'group_id': group_id,
                'country_iso': country_iso,
                'street_address': street_address,
                'postcode': postcode,
                'country_code': country_code,
                'landline': landline,
                'mobile': mobile,
                'email': email,
                'customer_url': customer_url,
                'birthday': birthday,
                'nameday': nameday,
                'notes': notes,
                'vat': vat,
                'countries': Countries.objects.all(),
            })

    return render(request, 'customer_new.html', {
        'countries': Countries.objects.all(),
    })

def customer_edit(request):
    if request.method == 'POST':
        if 'edit' in request.POST:
            customer_id = request.POST.get('customer_id')
            if not customer_id:
                return render(request, 'customer_edit.html', {
                    'error': 'Please select a customer to edit.',
                    'customers': Customers.objects.all(),
                    'countries': Countries.objects.all(),
                })
            customer = get_object_or_404(Customers, customer_id=customer_id)
            return render(request, 'customer_edit.html', {
                'customer': customer,
                'countries': Countries.objects.all(),
            })

        elif 'update' in request.POST:
            customer_id = request.POST.get('customer_id')
            if not customer_id:
                return render(request, 'customer_edit.html', {
                    'error': 'Invalid customer ID.',
                    'customers': Customers.objects.all(),
                    'countries': Countries.objects.all(),
                })

            customer = get_object_or_404(Customers, customer_id=customer_id)

            email = request.POST.get('email') or None
            if email and '@' not in email:
                return render(request, 'customer_edit.html', {
                    'customer': customer,
                    'countries': Countries.objects.all(),
                    'error': "Email must contain '@' if provided. For example: user@domain.com"
                })

            customer.fullname = request.POST.get('fullname')
            customer.legal_name = request.POST.get('legal_name') or None
            customer.group_id = request.POST.get('group_id') or None
            customer.country_iso = Countries.objects.get(country_iso=request.POST.get('country_iso')) if request.POST.get('country_iso') else None
            customer.street_address = request.POST.get('street_address')
            customer.postcode = request.POST.get('postcode')
            customer.landline = request.POST.get('landline') or None
            customer.mobile = request.POST.get('mobile') or None
            customer.email = email
            customer.web = request.POST.get('customer_url') or None
            customer.birthday = request.POST.get('birthday') or None
            customer.nameday = request.POST.get('nameday') or None
            customer.notes = request.POST.get('notes') or None
            customer.vat = request.POST.get('vat') or None

            try:
                customer.save()
                return redirect('customers:customer_list')
            except Exception as e:
                return render(request, 'customer_edit.html', {
                    'customer': customer,
                    'countries': Countries.objects.all(),
                    'error': f"Error updating customer: {str(e)}"
                })

    fullname = request.GET.get('fullname', '')
    customers = Customers.objects.all()
    if fullname:
        customers = customers.filter(fullname__icontains=fullname)

    return render(request, 'customer_edit.html', {
        'customers': customers,
        'fullname': fullname,
        'countries': Countries.objects.all(),
    })

def customer_list(request):
    search_term = ''
    customers = Customers.objects.all().select_related('country_iso')

    if request.method == 'POST':
        search_term = request.POST.get('search_term', '').strip()
        if search_term:
            customers = customers.filter(
                Q(fullname__icontains=search_term) |
                Q(legal_name__icontains=search_term)
            )

    return render(request, 'customer_list.html', {
        'customers': customers,
        'search_term': search_term
    })

def group_autocomplete(request):
    if 'term' in request.GET:
        term = request.GET.get('term')
        print(f"Group autocomplete term: {term}")
        qs = CustomersGroups.objects.filter(group_desc__icontains=term)
        groups = [{'label': item.group_desc, 'value': item.group_id} for item in qs]
        print(f"Group autocomplete results: {groups}")
        return JsonResponse(groups, safe=False)
    print("Group autocomplete: No term provided")
    return JsonResponse([], safe=False)

# ------------------ customer_autocomplete --------------------

def customer_autocomplete(request):
    if 'term' in request.GET:
        term = request.GET.get('term')
        qs = Customers.objects.filter(
            Q(fullname__icontains=term) | Q(legal_name__icontains=term, legal_name__isnull=False)
        )
        customers = [
            {
                'label': item.legal_name if item.legal_name else item.fullname,
                'value': item.customer_id
            }
            for item in qs
        ]
        logger.info(f"Customer autocomplete term: {term}, results: {customers}")
        return JsonResponse(customers, safe=False)
    logger.warning("No term provided for customer autocomplete")
    return JsonResponse([], safe=False)

# ------------------ customer_balance_quotation -------------------

def customer_balance_quotation(request, customer_id):
    customer = get_object_or_404(Customers, customer_id=customer_id)
    
    balances = CustomerBalance.objects.filter(customer=customer)
    
    quotation_numbers = SalesInvoice.objects.filter(
        sale_type='QUOTATION',
        status='PENDING',
        customer=customer
    ).exclude(quotation_number='').values('quotation_number').distinct()

    quotations = []
    for pn in quotation_numbers:
        quotation_number = pn['quotation_number']
        sales = SalesInvoice.objects.filter(
            quotation_number=quotation_number,
            sale_type='QUOTATION',
            status='PENDING'
        ).order_by('-timestamp')

        first_sale = sales.first()
        if first_sale:
            total_with_vat = sum(sale.total_with_vat for sale in sales)
            total_qty = sum(sale.qty for sale in sales)
            unit_price_without_vat = (total_with_vat / (1 + (first_sale.vat_rate / 100))) / total_qty
            quotations.append({
                'quotation_number': quotation_number,
                'customer': first_sale.customer.legal_name,
                'timestamp': first_sale.timestamp,
                'total_with_vat': total_with_vat,
                'unit_price': unit_price_without_vat,
                'sales': sales
            })

    logger.info(f"Quotations for customer {customer_id}: {quotations}")

    if request.method == 'POST':
        quotation_number = request.POST.get('quotation_number')
        if quotation_number:
            return redirect('reports:mark_quotation_paid', quotation_number=quotation_number.lstrip('QUOTATION-'))
        else:
            return render(request, 'customer_balance.html', {
                'customer': customer,
                'balances': balances,
                'quotations': quotations,
                'error': 'Please select a quotation to pay.'
            })

    return render(request, 'customer_balance.html', {
        'customer': customer,
        'balances': balances,
        'quotations': quotations
    })

# -------------------- customer_balance_retail --------------------

def customer_balance_retail(request, customer_id):
    customer = get_object_or_404(Customers, customer_id=customer_id)

    balances = CustomerBalance.objects.filter(customer=customer, transaction_type='CASH_SALE')

    return render(request, 'customer_balance_retail.html', {
        'customer': customer,
        'balances': balances
    })

# ----------------------- customer_payments ------------------------

def customer_payments(request):
    if request.method == 'POST':
        form_data = request.POST
        CustomerPayments.objects.create(
            customer_id=form_data.get('customer_id'),
            quotation_number=form_data.get('quotation_number'),
            amount_paid=form_data.get('amount_paid'),
            payment_date=form_data.get('payment_date'),
            payment_code=form_data.get('payment_code'),
            payment_details=form_data.get('payment_details'),
            transaction_type='QUOTATION',
            transaction_id=form_data.get('transaction_id'),
            vat_amount=form_data.get('vat_amount') or 0,
            installment_number=form_data.get('installment_number'),
            product_type=form_data.get('product_type')
        )
        return redirect('customers:payments_quotation')

    return render(request, 'customer_payments.html', {
        'customers': Customers.objects.all(),
        'payment_codes': PaymentCode.objects.all(),
        'payments': CustomerPayments.objects.filter(transaction_type='QUOTATION')
    })

# -------------------- customer_summary_select ---------------------

def customer_summary_select(request):
    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        if customer_id:
            return redirect('customers:customer_summary', customer_id=customer_id)
    customers = Customers.objects.all()
    return render(request, 'customer_summary_select.html', {'customers': customers})

# ----------------- customer_summary ----------------------

def customer_summary(request, customer_id):
    customer = get_object_or_404(Customers, customer_id=customer_id)
    products = Products.objects.all()

    product_id = request.GET.get('product_id', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%d/%m/%Y').strftime('%Y-%m-%d')
        except ValueError:
            start_date = ''
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%d/%m/%Y').strftime('%Y-%m-%d')
        except ValueError:
            end_date = ''

    # Розничные продажи
    retail_sales = RetailSale.objects.filter(customer=customer).select_related('customer', 'product')
    if product_id:
        retail_sales = retail_sales.filter(product_id=product_id)
    if start_date:
        retail_sales = retail_sales.filter(sell_date__gte=start_date)
    if end_date:
        retail_sales = retail_sales.filter(sell_date__lte=end_date)

    # Продажи через профрму (SalesInvoice с типом QUOTATION или INVOICED)
    quotation_sales = SalesInvoice.objects.filter(
        customer=customer,
        sale_type__in=['QUOTATION', 'INVOICED']
    ).select_related('customer', 'product')
    if product_id:
        quotation_sales = quotation_sales.filter(product_id=product_id)
    if start_date:
        quotation_sales = quotation_sales.filter(sell_date__gte=start_date)
    if end_date:
        quotation_sales = quotation_sales.filter(sell_date__lte=end_date)

    # Агрегация для розничных продаж
    totals_retail = retail_sales.aggregate(
        total_retail_amount=Sum('total_with_vat'),
        total_retail_profit=Sum('profit_wo_vat')
    )
    total_retail_amount = totals_retail['total_retail_amount'] or 0
    total_retail_profit = totals_retail['total_retail_profit'] or 0

    # Агрегация для профрм
    totals_quotation = quotation_sales.aggregate(
        total_quotation_amount=Sum('total_with_vat'),
        total_quotation_profit=Sum('profit_wo_vat')
    )
    total_quotation_amount = totals_quotation['total_quotation_amount'] or 0
    total_quotation_profit = totals_quotation['total_quotation_profit'] or 0

    # Общие итоги
    total_amount = total_retail_amount + total_quotation_amount
    total_profit = total_retail_profit + total_quotation_profit

    last_30_days = timezone.now().date() - timedelta(days=30)
    recent_sales_retail = RetailSale.objects.filter(
        customer=customer,
        sell_date__gte=last_30_days
    ).aggregate(total=Sum('total_with_vat'))
    recent_sales_quotation = SalesInvoice.objects.filter(
        customer=customer,
        sell_date__gte=last_30_days,
        sale_type__in=['QUOTATION', 'INVOICED']
    ).aggregate(total=Sum('total_with_vat'))
    recent_total_retail = recent_sales_retail['total'] or 0
    recent_total_quotation = recent_sales_quotation['total'] or 0
    recent_total = recent_total_retail + recent_total_quotation

    has_debt = CustomerBalance.objects.filter(
        customer=customer,
        balance_to_pay__gt=0
    ).exists()

    customer.credit_rating = max(0, customer.credit_rating)
    if recent_total > 1000:
        customer.credit_rating += 1
    if has_debt:
        customer.credit_rating = max(0, customer.credit_rating - 1)
    customer.save()

    context = {
        'customer': customer,
        'products': products,
        'retail_sales': retail_sales,
        'quotation_sales': quotation_sales,  # Добавляем профрмы
        'total_retail_amount': total_retail_amount,
        'total_retail_profit': total_retail_profit,
        'total_quotation_amount': total_quotation_amount,  # Добавляем итоги для профрм
        'total_quotation_profit': total_quotation_profit,
        'total_amount': total_amount,  # Общие итоги
        'total_profit': total_profit,
        'filter_product_id': product_id,
        'filter_start_date': start_date,
        'filter_end_date': end_date,
    }
    return render(request, 'customer_summary.html', context)