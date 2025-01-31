from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django import forms
from cart.models import Cart, displayed_items
# from inventory.models import product
from unified.models import Product as product
from transaction.models import productTransaction, transaction
from transaction.views import DateSelector
from plotly import express as px
from plotly import offline as po
import plotly.figure_factory as ff
from datetime import datetime, timedelta
import pandas as pd
import pytz, os, shutil
from vendor.models import Vendor
from django.http import JsonResponse
from unified.models import Product
import openpyxl
from django.http import HttpResponse
from datetime import datetime
from orders.models import Order,OrderedFood
from datetime import datetime
from django.http import JsonResponse
from decimal import Decimal

timezone = pytz.timezone("Asia/Kolkata")
from django.http import JsonResponse
@login_required(login_url="/pos/user/login/")
def fetch_product(request):
    try:
        # Get the current vendor associated with the logged-in user
        vendor = Vendor.objects.get(user=request.user)
    except Vendor.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Vendor not found'})

    if request.method == "GET":
        search = request.GET.get('search', '').strip()
        if search:
            # Filter products by the current vendor and search query
            products = product.objects.filter(vendor=vendor).filter(
                barcode__icontains=search
            ) | product.objects.filter(vendor=vendor).filter(
                product_name__icontains=search
            ) | product.objects.filter(vendor=vendor).filter(
                product_desc__icontains=search
            )

            # Serialize the matching products
            product_list = [
                {
                    'id': product.id,
                    'barcode': product.barcode,
                    'name': product.product_name,
                    'qty':product.qty,
                    'img_url': product.image.url if product.image else '',  # Use the URL of the image
                    'regular_price': product.regular_price,
                    'sales_price': product.sales_price,
                    'unit_type':product.unit_type
                }
                for product in products
            ]
            return JsonResponse({'success': True, 'products': product_list})
        return JsonResponse({'success': False, 'error': 'No search term provided'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

class EnterBarcode(forms.Form):
    product = forms.CharField(widget=forms.TextInput(attrs={'autofocus':"autofocus",' autocomplete':"off",'style':"width:100%"}),max_length = 32)
    qty = forms.DecimalField(label="Quantity",widget=forms.TextInput(attrs={'style':"width:100%"}))

@login_required(login_url="/pos/user/login/")
def register(request):
    qty = 1
    if request.method == "POST":
        inputed_text = request.POST.get('id_search')
        product_id = request.POST.get('product_id')
        qty = request.POST.get('qty', 1)
        if inputed_text and not product_id:
            try:
                vendor = Vendor.objects.get(user=request.user)
                barcode_product = product.objects.filter(barcode=inputed_text, vendor=vendor).first()
                product_id=barcode_product.id
            except:
                print("product barcode was not correct") 
        
        if qty:
            pass
        else:
            qty = 1

        if product_id and qty:
            return redirect(f"/pos/cart/add/{product_id}/{qty}")
    
    try:
        cart = request.session[settings.CART_SESSION_ID]
        Total = round(pd.DataFrame(cart).T["line_total"].astype(float).sum(), 2)
        Tax_Total = round(pd.DataFrame(cart).T["tax_value"].astype(float).sum(), 2)
    except KeyError:
        cart = Cart(request)
        Total = 0
        Tax_Total = 0

    context = {
        'product_not_for_open_sell': True if "ProductNotForOpenSell" in request.path else False,
        'no_product': True if "ProductNotFound" in request.path else False,
        'address_not_found': True if "AddressNotFound" in request.path else False,
        'not_enough_qty': True if "NotEnoughQTY" in request.path else False,
        'cart': cart,
        'total': Total,
        'tax_total': Tax_Total,
        'displayed_items': displayed_items.objects.all(),
    }
    request.session["Total"] = Total
    request.session["Tax_Total"] = Tax_Total
    request.session.modified = True
    return render(request, 'pos/retailScreen.html', context=context)


@login_required(login_url="/pos/user/login/")
def retail_display(request,values=None):
    if values:
        try:
            # response = f"""<div class="h5 text-dark" style="text-align:left;white-space:pre-wrap;padding-right:50px;"><div class="p-2">{'SUB-TOTAL':<15}:     {round(request.session["Total"]-request.session["Tax_Total"],2)}</div><div class="p-2">{'TAX-TOTAL':<16}:     {request.session["Tax_Total"]}</div></div><hr><div class="h1 text-gray-900 pl-5">TOTAL : <span style="padding-left:80px;">{request.session["Total"]}</span></div>"""
            cart = request.session[settings.CART_SESSION_ID]
            
            if len(cart) == 0: return HttpResponse("IMAGE")
            
            total = round(pd.DataFrame(cart).T["line_total"].astype(float).sum(),2) 
            response = f"""<div class="card shadow-sm p-0 m-0" style="width:100%;height:95%">
                    <div class="card-header p-0" >
                        <table class="table p-0 m-0" style="text-align:right;">
                            <tr>
                                <th style="font-family: bold;color:rgba(0, 0, 0, 0.623); width:40%" >Barcode/Name</th>
                                <th style="font-family: bold;color:rgba(0, 0, 0, 0.623)">Qty</th>
                                <th style="font-family: bold;color:rgba(0, 0, 0, 0.623)">Price</th>
                                <th style="font-family: bold;color:rgba(0, 0, 0, 0.623)">L-Total<br>Tax</th>
                                <th style="font-family: bold;color:rgba(0, 0, 0, 0.623)">L-Total<br>Deposit</th>
                                <th style="font-family: bold;color:rgba(0, 0, 0, 0.623)">Line<br>Total</th>
                            </tr>
                        </table>
                    </div>
                    <div id="table-body" class="card-body" style="overflow: auto ;padding:0;">
                        <table class="table p-0 m-0" style="text-align:right;">
                """
            if cart:
                for key,value in cart.items():
                    response = response + f"""<tr>
                                <th style="text-align:left">{key} <br> {value['name']}</th> 
                                <td>{value['quantity']}</td>
                                <td>{value['price']}</td>
                                <td>{value['tax_value']}</td>
                                <td>{value['deposit_value']}</td>
                                <td>{value['line_total']}</td>
                            </tr> """
            response = response + f"""</table> </div> 
                                        <div class="card-footer py-3">
                                            <h1 class="m-0 font-weight-bold text-primary">Transaction Total:
                                            <span class="m-0 font-weight-bold text-dark" style="float:right;item-align:right">$ {total:.2f}</span>
                                            </h1>
                                        </div>
                                    </div>"""
            return HttpResponse(response)
        except Exception as e:
            print(e)
            return HttpResponse("")
    
    path="images4display/"  # insert the path to your directory   
    if os.path.exists(f"./{path}"):
        # print(f"{settings.STATIC_ROOT}/{path}")
        shutil.copytree(f"./{path}", f"{settings.STATIC_ROOT}/{path}", dirs_exist_ok=True)
    img_list = [ path+i for i in  os.listdir(path) if not i.endswith('.md')]
    
    return render(request,'pos/retailDisplay.html',context={"store_name":settings.STORE_NAME, "display_images":img_list})


@login_required(login_url="/pos/user/login/")
def report_regular(request,start_date,end_date):
    # timezone.localize(datetime.combine(datetime.strptime(start_date,"%Y-%m-%d").date(), datetime.min.time()))
    start_date = datetime.strptime(start_date,"%Y-%m-%d").date()
    end_date = datetime.strptime(end_date,"%Y-%m-%d").date()
    vendor = Vendor.objects.get(user=request.user)
    df = pd.DataFrame(productTransaction.objects.filter(transaction_date_time__date__range = (start_date,end_date), transaction__vendor=vendor).order_by('-transaction_date_time').values())
    if not df.shape[0]:
        return redirect("/")

    df['transaction_date_time'] = df['transaction_date_time'].apply(lambda x: x.astimezone(timezone) )
    df['date'] = df['transaction_date_time'].dt.date
    df['total_sales'] = (df['qty'] * df['sales_price']) + df['tax_amount'] + df['deposit_amount']
    df['total_pre_sales'] = df['qty'] * df['sales_price']

    date_group = df.groupby(['date','department','payment_type'])[['qty','total_pre_sales','tax_amount','deposit_amount','total_sales']].apply(lambda x : x.sum())
    table = date_group.reset_index().groupby(['date'])[['total_pre_sales','tax_amount','deposit_amount','total_sales']].apply(lambda x : x.sum())
    for i, val in table.iterrows():
        date_group.loc[(i," Day Total","")] = val
    table = date_group.reset_index().groupby(['date','department'])[['qty','total_pre_sales','tax_amount','deposit_amount','total_sales']].apply(lambda x : x.sum())
    for i, val in table.iterrows():
        if i[1] ==  " Day Total":
            continue
        date_group.loc[(i[0],i[1]," Department Total ")] = val

    date_group.loc[("TOTAL","TOTAL"," TOTAL")] = df[['total_pre_sales','tax_amount','deposit_amount','total_sales']].apply(lambda x : x.sum())
    for i, val in df.groupby('payment_type')[['total_pre_sales','tax_amount','deposit_amount','total_sales']].apply(lambda x : x.sum()).iterrows():
         date_group.loc[("TOTAL","TOTAL",i)] = val

    # Drop the 'Total Deposit' column
    date_group.drop(columns=['deposit_amount'], inplace=True)

    date_group = date_group.sort_index()
    date_group.fillna("",inplace=True)
    date_group.rename(columns = { 'qty':'Quantity','total_pre_sales':'Total Pre_Sales','tax_amount':'Total Tax',
            'deposit_amount':'Total Deposit','total_sales':'Total Sales'}, inplace = True)
    date_group.index.names = ['Date','Department','Payment Type',]

    return render(request,"pos/reportsRegular.html", context={
            "table_html":date_group.to_html(classes= "table table-bordered table-hover h6 text-gray-900 border-5"),
            "start_date":start_date,"end_date":end_date,"store_name":vendor.vendor_name,
            })


@login_required(login_url="/pos/user/login/")
def dashboard_products(request):
    try:
        number = 10
        context = {}
        today_date=datetime.now().date()
        last_30_date = datetime.now().date() - timedelta(30)
        vendor = Vendor.objects.get(user=request.user)
        df = pd.DataFrame(productTransaction.objects.filter(transaction_date_time__date__range = (last_30_date,today_date), transaction__vendor=vendor).order_by('-transaction_date_time').values())
        context['products_group'] = {}
        for i, df in df.groupby('department'):
            context['products_group'][i] = df.groupby(["barcode","name"])[["qty"]].sum().reset_index().sort_values(by=["qty"],ascending=False).iloc[:number].to_dict('records')

        context['low_inventory_products'] = product.objects.filter(vendor=vendor).order_by('qty').values('barcode','product_name','qty')[:50]
        context['number'] = number
    except Exception as e:
        print(e)
        return redirect("/pos/register/")
    return render(request,"pos/productsDashboard.html",context=context)


@login_required(login_url="/pos/user/login/")
def dashboard_department(request):
    context ={}
    end_date=datetime.now().date()
    start_date=datetime.now().date()
    form = DateSelector(initial = {'end_date':end_date, 'start_date':start_date})
    if request.method == "POST":
        form = DateSelector(request.POST)
        if form.is_valid():
            end_date= form.cleaned_data['end_date']
            start_date= form.cleaned_data['start_date']
    vendor = Vendor.objects.get(user=request.user)
    df = pd.DataFrame(productTransaction.objects.filter(transaction_date_time__date__range = (start_date,end_date), transaction__vendor=vendor).order_by('-transaction_date_time').values())
    if df.shape[0]:
        df['total_sales'] = (df['qty'] * df['sales_price']) + df['tax_amount'] + df['deposit_amount']
        df['total_pre_sales'] = df['qty'] * df['sales_price']
        sales_by_payment = df.groupby('payment_type')['total_sales'].sum()

        # tableValues = [['Total QTY', 'Total Sales Before Tax', 'Total Tax', 'Total Deposit']+[f"Sales by {i}" for i in sales_by_payment.index.to_list()],
        #                     [df['qty'].sum(), df['total_pre_sales'].sum(), df['tax_amount'].sum(), df['deposit_amount'].sum() ]+sales_by_payment.to_list()]
        # Removed Deposit
        tableValues = [['Total QTY', 'Total Sales Before Tax', 'Total Tax']+[f"Sales by {i}" for i in sales_by_payment.index.to_list()],
                            [df['qty'].sum(), df['total_pre_sales'].sum(), df['tax_amount'].sum() ]+sales_by_payment.to_list()]
        
        tableValues = [("TOTAL SALES",round(df['total_sales'].sum(),2))]+ list(zip(tableValues[0],tableValues[1]))
        table_fig = ff.create_table(tableValues, height_constant= 25,)
        table_fig.update_layout(margin = dict(b=10,t=0,l=0,r=0),height=275 ,)
        context['table_fig'] = po.plot(table_fig, auto_open=False, output_type='div',config= {'displayModeBar': False},include_plotlyjs=False)

        pie_fig = px.pie(values=sales_by_payment,names=sales_by_payment.index, color=sales_by_payment.index,
                            color_discrete_map={'CASH': "darkgreen",'EBT': "royalblue",'DEBIT/CREDIT':"darkslategray"} )
        pie_fig.update_layout(margin = dict(b=50,t=10,l=10,r=10),height=225 ,
                    title={ 'text': f"Date Period : ({start_date:%Y/%m/%d} - {end_date:%Y/%m/%d})", 'font_size':16,
                            'y':0.15, 'x':0.5,  'xanchor': 'center', 'yanchor': 'top'})
        pie_fig.update_traces(hovertemplate=None)
        context['pie_fig'] = po.plot(pie_fig, auto_open=False, output_type='div',config= {'displayModeBar': False},include_plotlyjs=False)

        sales_by_department = df.groupby(['department','payment_type'])[['qty','total_pre_sales','tax_amount','deposit_amount','total_sales']].apply(lambda x : x.sum())
        sales_by_department = sales_by_department.reset_index()

        bar_fig = px.bar(sales_by_department, x="department",  y="total_sales", color="payment_type",text_auto=True, hover_name="total_sales",
                hover_data={'qty':True,'total_pre_sales':True,'tax_amount':True,'deposit_amount':False,'total_sales':True,},
                labels={'qty':"Quantity",'payment_type':"Payment Type",'department':"Department",'total_sales':"Total Sales","total_pre_sales":"Total Sales Before Tax",
                        'tax_amount':"Total Tax Amount",'deposit_amount':"Total Deposit Amount"},
                color_discrete_map={  'CASH': "darkgreen",'EBT': "royalblue",'DEBIT/CREDIT':"darkslategray"})
        bar_fig.update_yaxes(title=f"Total Sales ({start_date:%Y/%m/%d} - {end_date:%Y/%m/%d})")
        bar_fig.update_layout(margin = dict(b=10,pad=0,t=10,l=10,r=10),height=500,showlegend=False)

        # df['date'] = df['transaction_date_time'].dt.date
        # date_group = df.groupby(['date','department','payment_type'])[['qty','total_pre_sales','tax_amount','deposit_amount','total_sales']].apply(lambda x : x.sum())
        # date_group = date_group.reset_index()
        # bar_fig = px.bar(date_group, x="date",  y="total_sales", facet_row="department", hover_name="total_sales", color="payment_type",
        #         hover_data={'qty':True,'total_pre_sales':True,'tax_amount':True,'deposit_amount':True,'total_sales':False,},
        #         labels={'qty':"Quantity",'payment_type':"Payment Type",'department':"Department",'total_sales':"Total Sales","total_pre_sales":"Total Sales b4 Tax & Deposit",
        #                 'tax_amount':"Total Tax Amount",'deposit_amount':"Total Deposit Amount",'date':"Date"},
        #          color_discrete_sequence=["darkgreen", "royalblue", "darkslategray"])
        # bar_fig.update_layout(margin = dict(b=10,pad=0,t=10,l=10,r=10),height=500,showlegend=False)

        context['bar_fig'] = po.plot(bar_fig, auto_open=False, output_type='div',config= {'displayModeBar': False},include_plotlyjs=False)

    context["report_link"] = f"/pos/department_report/{start_date}/{end_date}/"
    context['form'] = form
    return render(request,"pos/departmentDashboard.html",context=context)


@login_required(login_url="/pos/user/login/")
def dashboard_sales(request):
    context = {}
    today_date =  datetime.combine(datetime.now().date(), datetime.min.time())
    try:
        vendor = Vendor.objects.get(user=request.user)
        df = pd.DataFrame(transaction.objects.filter(transaction_dt__date__gte = datetime(today_date.year, 1,1), vendor=vendor).values())
        df['transaction_dt'] = df['transaction_dt'].apply(lambda x: x.astimezone(timezone) )
        df['date'] = df['transaction_dt'].dt.date
        df_date = df.groupby('date')['total_sale'].sum()
        df_date.index = pd.to_datetime(df_date.index)
        if not df_date.get(datetime(today_date.year, 1,1)):df_date[datetime(today_date.year, 1,1)] = 0
        if not df_date.get(today_date): df_date[today_date] = 0
        df_date = df_date.asfreq('D',fill_value=0)

        context['today_total_sales'] = df_date.get(today_date)
        context["add_info"] = {}
        context["add_info"]['Yesterday\'s Total Sales'] = df_date.get(today_date-timedelta(1))
        context["add_info"]['Last 7 Days Avg Sales'] = df_date[df_date.index>today_date-timedelta(7)].sum()/7
        context['30_Days_Avg_Sales'] = df_date[df_date.index>today_date-timedelta(30)].mean()
        context['30_Days_Total_Sales'] = df_date[df_date.index>today_date-timedelta(30)].sum()
        # context["add_info"]['WTD Total Sales'] = df_date.resample('W').sum()[-1]
        weekly_sales = df_date.resample('W').sum()
        context["add_info"]['WTD Total Sales'] = df_date.resample('W').sum().iloc[-1]
        context["add_info"]['Last Week Total Sales'] = weekly_sales.iloc[-2] if len(weekly_sales) > 1 else 0
        if len(weekly_sales) > 0:
            context["add_info"]['WTD Total Sales'] = weekly_sales.iloc[-1]
        else:
            context["add_info"]['WTD Total Sales'] = 0

        # Monthly resampling
        monthly_sales = df_date.resample('ME').sum()
        if len(monthly_sales) > 0:
            context["add_info"]['MTD Total Sales'] = monthly_sales.iloc[-1]
        else:
            context["add_info"]['MTD Total Sales'] = 0

        # Yearly resampling
        yearly_sales = df_date.resample('YE').sum()
        if len(yearly_sales) > 0:
            context["add_info"]['YTD Total Sales'] = yearly_sales.iloc[-1]
        else:
            context["add_info"]['YTD Total Sales'] = 0

        # print(df_date.resample('W').sum())
        fig = px.bar(x= df_date.index,  y=df_date,text_auto=True,barmode='group',template="plotly_white" ,labels={"x":"Date","y":"Total Sales"})
        fig.update_xaxes(title="Days", tickformat = '%a,%d/%m',tickangle=-90)
        fig.update_yaxes(title="Total Sales")
        fig.update_layout( margin = dict(b=10,pad=0,t=10,r=0,l=0), )
        div = po.plot(fig, auto_open=False, output_type='div',config= {'displayModeBar': False},include_plotlyjs=False)
        context['30_day_sales_graph'] = div

        df_day_payment = df[df['date'] == today_date.date() ].groupby('payment_type')['total_sale'].sum().reset_index()
        fig2 = px.pie(df_day_payment,values='total_sale',names='payment_type',template="plotly_white",height=195 ,
            labels={"payment_type":"Payment Type","total_sale":"Total Sales"})
        fig2.update_layout( margin = dict(b=10,pad=0,t=10), )
        context['day_payment_graph'] = po.plot(fig2, auto_open=False, output_type='div',config= {'displayModeBar': False},include_plotlyjs=False)
    except Exception as e:
        return redirect("/pos/register/")
    return render(request,"pos/salesDashboard.html",context=context)


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            request.session["Total"] = 0.00
            request.session["Tax_Total"] = 0.00
            return redirect('home')
        else:
            return render(request, 'pos/registration/login.html',context={'error':True,"store_name":settings.STORE_NAME})
    else:
        return render(request, 'pos/registration/login.html',context={"store_name":settings.STORE_NAME},)


@login_required(login_url="/pos/user/login/")
def user_logout(request):
    logout(request)
    return render(request, 'pos/registration/login.html',context={'logout':True})

# def product_sales_report(request):
#     # Helper function to parse dates
#     def parse_date(date_str):
#         try:
#             return datetime.strptime(date_str, '%Y-%m-%d')
#         except (ValueError, TypeError):
#             return None

#     # Get date range from request
#     min_date = parse_date(request.GET.get('min_date'))
#     max_date = parse_date(request.GET.get('max_date'))

#     order_transactions = Order.objects.filter(vendors=request.user.user, is_ordered=True)

#     # Filter transactions based on date range and vendor
#     transactions = productTransaction.objects.filter(transaction__vendor=request.user.user)
#     if min_date:
#         transactions = transactions.filter(transaction_date_time__gte=min_date)
#     if max_date:
#         transactions = transactions.filter(transaction_date_time__lte=max_date)
    
#     def product_finder(request,barcode):
#         # Try to find the product by id
#         product = Product.objects.filter(vendor=request.user.user, id=barcode).first()
#         if not product:
#             # If no product is found by id, try to find it by barcode
#             product = Product.objects.filter(vendor=request.user.user, barcode=barcode).first()
#         return product
    
            
#     # Dictionary to store aggregated data per (barcode, sales_price)
#     aggregated_data = {}
#     for transaction in order_transactions:
#         # key = (transaction.barcode, transaction.sales_price)
#         order_products = OrderedFood.objects.filter(order=transaction)
#         for order_product in order_products:
#             key = (order_product.product.barcode, order_product.product.sales_price,'Online')
#             print(key)
#             if key not in aggregated_data:
#                 aggregated_data[key] = {
#                     'barcode': order_product.product.barcode,
#                     'name': order_product.product.product_name,   
#                     'department': order_product.product.category,  
#                     'sales_price': order_product.product.sales_price, 
#                     'hsn_number': order_product.product.hsn_number if order_product.product.hsn_number else '',  
#                     'model_number': order_product.product.model_number if order_product.product.model_number else '',  
#                     'unit_type': order_product.product.unit_type if order_product.product.unit_type else '',  
#                     'tax_percentage': order_product.product.tax_category.tax_percentage,
#                     'tax_category': order_product.product.tax_category,
#                     'total_tax_amount': 0,
#                     'total_qty_sold': 0,
#                     'total_value': 0,
#                 }
        
#             # Update aggregated data
#             aggregated_data[key]['total_qty_sold'] += order_product.quantity
#             aggregated_data[key]['total_tax_amount'] += (aggregated_data[key]['sales_price']*(order_product.product.tax_category.tax_percentage/100))* aggregated_data[key]['total_qty_sold']
#             aggregated_data[key]['total_value'] = aggregated_data[key]['sales_price'] * aggregated_data[key]['total_qty_sold']

#     print(aggregated_data)
#     print('--------------------------------------------------------------------------------------')

#     for transaction in transactions:
#         # Composite key of barcode and sales_price
#         key = (transaction.barcode, transaction.sales_price,'POS')
#         if key not in aggregated_data:
#             aggregated_data[key] = {
#                 'barcode': transaction.barcode,
#                 'name': transaction.name,   
#                 'department': transaction.department,  
#                 'sales_price': transaction.sales_price, 
#                 'hsn_number': product_finder(request,transaction.barcode).hsn_number if product_finder(request,transaction.barcode) else '',  
#                 'model_number': product_finder(request, transaction.barcode).model_number if product_finder(request,transaction.barcode) else '',  
#                 'unit_type': product_finder(request, transaction.barcode).unit_type if product_finder(request,transaction.barcode) else '',  
#                 'tax_percentage': transaction.tax_percentage,
#                 'tax_category': transaction.tax_category,
#                 'total_tax_amount': 0,
#                 'total_qty_sold': 0,
#                 'total_value': 0,
#             }
        
#         # Update aggregated data
#         aggregated_data[key]['total_qty_sold'] += transaction.qty
#         aggregated_data[key]['total_tax_amount'] += transaction.tax_amount
#         aggregated_data[key]['total_value'] = aggregated_data[key]['sales_price'] * aggregated_data[key]['total_qty_sold']
#     print(aggregated_data)

#     # Format the values in aggregated_data
#     for key, data in aggregated_data.items():
#         data['total_qty_sold'] = (
#             int(data['total_qty_sold']) 
#             if data['total_qty_sold'] == int(data['total_qty_sold']) 
#             else round(data['total_qty_sold'], 1)
#         )
#         data['total_tax_amount'] = (
#             int(data['total_tax_amount']) 
#             if data['total_tax_amount'] == int(data['total_tax_amount']) 
#             else round(data['total_tax_amount'], 2)
#         )
#         data['total_value'] = round(data['total_value'], 2)

#     # Format data for display
#     for key, data in aggregated_data.items():
#         data['total_value'] = f"₹{float(data['total_value']):.2f}"
#         data['total_tax_amount'] = f"₹{(data['total_tax_amount'])} ({data['tax_category']} {(data['tax_percentage']):.0f}%)"
#         data['sales_price'] = f"₹{float(data['sales_price']):.2f}"

#     # Convert aggregated data to a list
#     data = list(aggregated_data.values())

#     # Return the result as JSON
#     return JsonResponse({'data': data}, safe=False)


def product_sales_report(request):
    # Helper function to parse dates
    def parse_date(date_str):
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            return None

    # Get date range from request
    min_date = parse_date(request.GET.get('min_date'))
    max_date = parse_date(request.GET.get('max_date'))

    # Query related data
    order_transactions = Order.objects.filter(
        vendors=request.user.user, 
        is_ordered=True
    ).select_related('user').order_by('-created_at')
    
    transactions = productTransaction.objects.filter(
        transaction__vendor=request.user.user
    ).select_related('transaction').order_by('-transaction_date_time')
    
    # Apply date filters
    if min_date:
        # Include transactions on or after min_date
        transactions = transactions.filter(transaction_date_time__gte=min_date)
        order_transactions = order_transactions.filter(created_at__gte=min_date)
    
    if max_date:
        # Extend max_date to end of the day and use __lt to include all of max_date's transactions
        max_date_end = max_date + timedelta(days=1)
        transactions = transactions.filter(transaction_date_time__lt=max_date_end)
        order_transactions = order_transactions.filter(created_at__lt=max_date_end)
    # Dictionary to store aggregated data
    aggregated_data = {}

    # Process order transactions (Online orders)
    for transaction in order_transactions:
        order_products = OrderedFood.objects.filter(order=transaction).select_related(
            'product', 'product__tax_category', 'product__category'
        )
        for order_product in order_products:
            key = (order_product.product.barcode, order_product.product.sales_price, 'Online')
            if key not in aggregated_data:
                aggregated_data[key] = {
                    'barcode': order_product.product.barcode,
                    'name': order_product.product.product_name,
                    'department': str(order_product.product.category),
                    'sales_price': order_product.product.sales_price,
                    'hsn_number': order_product.product.hsn_number or '',
                    'model_number': order_product.product.model_number or '',
                    'unit_type': order_product.product.unit_type or '',
                    'tax_percentage': float(order_product.product.tax_category.tax_percentage),
                    'tax_category': str(order_product.product.tax_category.tax_category),
                    'platform':'Online',
                    'transaction_date_time':order_product.created_at,
                    'total_tax_amount': Decimal('0'),
                    'total_qty_sold': Decimal('0'),
                    'total_value': Decimal('0'),
                }

            aggregated_data[key]['total_qty_sold'] += Decimal(order_product.quantity)
            aggregated_data[key]['total_tax_amount'] += (
                order_product.product.sales_price 
                * (order_product.product.tax_category.tax_percentage / 100)
                * order_product.quantity
            )
            aggregated_data[key]['total_value'] += order_product.product.sales_price * order_product.quantity

    # Process POS transactions
    for transaction in transactions:
        key = (transaction.barcode, transaction.sales_price, 'POS')
        product = Product.objects.filter(vendor=request.user.user, id=transaction.barcode).select_related(
            'tax_category', 'category'
        ).first()
        if not product:
            product = Product.objects.filter(vendor=request.user.user, barcode=transaction.barcode).select_related(
                    'tax_category', 'category'
                ).first()
            
        if key not in aggregated_data:
            aggregated_data[key] = {
                'barcode': transaction.barcode,
                'name': transaction.name,
                'department': str(product.category) if product else '',
                'sales_price': transaction.sales_price,
                'hsn_number': product.hsn_number if product else '',
                'model_number': product.model_number if product else '',
                'unit_type': product.unit_type if product else '',
                'tax_percentage': float(transaction.tax_percentage),
                'tax_category': str(transaction.tax_category),
                'platform':'POS',
                'transaction_date_time':transaction.transaction_date_time ,
                'total_tax_amount': Decimal('0'),
                'total_qty_sold': Decimal('0'),
                'total_value': Decimal('0'),
            }

        aggregated_data[key]['total_qty_sold'] += Decimal(transaction.qty)
        aggregated_data[key]['total_tax_amount'] += Decimal(transaction.tax_amount)
        aggregated_data[key]['total_value'] += transaction.sales_price * Decimal(transaction.qty)

    # Format and serialize the data
    for key, data in aggregated_data.items():
        data['total_qty_sold'] = (
            int(data['total_qty_sold']) 
            if data['total_qty_sold'] == int(data['total_qty_sold']) 
            else round(data['total_qty_sold'], 1)
        )
        data['total_tax_amount'] = round(data['total_tax_amount'], 2)
        data['total_value'] = round(data['total_value'], 2)
        data['sales_price'] = f"₹{float(data['sales_price']):.2f}"
        data['total_tax_amount'] = f"₹{data['total_tax_amount']} ({data['tax_category']} {data['tax_percentage']}%)"
        data['total_value'] = f"₹{data['total_value']:.2f}"

    # Convert aggregated data to a list
    data = list(aggregated_data.values())

    # Return the result as JSON
    return JsonResponse({'data': data}, safe=False)


def product_sales_report_page(request):
    return render(request, 'pos/product_sales_report.html')


def product_sales_report_download(request):
    # Helper function to parse dates
    def parse_date(date_str):
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            return None

    if request.method == "POST":  # Ensure the method is POST
        # Get date range from request
        min_date = request.POST.get('min_date')
        max_date = request.POST.get('max_date')

        # Parse dates if needed
        parsed_min_date = parse_date(min_date)
        parsed_max_date = parse_date(max_date)

            # Query related data
        order_transactions = Order.objects.filter(
            vendors=request.user.user, 
            is_ordered=True
        ).select_related('user').order_by('-created_at')
        
        transactions = productTransaction.objects.filter(
            transaction__vendor=request.user.user
        ).select_related('transaction').order_by('-transaction_date_time')
        
        # Apply date filters
        if parsed_min_date:
            # Include transactions on or after min_date
            transactions = transactions.filter(transaction_date_time__gte=parsed_min_date)
            order_transactions = order_transactions.filter(created_at__gte=parsed_min_date)
        
        if parsed_max_date:
            # Extend max_date to end of the day and use __lt to include all of max_date's transactions
            max_date_end = parsed_max_date + timedelta(days=1)
            transactions = transactions.filter(transaction_date_time__lt=max_date_end)
            order_transactions = order_transactions.filter(created_at__lt=max_date_end)
        # Dictionary to store aggregated data
        aggregated_data = {}

        # Process order transactions (Online orders)
        for transaction in order_transactions:
            order_products = OrderedFood.objects.filter(order=transaction).select_related(
                'product', 'product__tax_category', 'product__category'
            )
            for order_product in order_products:
                key = (order_product.product.barcode, order_product.product.sales_price, 'Online')
                if key not in aggregated_data:
                    aggregated_data[key] = {
                        'barcode': order_product.product.barcode,
                        'name': order_product.product.product_name,
                        'department': str(order_product.product.category),
                        'sales_price': order_product.product.sales_price,
                        'hsn_number': order_product.product.hsn_number or '',
                        'model_number': order_product.product.model_number or '',
                        'unit_type': order_product.product.unit_type or '',
                        'tax_percentage': float(order_product.product.tax_category.tax_percentage),
                        'tax_category': str(order_product.product.tax_category.tax_category),
                        'platform': 'Online',
                        'total_tax_amount': Decimal('0'),
                        'total_qty_sold': Decimal('0'),
                        'total_value': Decimal('0'),
                    }

                aggregated_data[key]['total_qty_sold'] += Decimal(order_product.quantity)
                aggregated_data[key]['total_tax_amount'] += (
                    order_product.product.sales_price 
                    * (order_product.product.tax_category.tax_percentage / 100)
                    * order_product.quantity
                )
                aggregated_data[key]['total_value'] += order_product.product.sales_price * order_product.quantity

        # Process POS transactions
        for transaction in transactions:
            key = (transaction.barcode, transaction.sales_price, 'POS')
            product = Product.objects.filter(vendor=request.user.user, id=transaction.barcode).select_related(
                'tax_category', 'category'
                ).first()
            if not product:
                product = Product.objects.filter(vendor=request.user.user, barcode=transaction.barcode).select_related(
                        'tax_category', 'category'
                    ).first()

            if key not in aggregated_data:
                aggregated_data[key] = {
                    'barcode': transaction.barcode,
                    'name': transaction.name,
                    'department': str(product.category) if product else '',
                    'sales_price': transaction.sales_price,
                    'hsn_number': product.hsn_number if product else '',
                    'model_number': product.model_number if product else '',
                    'unit_type': product.unit_type if product else '',
                    'tax_percentage': float(transaction.tax_percentage),
                    'tax_category': str(transaction.tax_category),
                    'platform': 'POS',
                    'total_tax_amount': Decimal('0'),
                    'total_qty_sold': Decimal('0'),
                    'total_value': Decimal('0'),
                }

            aggregated_data[key]['total_qty_sold'] += Decimal(transaction.qty)
            aggregated_data[key]['total_tax_amount'] += Decimal(transaction.tax_amount)
            aggregated_data[key]['total_value'] += transaction.sales_price * Decimal(transaction.qty)

        # Format and serialize the data
        for key, data in aggregated_data.items():
            data['total_qty_sold'] = (
                int(data['total_qty_sold']) 
                if data['total_qty_sold'] == int(data['total_qty_sold']) 
                else round(data['total_qty_sold'], 1)
            )
            data['total_tax_amount'] = round(data['total_tax_amount'], 2)
            data['total_value'] = round(data['total_value'], 2)
            data['sales_price'] = f"₹{float(data['sales_price']):.2f}"
            data['total_tax_amount'] = f"₹{data['total_tax_amount']} ({data['tax_category']} {data['tax_percentage']}%)"
            data['total_value'] = f"₹{data['total_value']:.2f}"

        # Create an Excel workbook and sheet
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Product Sales Report"

        # Add column headers
        columns = [
            'Name', 'Department', 'HSN Number', 'Model Number',
            'Sales Price', 'Total Quantity Sold', 'Unit Type', 'Sale Source', 'Tax', 'Total Value'
        ]
        sheet.append(columns)

        # Add data rows
        for data in aggregated_data.values():
            row = [
                data['name'],
                data['department'],
                data['hsn_number'],
                data['model_number'],
                data['sales_price'],
                data['total_qty_sold'],
                data['unit_type'],
                data['platform'],
                data['total_tax_amount'],
                data['total_value'],
            ]
            sheet.append(row)

        # Auto-adjust column width
        for column_cells in sheet.columns:
            max_length = 0
            col_letter = column_cells[0].column_letter  # Get column letter
            for cell in column_cells:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except Exception:
                    pass
            adjusted_width = max_length + 2
            sheet.column_dimensions[col_letter].width = adjusted_width

        # Save the workbook to an HTTP response for download
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # Use the current date if min_date or max_date is not provided
        from datetime import date
        formatted_min_date = min_date if min_date else request.user.created_date.strftime("%Y-%m-%d")
        formatted_max_date = max_date if max_date else date.today().strftime("%Y-%m-%d")

        response['Content-Disposition'] = f'attachment; filename="product_sales_report_{formatted_min_date}_to_{formatted_max_date}.xlsx"'

        workbook.save(response)
        return response

    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)
