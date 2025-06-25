let autocomplete;

function initAutoComplete(){
autocomplete = new google.maps.places.Autocomplete(
    document.getElementById('id_address'),
    {
        types: ['geocode', 'establishment'],
        //default in this app is "IN" - add your country code
        componentRestrictions: {'country': ['in']},
    })
// function to specify what should happen when the prediction is clicked
autocomplete.addListener('place_changed', onPlaceChanged);
}

function onPlaceChanged (){
    var place = autocomplete.getPlace();

    // User did not select the prediction. Reset the input field or alert()
    if (!place.geometry){
        document.getElementById('id_address').placeholder = "Start typing...";
    }
    else{
        // console.log('place name=>', place.name)
    }

    // get the address components and assign them to the fields
    // console.log(place);
    var geocoder = new google.maps.Geocoder()
    var address = document.getElementById('id_address').value

    geocoder.geocode({'address': address}, function(results, status){
        // console.log('results=>', results)
        // console.log('status=>', status)
        if(status == google.maps.GeocoderStatus.OK){
            var latitude = results[0].geometry.location.lat();
            var longitude = results[0].geometry.location.lng();

            // console.log('lat=>', latitude);
            // console.log('long=>', longitude);
            $('#id_latitude').val(latitude);
            $('#id_longitude').val(longitude);

            $('#id_address').val(address);
        }
    });

    // loop through the address components and assign other address data
    console.log(place.address_components);
    for(var i=0; i<place.address_components.length; i++){
        for(var j=0; j<place.address_components[i].types.length; j++){
            // get country
            if(place.address_components[i].types[j] == 'country'){
                $('#id_country').val(place.address_components[i].long_name);
            }
            // get state
            if(place.address_components[i].types[j] == 'administrative_area_level_1'){
                $('#id_state').val(place.address_components[i].long_name);
            }
            // get city
            if(place.address_components[i].types[j] == 'locality'){
                $('#id_city').val(place.address_components[i].long_name);
            }
            // get pincode
            if(place.address_components[i].types[j] == 'postal_code'){
                $('#id_pin_code').val(place.address_components[i].long_name);
            }else{
                $('#id_pin_code').val("");
            }
        }
    }

}


$(document).ready(function(){
    // add to cart
    $('.add_to_cart').on('click', function(e){
        e.preventDefault();
        
        food_id = $(this).attr('data-id');
        url = $(this).attr('data-url');
        
       
        $.ajax({
            type: 'GET',
            url: url,
            success: function(response){
                if(response.status == 'login_required'){
                    swal(response.message, '', 'info').then(function(){
                        window.location = '/login';
                    })
                }else if(response.status == 'Failed'){
                    swal(response.message, '', 'error')
                
                }else if(response.status == 'stock_out'){
                    swal(response.message, '', 'error')
                }
                else if(response.status =='different_vendor_product'){
                    swal(response.message,'','warning')
                }
                else{
                    console.log(response)
                    $('#cart_count').text(response.cart_counter);
                    // $('#cart_counter').attr('data-count', response.cart_counter['cart_count']);
                    $('#qty-'+food_id).html(response.qty);
                    console.log($('#cart_count').text())
                    console.log(response.qty)

                    console.log('add btn =>',$('#add_to_cart_btn-'+food_id))


                    if (response.qty <= 0){
                        // If the quantity is 0 or less, show the add button
                        $('#add_to_cart_btn-'+food_id).show();
                        $('#quantity-btn-box-'+food_id).hide();
                    } else {
                        // If the quantity is greater than 0, show the increase and decrease buttons
                        $('#add_to_cart_btn-'+food_id).hide();
                        $('#quantity-btn-box-'+food_id).show();
                    console.log('add btn =>',$('#add_to_cart_btn-'+food_id))

                    } 
                    // # TODO
                        // In where we will get the add and increse and decrease cart item button when it qty is 0 or lesss the show 
                        // add  button otherwise show the increase and decrease button if more then 1 or greater then 1

                    // subtotal, tax and grand total
                    applyCartAmounts(
                        response.cart_amount['subtotal'],
                        response.cart_amount['tax_dict'],
                        response.cart_amount['grand_total']
                    )
                }
            }
        })
    })


    // place the cart item quantity on load
    $('.item_qty').each(function(){
        var the_id = $(this).attr('id')
        var qty = $(this).attr('data-qty')
        $('#'+the_id).html(qty)
    })

    // decrease cart
    $('.decrease_cart').on('click', function(e){
        e.preventDefault();
        
        food_id = $(this).attr('data-id');
        url = $(this).attr('data-url');
        cart_id = $(this).attr('id');
        
        
        $.ajax({
            type: 'GET',
            url: url,
            success: function(response){
                console.log(response)
                if(response.status == 'login_required'){
                    swal(response.message, '', 'info').then(function(){
                        window.location = '/login';
                    })
                }else if(response.status == 'Failed'){
                    swal(response.message, '', 'error')
                }else{
                    $('#cart_count').text(response.cart_counter);
                    $('#qty-'+food_id).html(response.qty);
                     if (response.qty <= 0){
                        // If the quantity is 0 or less, show the add button
                        $('#add_to_cart_btn-'+food_id).show();
                        $('#quantity-btn-box-'+food_id).hide();
                    } else {
                        // If the quantity is greater than 0, show the increase and decrease buttons
                        $('#add_to_cart_btn-'+food_id).hide();
                        $('#quantity-btn-box-'+food_id).show();
                    console.log('add btn =>',$('#add_to_cart_btn-'+food_id))

                    } 

                    applyCartAmounts(
                        response.cart_amount['subtotal'],
                        response.cart_amount['tax_dict'],
                        response.cart_amount['grand_total']
                    )

                    if(window.location.pathname == '/cart/'){
                        removeCartItem(response.qty, cart_id, food_id);
                        checkEmptyCart();
                    }
                    
                } 
            }
        })
    })


    // DELETE CART ITEM
    $('.delete_cart').on('click', function(e){
        e.preventDefault();
        
        cart_id = $(this).attr('data-id');
        url = $(this).attr('data-url');
        product_id = $(this).attr('data-product-id');
        
        
        $.ajax({
            type: 'GET',
            url: url,
            success: function(response){
                console.log(response)
                if(response.status == 'Failed'){
                    swal(response.message, '', 'error')
                }else{
                    console.log(response)
                    $('#cart_count').text(response.cart_counter);

                    applyCartAmounts(
                        response.cart_amount['subtotal'],
                        response.cart_amount['tax_dict'],
                        response.cart_amount['grand_total']
                    )

                    removeCartItem(0, cart_id, product_id);
                    checkEmptyCart();
                } 
            }
        })
    })


    // delete the cart element if the qty is 0
function removeCartItem(cartItemQty, cart_id,product_id){
    if(cartItemQty <= 0){
        var el = document.getElementById("cart-item-"+cart_id);
        var el2 = document.getElementById("tax-li-"+product_id);
        if (el || el2) {
            el.remove();
            el2.remove();
        }
    }
}

    // Check if the cart is empty
    function checkEmptyCart(){
        var cart_counter = document.getElementById('cart_count').innerText
        if(cart_counter == 0){
            document.getElementById("empty-cart").style.display = "block";
        }
    }


    function applyCartAmounts(subtotal, tax_dict, grand_total) {
        if (window.location.pathname == '/cart/') {
            // Update the subtotal and grand total in the cart
            $('#subtotal').html(subtotal);
            $('#total').html(grand_total);
    
            console.log(tax_dict);
    
            // Iterate over the tax_dict array
            for (let i = 0; i < tax_dict.length; i++) {
                let single_tax = tax_dict[i];
                let productId = single_tax.product_id;
                let taxCategory = single_tax.tax_category;
                let taxInfo = single_tax.tax_info;
    
                // Iterate through tax_info to get each tax percentage and amount
                for (let percentage in taxInfo) {
                    let amount = taxInfo[percentage];
                    
                    // Update the corresponding HTML element with product-specific tax
                    $('#tax-' + productId).html(amount);
                }
            }
        }
    }
    

    // ADD OPENING HOUR
    $('.add_hour').on('click', function(e){
        e.preventDefault();
        var day = document.getElementById('id_day').value
        var from_hour = document.getElementById('id_from_hour').value
        var to_hour = document.getElementById('id_to_hour').value
        var is_closed = document.getElementById('id_is_closed').checked
        var csrf_token = $('input[name=csrfmiddlewaretoken]').val()
        var url = document.getElementById('add_hour_url').value

        console.log(day, from_hour, to_hour, is_closed, csrf_token)

        if(is_closed){
            is_closed = 'True'
            condition = "day != ''"
        }else{
            is_closed = 'False'
            condition = "day != '' && from_hour != '' && to_hour != ''"
        }

        if(eval(condition)){
            $.ajax({
                type: 'POST',
                url: url,
                data: {
                    'day': day,
                    'from_hour': from_hour,
                    'to_hour': to_hour,
                    'is_closed': is_closed,
                    'csrfmiddlewaretoken': csrf_token,
                },
                success: function(response){
                    if(response.status == 'success'){
                        if(response.is_closed == 'Closed'){
                            html = '<tr id="hour-'+response.id+'"><td><b>'+response.day+'</b></td><td>Closed</td><td><a href="#" class="remove_hour" data-url="/vendor/opening-hours/remove/'+response.id+'/">Remove</a></td></tr>';
                        }else{
                            html = '<tr id="hour-'+response.id+'"><td><b>'+response.day+'</b></td><td>'+response.from_hour+' - '+response.to_hour+'</td><td><a href="#" class="remove_hour" data-url="/vendor/opening-hours/remove/'+response.id+'/">Remove</a></td></tr>';
                        }
                        
                        $(".opening_hours").append(html)
                        document.getElementById("opening_hours").reset();
                    }else{
                        swal(response.message, '', "error")
                    }
                }
            })
        }else{
            swal('Please fill all fields', '', 'info')
        }
    });

    // REMOVE OPENING HOUR
    $(document).on('click', '.remove_hour', function(e){
        e.preventDefault();
        url = $(this).attr('data-url');
        
        $.ajax({
            type: 'GET',
            url: url,
            success: function(response){
                if(response.status == 'success'){
                    document.getElementById('hour-'+response.id).remove()
                }
            }
        })
    })

   // document ready close 
});