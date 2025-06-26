from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.db import models
from django.db.models import Min, Max, Sum
from django.db.models.functions import TruncMonth, TruncYear
import json
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from datetime import datetime, timedelta
from django.db import IntegrityError

from .models import Aperd, Product, AumData
from .forms import AperdForm, ProductForm, AumDataForm

import json



# Create your views here.

def loginPage(request):
    page = 'login'

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'User does not exist')
            return render(request, 'login.html', {'page': page})

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username OR password does not exist')

    # Clear any existing success messages before rendering login page
    storage = messages.get_messages(request)
    storage.used = True

    context = {'page': page}
    return render(request, 'login.html', context)


@login_required(login_url='login')
def logoutUser(request):
    logout(request) # Bkl delete session tokennya
    return redirect('login')

@login_required(login_url='login')
def home(request):
    q = request.GET.get('q') or ''
    aperds   = Aperd.objects.filter(name__icontains=q)
    products = Product.objects.filter(name__icontains=q)

    # 1) Total AUM across all data
    total_aum_all = AumData.objects.aggregate(total=Sum('aum'))['total'] or 0

    # 2) AUM by APERD
    aperd_data = []
    for a in aperds:
        s = AumData.objects.filter(aperd=a).aggregate(total=Sum('aum'))['total'] or 0
        aperd_data.append({'name': a.name, 'aum': float(s)})

    # 3) AUM by Product
    prod_data = []
    for p in products:
        s = AumData.objects.filter(product=p).aggregate(total=Sum('aum'))['total'] or 0
        prod_data.append({'name': p.name, 'aum': float(s)})

    # 4) Build global month list
    monthly_all = (
        AumData.objects
            .annotate(m=TruncMonth('date'))
            .values('m')
            .distinct()
            .order_by('m')
    )
    month_labels = [d['m'].strftime('%b %Y') for d in monthly_all]

    def build_growth(series_totals):
        out = []
        for i in range(len(series_totals)):
            if i == 0 or series_totals[i-1] == 0:
                out.append(0)
            else:
                out.append(round((series_totals[i] - series_totals[i-1]) / series_totals[i-1] * 100, 2))
        return out

    # 5) Growth per APERD
    growth_by_aperd = {}
    for a in aperds:
        qs = (
            AumData.objects.filter(aperd=a)
                .annotate(m=TruncMonth('date'))
                .values('m')
                .annotate(total=Sum('aum'))
                .order_by('m')
        )
        totals_map = { d['m'].strftime('%b %Y'): float(d['total']) for d in qs }
        series = [totals_map.get(m, 0) for m in month_labels]
        growth_by_aperd[a.id] = build_growth(series)

    # 6) Growth per Product
    growth_by_product = {}
    for p in products:
        qs = (
            AumData.objects.filter(product=p)
                .annotate(m=TruncMonth('date'))
                .values('m')
                .annotate(total=Sum('aum'))
                .order_by('m')
        )
        totals_map = { d['m'].strftime('%b %Y'): float(d['total']) for d in qs }
        series = [totals_map.get(m, 0) for m in month_labels]
        growth_by_product[p.id] = build_growth(series)

    # 7) Dropdown options
    options = (
        [{'type':'aperd','id':a.id,'name':a.name} for a in aperds]
      + [{'type':'product','id':p.id,'name':p.name} for p in products]
    )

    context = {
        'aperds': aperds,
        'aperd_count': aperds.count(),
        'prod_data': json.dumps(prod_data),
        'aperd_data': json.dumps(aperd_data),  
        'total_aum':    "{:,.2f}".format(total_aum_all),
        'month_labels': json.dumps(month_labels),
        'today': datetime.today(),
    }
    return render(request, 'myapp/home.html', context)


@login_required(login_url='login')
def aperd(request, pk):
    aperd = get_object_or_404(Aperd, id=pk)

    q = request.GET.get('q') if request.GET.get('q') != None else ''
    products = Product.objects.filter(
        aperd=aperd,
        name__icontains=q
    )

    filter_type  = request.GET.get('filter', 'all')   # 'all' or 'year'
    year_selected = request.GET.get('year')           # e.g. "2024"

    # Fetch all AUMData for this APERD
    data_qs = AumData.objects.filter(aperd=aperd).order_by('date')

    years = data_qs.dates('date', 'year').values_list('date__year', flat=True)
    if filter_type == 'year' and year_selected and year_selected.isdigit():
        data_qs = data_qs.filter(date__year=int(year_selected))
    #
    #  Total AUM for this APERD across all its products
    total_aum_aperd = data_qs.aggregate(total=Sum('aum'))['total'] or 0

    # Bar chart: AUM by product
    product_agg = data_qs.values('product__name').annotate(total=Sum('aum')).order_by('product__name')
    bar_labels = [d['product__name'] for d in product_agg]
    bar_aums = [float(d['total']) for d in product_agg]

    # Line chart: growth month over month for this APERD
    monthly = data_qs.annotate(period=TruncMonth('date')) \
                   .values('period') \
                   .annotate(total=Sum('aum')) \
                   .order_by('period')

    labels = [d['period'].strftime('%b %Y') for d in monthly]
    monthly_totals = [float(d['total']) for d in monthly]

    growth_vals = []
    for i, curr in enumerate(monthly_totals):
        if i == 0 or monthly_totals[i - 1] == 0:
            growth_vals.append(0)
        else:
            growth_vals.append(round((curr - monthly_totals[i - 1]) / monthly_totals[i - 1] * 100, 2))

    chart_data = {
        'bar_labels':   bar_labels,
        'bar_aums':     bar_aums,
        'labels':       labels,
        'aum_values':   monthly_totals,
        'growth_values':growth_vals,
    }

    context = {
        'aperd': aperd,
        'products': products,
        'chart_data': json.dumps(chart_data),
        'filter_type': filter_type,
        'today': datetime.today(),
        'year_selected':    year_selected,
        'years':            years,
        'total_aum_aperd':  f"{total_aum_aperd:,.2f}",
    }
    return render(request, 'myapp/aperd.html', context)

@login_required(login_url='login')
def addAperd(request):
    if request.method == 'POST':
        form = AperdForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = AperdForm()
    
    context = {'form': form, 'title':'Add New APERD', 'today': datetime.today()}
    return render(request, 'myapp/addEdit.html', context) 

@login_required(login_url='login')
def editAperd(request,pk):
    aperd = Aperd.objects.get(id=pk)
    form = AperdForm(instance=aperd)
    # Pake instance biar nanti bkl akses id yang mau diedit
    # dan gak bakal buat room baru

    if request.method == 'POST':
        form = AperdForm(request.POST, instance=aperd)
        # Sama kyk reasoning di atas, ditambah instance biar
        # nanti dia edit room sesuai sm id dan bukan nambah
        # room baru.

        aperd.name = request.POST.get('name')
        aperd.pic = request.POST.get('pic')
        aperd.progress = request.POST.get('progress')
        aperd.desc = request.POST.get('desc')
        aperd.save()

        return redirect('home')
    
        # if form.is_valid():
        #     form.save()
        #     return redirect('home')

    context = {'form': form, 'aperd': aperd, 'title': 'Edit APERD', 'today': datetime.today()}
    return render(request, 'myapp/addEdit.html', context)

@login_required(login_url='login')
def deleteAperd(request, pk):
    aperd = get_object_or_404(Aperd, id=pk)

    if request.method == 'POST':
        products = aperd.product_set.all()

        for product in products:
            if product.aperd.count() <= 1:
                # Only connected to this APERD → delete it and its AUM data
                AumData.objects.filter(product=product).delete()
                product.delete()
            else:
                # More than one APERD → just remove this one
                product.aperd.remove(aperd)

        # Delete AUMData linked to this APERD
        AumData.objects.filter(aperd=aperd).delete()

        # Finally, delete the APERD
        aperd.delete()

        return redirect('home')

    return render(request, 'myapp/delete.html', {'obj': aperd, 'today': datetime.today(),})
 

@login_required(login_url='login')
def product(request, pk):
    product = get_object_or_404(Product, id=pk)
    aperd_id = request.GET.get('aperd_id')
    try:
        if aperd_id and aperd_id.isdigit():
            back_url = reverse('aperd', args=[int(aperd_id)])
        else:
            raise ValueError
    except (NoReverseMatch, ValueError):
        back_url = reverse('home')

    filter_type   = request.GET.get('filter', 'all')   # 'all' or 'year'
    year_selected = request.GET.get('year')

    data_qs = AumData.objects.filter(product=product).order_by('date')  

    # collect available years
    years = data_qs.dates('date','year').values_list('date__year', flat=True)

     # apply filter
    if filter_type == 'year' and year_selected and year_selected.isdigit():
        data_qs = data_qs.filter(date__year=int(year_selected))

    total_aum_product = data_qs.aggregate(total=Sum('aum'))['total'] or 0

    # Bar chart: AUM per APERD managing the product
    aperd_agg = data_qs.values('aperd__name').annotate(total=Sum('aum')).order_by('aperd__name')
    bar_labels = [d['aperd__name'] for d in aperd_agg]
    bar_aums = [float(d['total']) for d in aperd_agg]

    # Line chart: Growth rate month over month
    monthly = data_qs.annotate(period=TruncMonth('date')) \
                   .values('period') \
                   .annotate(total=Sum('aum')) \
                   .order_by('period')

    labels = [d['period'].strftime('%b %Y') for d in monthly]
    monthly_totals = [float(d['total']) for d in monthly]

    growth_vals = []
    for i, curr in enumerate(monthly_totals):
        if i == 0 or monthly_totals[i - 1] == 0:
            growth_vals.append(0)
        else:
            growth_vals.append(round((curr - monthly_totals[i - 1]) / monthly_totals[i - 1] * 100, 2))

    chart_data = {
        'labels': labels,
        'aum_values': monthly_totals,
        'growth_values': growth_vals,
        'bar_labels': bar_labels,
        'bar_aums': bar_aums
    }

    context = {
        'product': product,
        'back_url': back_url,
        'chart_data': json.dumps(chart_data),
        'data_list': data_qs,
        'today': datetime.today(),
        'filter_type': filter_type,
        'year_selected': year_selected,
        'years': years,
        'total_aum_product': f"{total_aum_product:,.2f}",
    }
    return render(request, 'myapp/product.html', context)


@login_required(login_url='login')
def addProduct(request):
    aperd_id = request.GET.get('aperd_id') or request.POST.get('aperd_id')

    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            if aperd_id:
                return redirect('aperd', pk=aperd_id)
            else:
                return redirect('home')
    else:
        form = ProductForm()

    context = {
        'form': form,
        'title': 'Add New Product',
        'aperd_id': aperd_id,
        'today': datetime.today()
    }
    return render(request, 'myapp/addEdit.html', context)

@login_required(login_url='login')
def editProduct(request, pk):
    product = Product.objects.get(id=pk)
    aperd_id = request.GET.get('aperd_id') or request.POST.get('aperd_id')

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            if aperd_id:
                return redirect('aperd', pk=aperd_id)
            else:
                return redirect('home')
    else:
        form = ProductForm(instance=product)

    context = {
        'form': form,
        'title': 'Edit Product',
        'product': product,
        'aperd_id': aperd_id,
        'today': datetime.today()
    }
    return render(request, 'myapp/addEdit.html', context)

@login_required(login_url='login')
def deleteProduct(request, pk):
    product = Product.objects.get(id=pk)
    aperd_id = request.GET.get('aperd_id')

    if request.method == 'POST':
        product.delete()
        if aperd_id:
            return redirect('aperd', pk=aperd_id)
        else:
            return redirect('home')

    context = {
        'obj': product,
        'aperd_id': aperd_id,
        'today': datetime.today()
    }
    return render(request, 'myapp/delete.html', context)

@login_required(login_url='login')
def add_product_data(request, pk):
    product = get_object_or_404(Product, id=pk)
    
    if request.method == 'POST':
        form = AumDataForm(request.POST)
        if form.is_valid():
            try:
                product_data = form.save(commit=False)
                product_data.product = product
                product_data.save()
                # messages.success(request, 'Data added successfully!')
                return redirect('product', pk=product.id)
            except IntegrityError:
                messages.error(request, 'Data for this date already exists. Please choose a different date or edit the existing data.')
                return render(request, 'myapp/addEdit.html', {
                    'form': form,
                    'product': product,
                    'title': 'Add Product Data'
                })
    else:
        form = AumDataForm()
    
    context = {
        'form': form,
        'product': product,
        'title': 'Add Product Data',
        'today': datetime.today()
    }
    return render(request, 'myapp/addEdit.html', context)

@login_required(login_url='login')
def edit_product_data(request, pk, data_pk):
    product_data = get_object_or_404(AumData, id=data_pk, product_id=pk)
    
    if request.method == 'POST':
        form = AumDataForm(request.POST, instance=product_data)
        if form.is_valid():
            form.save()
            messages.success(request, 'Data updated successfully!')
            return redirect('product', pk=pk)
    else:
        form = AumDataForm(instance=product_data)
    
    context = {
        'form': form,
        'product': product_data.product,
        'title': 'Edit Product Data',
        'today': datetime.today()
    }
    return render(request, 'myapp/addEdit.html', context)

@login_required(login_url='login')
def delete_product_data(request, pk, data_pk):
    product_data = get_object_or_404(AumData, id=data_pk, product_id=pk)
    
    if request.method == 'POST':
        product_data.delete()
        messages.success(request, 'Data deleted successfully!')
        return redirect('product', pk=pk)
    
    context = {
        'obj': product_data,
        'title': 'Delete Product Data',
        'today': datetime.today()   
    }
    return render(request, 'myapp/delete.html', context)  